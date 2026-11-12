import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.logging import logger
from backend.app.models.entities import (
    Repository, RepositorySnapshot, AnalysisJob, SourceFile, CodeSymbol, GraphNode, GraphEdge
)
from backend.app.services.ingestion.clone_service import CloneService
from backend.app.services.parsing.classifier import FileClassifier, ClassifiedFile
from backend.app.services.parsing.parser_service import ParserService
from backend.app.services.graphs.graph_builder import CodeKnowledgeGraph
from backend.app.services.architecture.overview_service import RepositoryOverviewGenerator
from backend.app.services.analytics.metrics_service import ArchitectureAnalyticsService
from backend.app.services.retrieval.hybrid_search import HybridRetrievalEngine
from backend.app.schemas.repository import RepositoryOverview

class RepositoryOrchestrator:
    def __init__(self):
        self.clone_service = CloneService()
        self.parser_service = ParserService()
        self.overview_gen = RepositoryOverviewGenerator()
        self.analytics_service = ArchitectureAnalyticsService()

        # In-memory runtime cache for high-performance interactive queries
        self.graph_cache: Dict[str, CodeKnowledgeGraph] = {} # snapshot_id -> CodeKnowledgeGraph
        self.retrieval_cache: Dict[str, HybridRetrievalEngine] = {} # snapshot_id -> HybridRetrievalEngine
        self.overview_cache: Dict[str, RepositoryOverview] = {} # snapshot_id -> RepositoryOverview
        self.classified_cache: Dict[str, List[ClassifiedFile]] = {} # snapshot_id -> ClassifiedFiles

    async def analyze_repository(
        self,
        db: AsyncSession,
        url: str,
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None
    ) -> AnalysisJob:
        # 1. Normalize and resolve repo record
        from backend.app.core.security import validate_github_url
        normalized_url, owner, name = validate_github_url(url)

        stmt = select(Repository).where(Repository.url == normalized_url)
        res = await db.execute(stmt)
        repo = res.scalar_one_or_none()

        if not repo:
            repo = Repository(
                url=normalized_url,
                owner=owner,
                name=name,
                default_branch=branch or "main",
            )
            db.add(repo)
            await db.commit()
            await db.refresh(repo)

        # Create job record
        job = AnalysisJob(
            repository_id=repo.id,
            commit_sha=commit_sha,
            status="queued",
            progress_percentage=5,
            current_step="Job queued for processing"
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        # Trigger background processing
        asyncio.create_task(self._run_analysis_pipeline(job.id, repo.id, normalized_url, branch, commit_sha))
        return job

    async def _run_analysis_pipeline(
        self,
        job_id: str,
        repo_id: str,
        url: str,
        branch: Optional[str],
        commit_sha: Optional[str]
    ):
        from backend.app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            try:
                # Update job status: Cloning
                await self._update_job(db, job_id, "cloning", 20, "Fetching repository contents...")

                repo_dir, resolved_sha, meta = await self.clone_service.clone_or_checkout(
                    raw_url=url, branch=branch, commit_sha=commit_sha
                )

                # Update repository metadata
                repo = await db.get(Repository, repo_id)
                if repo:
                    repo.description = meta.get("description", repo.description)
                    repo.stars = meta.get("stars", repo.stars)
                    repo.primary_language = meta.get("primary_language", repo.primary_language)
                    repo.default_branch = meta.get("default_branch", repo.default_branch)
                    await db.commit()

                # Step 2: File Discovery & Classification
                await self._update_job(db, job_id, "parsing", 40, "Classifying files and scanning directory...")
                classifier = FileClassifier(repo_dir)
                classified_files = classifier.scan_repository()

                # Create Snapshot
                snapshot = RepositorySnapshot(
                    repository_id=repo_id,
                    commit_sha=resolved_sha,
                    branch=branch or meta.get("default_branch", "main"),
                    status="analyzing",
                    total_files=len(classified_files),
                    total_lines=sum(f.loc for f in classified_files),
                )
                db.add(snapshot)
                await db.commit()
                await db.refresh(snapshot)

                # Step 3: AST Parsing
                await self._update_job(db, job_id, "parsing", 65, "Parsing source code with Tree-sitter & AST...")
                parse_results = []
                for cf in classified_files:
                    if cf.category in ("source", "test"):
                        pr = self.parser_service.parse_file(cf.path, cf.absolute_path, cf.language)
                        parse_results.append(pr)

                # Step 4: Construct Knowledge Graph
                await self._update_job(db, job_id, "building_graph", 80, "Constructing versioned code knowledge graph...")
                graph = CodeKnowledgeGraph(snapshot.id)
                graph.build(classified_files, parse_results, repo.name)

                # Step 5: Compute Architecture Overview & Analytics
                await self._update_job(db, job_id, "building_graph", 90, "Generating architectural overview and metrics...")
                overview = self.overview_gen.generate_overview(
                    repo_dir=repo_dir,
                    repository_id=repo_id,
                    snapshot_id=snapshot.id,
                    owner=repo.owner,
                    name=repo.name,
                    description=repo.description,
                    commit_sha=resolved_sha,
                    branch=snapshot.branch,
                    classified_files=classified_files,
                    primary_lang=repo.primary_language
                )

                # Step 6: Index for Retrieval
                retrieval_engine = HybridRetrievalEngine(commit_sha=resolved_sha)
                all_symbols = [s for pr in parse_results for s in pr.symbols]
                retrieval_engine.index_repository(classified_files, all_symbols, graph.graph)

                # Cache in-memory
                self.graph_cache[snapshot.id] = graph
                self.retrieval_cache[snapshot.id] = retrieval_engine
                self.overview_cache[snapshot.id] = overview
                self.classified_cache[snapshot.id] = classified_files

                # Update snapshot in DB
                snapshot.status = "completed"
                snapshot.overview_json = overview.model_dump()
                await db.commit()

                # Complete Job
                await self._update_job(db, job_id, "completed", 100, "Analysis complete", snapshot_id=snapshot.id)
                logger.info(f"Analysis completed successfully for {repo.name} ({resolved_sha[:8]}).")

            except Exception as e:
                logger.exception(f"Repository analysis failed: {e}")
                await self._update_job(db, job_id, "failed", 100, f"Analysis failed: {str(e)}")

    async def _update_job(
        self,
        db: AsyncSession,
        job_id: str,
        status: str,
        progress: int,
        step: str,
        snapshot_id: Optional[str] = None
    ):
        job = await db.get(AnalysisJob, job_id)
        if job:
            job.status = status
            job.progress_percentage = progress
            job.current_step = step
            await db.commit()

orchestrator = RepositoryOrchestrator()
