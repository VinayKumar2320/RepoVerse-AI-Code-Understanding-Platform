from typing import List, Dict, Any, Optional
from backend.app.schemas.learning import (
    AdaptiveExplanationResponse, LearningStepSchema, TopicWalkthroughResponse
)
from backend.app.schemas.repository import RepositoryOverview
from backend.app.services.parsing.symbol_types import ParsedSymbol
from backend.app.schemas.architecture import ArchitectureAnalyticsResponse

class AdaptiveLearningEngine:
    def generate_adaptive_explanation(
        self,
        level: str, # "beginner", "developer", "senior"
        overview: RepositoryOverview,
        symbols: List[ParsedSymbol],
        analytics: Optional[ArchitectureAnalyticsResponse] = None
    ) -> AdaptiveExplanationResponse:
        level_normalized = level.lower().strip()
        if level_normalized not in ("beginner", "developer", "senior"):
            level_normalized = "developer"

        if level_normalized == "beginner":
            return self._build_beginner_mode(overview, symbols)
        elif level_normalized == "senior":
            return self._build_senior_mode(overview, symbols, analytics)
        else:
            return self._build_developer_mode(overview, symbols, analytics)

    def _build_beginner_mode(
        self,
        ov: RepositoryOverview,
        symbols: List[ParsedSymbol]
    ) -> AdaptiveExplanationResponse:
        entry = ov.entry_points[0] if ov.entry_points else "the root module"
        fw = ", ".join(ov.frameworks) if ov.frameworks else ov.primary_language

        overview_text = (
            f"Think of {ov.name} like an automated workshop. It takes in requests, "
            f"processes them using {fw}, and delivers results reliably. "
            f"Its goal is simple: {ov.problem_solved}"
        )

        mental_model = (
            "Imagine an airport: the entry points are the arrival gates, the core modules "
            "are the baggage sorters and navigators, and the outputs are flights taking off. "
            "You only need to follow one path from entry to exit to see the whole system in action."
        )

        breakdown = [
            {"component": d["path"], "what_it_does": f"Holds the files that handle {d['role'].lower()}."}
            for d in ov.important_directories[:4]
        ]

        steps = [
            LearningStepSchema(
                step_id=1,
                title="1. What is this project?",
                summary=f"Understanding the purpose of {ov.name}",
                detailed_explanation=(
                    f"{ov.name} is written in {ov.primary_language}. "
                    f"It was created to solve: {ov.problem_solved} "
                    f"It organizes {ov.total_files} files into logical folders."
                ),
                key_takeaways=[
                    f"Primary language: {ov.primary_language}",
                    f"Core objective: {ov.problem_solved}",
                    "Clean, modular directory structure"
                ],
                citations=[{"file_path": "README.md", "start_line": 1, "end_line": 25}],
                suggested_files=["README.md"],
                difficulty="Introductory",
                comprehension_check={
                    "question": f"What language is {ov.name} primarily built with?",
                    "options": [ov.primary_language, "Assembly", "Fortran"],
                    "correct": ov.primary_language
                }
            ),
            LearningStepSchema(
                step_id=2,
                title="2. How is it organized?",
                summary="Understanding the main folders and layout",
                detailed_explanation=(
                    f"The project separates code into distinct directories. "
                    f"For example, '{ov.important_directories[0]['path'] if ov.important_directories else 'src'}' "
                    f"contains the main functional logic."
                ),
                key_takeaways=[
                    "Folders group related responsibilities",
                    "Config files sit at the root, while logic sits inside dedicated source folders"
                ],
                citations=[{"file_path": d["path"], "start_line": 1, "end_line": 1} for d in ov.important_directories[:2]],
                suggested_files=[d["path"] for d in ov.important_directories[:3]],
                difficulty="Introductory"
            ),
            LearningStepSchema(
                step_id=3,
                title="3. Where does execution begin?",
                summary=f"Starting at {entry}",
                detailed_explanation=(
                    f"Every program has a 'front door' where it starts running. "
                    f"In {ov.name}, that front door is likely `{entry}`. When you launch the app, "
                    f"the computer reads this file first to configure the environment and start listening for inputs."
                ),
                key_takeaways=[
                    f"Execution begins at `{entry}`",
                    "Initialization loads configuration and sets up handlers"
                ],
                citations=[{"file_path": entry, "start_line": 1, "end_line": 30}],
                suggested_files=[entry],
                difficulty="Introductory"
            ),
            LearningStepSchema(
                step_id=4,
                title="4. How do I run and test it?",
                summary="Running the project on your machine",
                detailed_explanation=(
                    f"To run this project locally, execute: `{ov.local_run_commands[0] if ov.local_run_commands else 'python main.py'}`. "
                    f"To verify everything works, run the automated tests using: `{ov.test_commands[0] if ov.test_commands else 'pytest'}`."
                ),
                key_takeaways=[
                    f"Start command: {ov.local_run_commands[0] if ov.local_run_commands else 'Default launcher'}",
                    f"Test command: {ov.test_commands[0] if ov.test_commands else 'Test runner'}"
                ],
                citations=[],
                suggested_files=[],
                difficulty="Introductory"
            )
        ]

        return AdaptiveExplanationResponse(
            experience_level="beginner",
            overview=overview_text,
            mental_model=mental_model,
            architecture_breakdown=breakdown,
            steps=steps
        )

    def _build_developer_mode(
        self,
        ov: RepositoryOverview,
        symbols: List[ParsedSymbol],
        analytics: Optional[ArchitectureAnalyticsResponse]
    ) -> AdaptiveExplanationResponse:
        endpoints = [s for s in symbols if s.kind == "endpoint"]
        classes = [s for s in symbols if s.kind == "class"]
        entry = ov.entry_points[0] if ov.entry_points else "main"

        overview_text = (
            f"{ov.name} is a {ov.primary_language} application comprising {ov.total_files} files "
            f"and {ov.total_lines:,} lines of code. It integrates {', '.join(ov.frameworks) if ov.frameworks else 'standard libraries'} "
            f"to solve: {ov.problem_solved} "
            f"Architecture exposes {len(endpoints)} detected endpoints and {len(classes)} classes."
        )

        mental_model = (
            "Layered service architecture: Inbound requests or CLI invocations arrive via entry-point modules, "
            "delegate to domain service controllers, and propagate through typed data entities."
        )

        breakdown = [
            {"component": d["path"], "what_it_does": d["role"]}
            for d in ov.important_directories
        ]

        steps = [
            LearningStepSchema(
                step_id=1,
                title="1. Architecture & Boundaries",
                summary="High-level decomposition of modules and packages",
                detailed_explanation=(
                    f"The codebase is divided into modular packages: "
                    f"{', '.join([d['path'] for d in ov.important_directories[:4]])}. "
                    f"External dependencies include {', '.join(ov.frameworks) if ov.frameworks else 'None'}."
                ),
                key_takeaways=[
                    f"Total LOC: {ov.total_lines:,}",
                    f"Detected frameworks: {', '.join(ov.frameworks)}",
                    "Separation of concerns between entry points and domain logic"
                ],
                citations=[{"file_path": d["path"], "start_line": 1, "end_line": 1} for d in ov.important_directories[:3]],
                suggested_files=[d["path"] for d in ov.important_directories[:3]],
                difficulty="Intermediate"
            ),
            LearningStepSchema(
                step_id=2,
                title="2. Entry Points & Routing",
                summary=f"Bootstrapping and routing via {entry}",
                detailed_explanation=(
                    f"Bootstrapping occurs in `{entry}`. Route handlers or CLI commands are registered here "
                    f"and dispatched to handler functions."
                ),
                key_takeaways=[
                    f"Primary bootstrap file: {entry}",
                    f"Routes/Endpoints detected: {len(endpoints)}"
                ],
                citations=[{"file_path": entry, "start_line": 1, "end_line": 40}],
                suggested_files=[entry] + [ep.qualified_name.split("::")[0] for ep in endpoints[:2]],
                difficulty="Intermediate"
            ),
            LearningStepSchema(
                step_id=3,
                title="3. Core Domain Entities & Services",
                summary="Key classes and method contracts",
                detailed_explanation=(
                    f"Central business logic is encapsulated in {len(classes)} classes. "
                    f"Prominent entities: {', '.join([c.name for c in classes[:4]]) if classes else 'Functional modules'}."
                ),
                key_takeaways=[
                    "Encapsulated state and business rules",
                    "Dependency injection / modular imports between services"
                ],
                citations=[{"file_path": c.qualified_name.split("::")[0], "start_line": c.start_line, "end_line": c.end_line, "symbol": c.name} for c in classes[:3]],
                suggested_files=[c.qualified_name.split("::")[0] for c in classes[:3]],
                difficulty="Intermediate"
            ),
            LearningStepSchema(
                step_id=4,
                title="4. Testing & Contribution Flow",
                summary="Running test suite and verifying changes",
                detailed_explanation=(
                    f"The test harness is executed with: `{ov.test_commands[0] if ov.test_commands else 'pytest'}`. "
                    f"New contributions should add tests matching existing fixtures and patterns."
                ),
                key_takeaways=[
                    f"Test command: {ov.test_commands[0] if ov.test_commands else 'pytest'}",
                    "Verify regression before committing"
                ],
                citations=[],
                suggested_files=[],
                difficulty="Intermediate"
            )
        ]

        return AdaptiveExplanationResponse(
            experience_level="developer",
            overview=overview_text,
            mental_model=mental_model,
            architecture_breakdown=breakdown,
            steps=steps
        )

    def _build_senior_mode(
        self,
        ov: RepositoryOverview,
        symbols: List[ParsedSymbol],
        analytics: Optional[ArchitectureAnalyticsResponse]
    ) -> AdaptiveExplanationResponse:
        cycles_count = len(analytics.dependency_cycles) if analytics else 0
        sccs_count = len(analytics.strongly_connected_components) if analytics else 0

        overview_text = (
            f"Structural evaluation of {ov.name}: Total codebase consists of {ov.total_files} files "
            f"({ov.total_lines:,} LOC) with {analytics.total_modules if analytics else ov.total_files} module nodes "
            f"and {analytics.total_dependencies if analytics else 0} dependency edges. "
            f"Analysis reveals {cycles_count} cyclic dependency paths and {sccs_count} strongly connected clusters."
        )

        mental_model = (
            "System coupling & cohesion assessment: Examine afferent vs efferent coupling hotspots, "
            "evaluate architectural boundaries between modules, and verify adherence to the Stable Dependencies Principle."
        )

        patterns = [
            "Modular Decoupling: Domain logic isolated behind explicit interfaces",
            "Dependency Inversion: Higher-level policy decoupled from specific driver implementations",
            f"Architectural Verdict: {analytics.summary_verdict if analytics else 'Verified modular separation'}"
        ]

        pitfalls = [
            f"Cyclic Dependencies: {cycles_count} detected cycles" if cycles_count > 0 else "Zero dependency cycles detected (stable design)",
            "Hotspot Risk: Modules with elevated fan-in require high test coverage to prevent cascading regression"
        ]

        steps = [
            LearningStepSchema(
                step_id=1,
                title="1. Structural Coupling & Centrality Analysis",
                summary="Evaluating fan-in / fan-out bottlenecks and instability",
                detailed_explanation=(
                    f"Central modules identified via PageRank & degree centrality: "
                    f"{', '.join([h['label'] for h in (analytics.top_central_modules if analytics else [])])}. "
                    f"High fan-in modules serve as foundational abstractions but create tight afferent coupling."
                ),
                key_takeaways=[
                    f"Hotspot modules: {len(analytics.fan_in_hotspots) if analytics else 0}",
                    "Monitor Robert C. Martin's instability metric (I) across subsystem boundaries"
                ],
                citations=[],
                suggested_files=[h["label"] for h in (analytics.top_central_modules[:3] if analytics else [])],
                difficulty="Advanced"
            ),
            LearningStepSchema(
                step_id=2,
                title="2. Architectural Tradeoffs & Cycle Mitigation",
                summary="Refactoring opportunities and cyclic dependency remediation",
                detailed_explanation=(
                    f"Evaluation of {cycles_count} cyclic dependency chains. "
                    f"If cycles exist, resolve them by extracting common interface definitions "
                    f"or introducing event-driven pub/sub communication."
                ),
                key_takeaways=[
                    f"Cyclic graph paths: {cycles_count}",
                    "Enforce acyclic dependency principle (ADP)"
                ],
                citations=[],
                suggested_files=[],
                difficulty="Advanced"
            ),
            LearningStepSchema(
                step_id=3,
                title="3. Extensibility & Boundary Hardening",
                summary="Assessing scalability, plugin points, and testing pyramids",
                detailed_explanation=(
                    f"The project allows extension primarily through {ov.primary_language} class inheritance "
                    f"and function parameterization. Verify test boundaries before introducing architectural mutations."
                ),
                key_takeaways=[
                    "Check contracts before extending public API surfaces",
                    "Maintain unit vs integration test isolation"
                ],
                citations=[],
                suggested_files=[],
                difficulty="Advanced"
            )
        ]

        return AdaptiveExplanationResponse(
            experience_level="senior",
            overview=overview_text,
            mental_model=mental_model,
            architecture_breakdown=[],
            steps=steps,
            tradeoffs_and_patterns=patterns,
            common_pitfalls=pitfalls
        )

    def generate_topic_walkthrough(
        self,
        topic: str,
        ov: RepositoryOverview,
        symbols: List[ParsedSymbol]
    ) -> TopicWalkthroughResponse:
        topic_lower = topic.lower().strip()

        # Find relevant files and symbols for topic
        relevant_files = []
        relevant_symbols = []

        keywords = {
            "authentication": ["auth", "token", "jwt", "login", "user", "password", "session"],
            "api": ["api", "route", "router", "endpoint", "controller", "handler", "v1"],
            "database": ["db", "database", "model", "schema", "query", "crud", "repository", "migration"],
            "testing": ["test", "fixture", "mock", "conftest", "spec"],
            "core_flow": ["engine", "service", "process", "pipeline", "main"],
        }.get(topic_lower, [topic_lower])

        for sym in symbols:
            if any(kw in sym.name.lower() or kw in sym.qualified_name.lower() for kw in keywords):
                relevant_symbols.append(sym.name)
                f_path = sym.qualified_name.split("::")[0]
                if f_path not in relevant_files:
                    relevant_files.append(f_path)

        return TopicWalkthroughResponse(
            topic=topic_lower,
            title=f"Guided Walkthrough: {topic.capitalize()} in {ov.name}",
            description=f"Step-by-step deep dive into how {topic_lower} is implemented across {len(relevant_files)} files.",
            relevant_files=relevant_files[:5],
            relevant_symbols=relevant_symbols[:8],
            steps=[
                LearningStepSchema(
                    step_id=1,
                    title=f"1. Core Concepts of {topic.capitalize()}",
                    summary=f"Overview of files implementing {topic_lower}",
                    detailed_explanation=f"Implementation spans: {', '.join(relevant_files[:3]) if relevant_files else 'standard modules'}.",
                    key_takeaways=[f"Inspected {len(relevant_symbols)} related symbols"],
                    citations=[{"file_path": rf, "start_line": 1, "end_line": 30} for rf in relevant_files[:2]],
                    suggested_files=relevant_files[:3],
                    difficulty="Intermediate"
                )
            ]
        )
