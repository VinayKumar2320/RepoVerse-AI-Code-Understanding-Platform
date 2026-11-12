#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from sqlalchemy import select

from backend.app.core.database import init_db, AsyncSessionLocal
from backend.app.models.entities import Repository, RepositorySnapshot
from backend.app.services.parsing.classifier import FileClassifier
from backend.app.services.parsing.parser_service import ParserService
from backend.app.services.graphs.graph_builder import CodeKnowledgeGraph
from backend.app.services.architecture.overview_service import RepositoryOverviewGenerator
from backend.app.services.retrieval.hybrid_search import HybridRetrievalEngine
from backend.app.services.orchestrator import orchestrator
from backend.app.core.logging import logger

DEMOS = [
    {
        "url": "https://github.com/pallets/flask",
        "owner": "pallets",
        "name": "flask",
        "description": "The Python micro framework for building web applications.",
        "primary_language": "Python",
        "fixture_dir": Path("benchmarks/repositories/flask_mini"),
    },
    {
        "url": "https://github.com/facebook/react",
        "owner": "facebook",
        "name": "react",
        "description": "The library for web and native user interfaces.",
        "primary_language": "TypeScript",
        "fixture_dir": Path("benchmarks/repositories/react_ts_mini"),
    }
]

async def bootstrap():
    await init_db()
    async with AsyncSessionLocal() as db:
        for demo in DEMOS:
            stmt = select(Repository).where(Repository.url == demo["url"])
            res = await db.execute(stmt)
            repo = res.scalar_one_or_none()

            if not repo:
                repo = Repository(
                    url=demo["url"],
                    owner=demo["owner"],
                    name=demo["name"],
                    description=demo["description"],
                    default_branch="main",
                    stars=65000,
                    primary_language=demo["primary_language"],
                )
                db.add(repo)
                await db.commit()
                await db.refresh(repo)

            fixture_dir = demo["fixture_dir"]
            classifier = FileClassifier(fixture_dir)
            classified_files = classifier.scan_repository()

            parser_svc = ParserService()
            parse_results = []
            for cf in classified_files:
                pr = parser_svc.parse_file(cf.path, cf.absolute_path, cf.language)
                parse_results.append(pr)

            resolved_sha = "d3b07384d113edec49eaa6238ad5ff00"
            snapshot = RepositorySnapshot(
                repository_id=repo.id,
                commit_sha=resolved_sha,
                branch="main",
                status="completed",
                total_files=len(classified_files),
                total_lines=sum(f.loc for f in classified_files),
            )
            db.add(snapshot)
            await db.commit()
            await db.refresh(snapshot)

            # Build Knowledge Graph
            graph = CodeKnowledgeGraph(snapshot.id)
            graph.build(classified_files, parse_results, repo.name)

            # Generate Overview
            overview_gen = RepositoryOverviewGenerator()
            overview = overview_gen.generate_overview(
                repo_dir=fixture_dir,
                repository_id=repo.id,
                snapshot_id=snapshot.id,
                owner=repo.owner,
                name=repo.name,
                description=repo.description,
                commit_sha=resolved_sha,
                branch="main",
                classified_files=classified_files,
                primary_lang=repo.primary_language
            )

            # Index Retrieval
            retrieval = HybridRetrievalEngine(commit_sha=resolved_sha)
            all_syms = [s for pr in parse_results for s in pr.symbols]
            retrieval.index_repository(classified_files, all_syms, graph.graph)

            snapshot.overview_json = overview.model_dump()
            await db.commit()

            # Cache in memory
            orchestrator.graph_cache[snapshot.id] = graph
            orchestrator.retrieval_cache[snapshot.id] = retrieval
            orchestrator.overview_cache[snapshot.id] = overview
            orchestrator.classified_cache[snapshot.id] = classified_files

            logger.info(f"Successfully bootstrapped demo repository: {repo.owner}/{repo.name} (Snapshot: {snapshot.id})")

if __name__ == "__main__":
    asyncio.run(bootstrap())
