from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import re

from backend.app.schemas.repository import RepositoryOverview
from backend.app.services.parsing.classifier import ClassifiedFile
from backend.app.core.logging import logger

class RepositoryOverviewGenerator:
    def generate_overview(
        self,
        repo_dir: Path,
        repository_id: str,
        snapshot_id: str,
        owner: str,
        name: str,
        description: Optional[str],
        commit_sha: str,
        branch: str,
        classified_files: List[ClassifiedFile],
        primary_lang: Optional[str] = None
    ) -> RepositoryOverview:
        # 1. Read README if available
        readme_text = self._read_readme(repo_dir)

        # 2. Languages breakdown
        lang_counts: Dict[str, int] = {}
        total_loc = 0
        for cf in classified_files:
            lang_counts[cf.language] = lang_counts.get(cf.language, 0) + cf.loc
            total_loc += cf.loc

        primary = primary_lang or (max(lang_counts.items(), key=lambda x: x[1])[0] if lang_counts else "Unknown")

        # 3. Detect Frameworks & Dependencies
        frameworks = self._detect_frameworks(repo_dir, classified_files)

        # 4. Detect Likely Entry Points
        entry_points = self._detect_entry_points(classified_files)

        # 5. Important Directories
        important_dirs = self._detect_important_directories(classified_files)

        # 6. Core Components
        core_components = self._detect_core_components(classified_files, primary)

        # 7. Local Run & Test Commands
        run_cmds, test_cmds = self._extract_commands(repo_dir, classified_files, readme_text)

        # 8. Problem Solved & Summary
        problem_solved, arch_summary = self._summarize_problem_and_architecture(
            name, owner, description, readme_text, primary, frameworks, core_components
        )

        return RepositoryOverview(
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            name=name,
            owner=owner,
            description=description or f"Open-source repository {name}",
            commit_sha=commit_sha,
            branch=branch,
            primary_language=primary,
            languages=lang_counts,
            total_files=len(classified_files),
            total_lines=total_loc,
            problem_solved=problem_solved,
            frameworks=frameworks,
            entry_points=entry_points,
            important_directories=important_dirs,
            core_components=core_components,
            local_run_commands=run_cmds,
            test_commands=test_cmds,
            architecture_summary=arch_summary,
        )

    def _read_readme(self, repo_dir: Path) -> str:
        for fname in ["README.md", "README.rst", "README.txt", "readme.md"]:
            fp = repo_dir / fname
            if fp.exists():
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        return f.read()
                except Exception:
                    pass
        return ""

    def _detect_frameworks(self, repo_dir: Path, files: List[ClassifiedFile]) -> List[str]:
        found = set()
        file_paths = {f.path.lower() for f in files}

        # Check package.json
        pkg_json = repo_dir / "package.json"
        if pkg_json.exists():
            try:
                with open(pkg_json, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    for k in deps:
                        if k in ("next", "react", "vue", "express", "fastify", "svelte", "tailwindcss", "prisma", "nestjs"):
                            found.add(k.capitalize())
            except Exception:
                pass

        # Check pyproject.toml / requirements.txt
        req_txt = repo_dir / "requirements.txt"
        if req_txt.exists():
            try:
                with open(req_txt, "r", encoding="utf-8", errors="ignore") as f:
                    txt = f.read().lower()
                    for fw in ["fastapi", "flask", "django", "tornado", "sqlalchemy", "pydantic", "torch", "pandas"]:
                        if fw in txt:
                            found.add(fw.capitalize())
            except Exception:
                pass

        # Heuristics from directory names
        if any("docker-compose" in p for p in file_paths):
            found.add("Docker")
        if any(".github/workflows" in p for p in file_paths):
            found.add("GitHub Actions")

        return sorted(list(found))

    def _detect_entry_points(self, files: List[ClassifiedFile]) -> List[str]:
        entry_candidates = [
            "main.py", "app.py", "wsgi.py", "asgi.py", "server.py", "manage.py", "cli.py",
            "src/index.ts", "src/index.js", "src/main.ts", "src/server.ts", "src/app.tsx",
            "index.js", "index.ts", "server.js", "app.js", "src/app/page.tsx"
        ]
        entries = []
        for cf in files:
            for cand in entry_candidates:
                if cf.path == cand or cf.path.endswith(f"/{cand}"):
                    entries.append(cf.path)
        return entries[:5]

    def _detect_important_directories(self, files: List[ClassifiedFile]) -> List[Dict[str, str]]:
        dir_roles = {
            "app": "Application core logic and API endpoints",
            "src": "Source code implementation",
            "backend": "Backend server and database services",
            "frontend": "Frontend user interface components and pages",
            "api": "REST / GraphQL API routing and controllers",
            "services": "Business logic and domain services",
            "models": "Data models, schemas, and database entities",
            "core": "Configuration, logging, and infrastructure utilities",
            "tests": "Automated unit and integration test suites",
            "scripts": "Automation, build, and benchmark utilities",
            "docs": "Documentation and developer guides",
        }
        res = []
        seen_dirs = set()
        for f in files:
            first_dir = f.path.split("/")[0] if "/" in f.path else ""
            if first_dir and first_dir not in seen_dirs and first_dir in dir_roles:
                seen_dirs.add(first_dir)
                res.append({"path": first_dir, "role": dir_roles[first_dir]})
        return res

    def _detect_core_components(self, files: List[ClassifiedFile], primary_lang: str) -> List[Dict[str, str]]:
        components = []
        for f in files:
            if f.category == "source" and f.loc > 50:
                p = f.path
                name = Path(p).stem
                if any(k in name.lower() for k in ["service", "client", "engine", "handler", "manager", "router", "parser"]):
                    components.append({
                        "name": name,
                        "file": p,
                        "purpose": f"Handles core {name.lower()} operations ({f.loc} LOC)"
                    })
            if len(components) >= 5:
                break
        return components

    def _extract_commands(
        self,
        repo_dir: Path,
        files: List[ClassifiedFile],
        readme: str
    ) -> Tuple[List[str], List[str]]:
        run_cmds = []
        test_cmds = []

        file_paths = {f.path for f in files}

        # Check python
        if "pyproject.toml" in file_paths or "requirements.txt" in file_paths:
            run_cmds.append("pip install -r requirements.txt (or poetry install)")
            test_cmds.append("pytest")

        # Check node
        if "package.json" in file_paths:
            run_cmds.append("npm install && npm run dev")
            test_cmds.append("npm test")

        # Check docker
        if any("docker-compose" in p for p in file_paths):
            run_cmds.append("docker compose up")

        # Check README for code blocks with pytest or run
        for match in re.findall(r"```(?:bash|sh|console)?\n(.*?)\n```", readme, re.DOTALL):
            for line in match.strip().splitlines():
                line = line.strip().lstrip("$ ")
                if any(kw in line for kw in ["pytest", "npm test", "vitest", "cargo test", "python -m unittest"]):
                    if line not in test_cmds:
                        test_cmds.append(line)
                elif any(kw in line for kw in ["npm start", "python main.py", "uvicorn", "docker-compose up"]):
                    if line not in run_cmds:
                        run_cmds.append(line)

        return run_cmds[:3], test_cmds[:3]

    def _summarize_problem_and_architecture(
        self,
        name: str,
        owner: str,
        description: Optional[str],
        readme: str,
        primary_lang: str,
        frameworks: List[str],
        components: List[Dict[str, str]]
    ) -> Tuple[str, str]:
        # Extract first paragraph from README if present
        first_para = ""
        for line in readme.split("\n\n"):
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("#") and len(cleaned) > 40:
                first_para = cleaned.replace("\n", " ")
                break

        problem_solved = first_para or description or f"Provides a {primary_lang}-based solution for {name}."
        if len(problem_solved) > 280:
            problem_solved = problem_solved[:277] + "..."

        fw_str = ", ".join(frameworks) if frameworks else primary_lang
        comp_str = ", ".join([c["name"] for c in components[:3]]) if components else "modular source units"

        arch_summary = (
            f"{name} is structured as a {primary_lang} project leveraging {fw_str}. "
            f"Its primary execution paths traverse {comp_str}, providing clean separation of "
            f"responsibilities between API routing, service logic, and foundational utilities."
        )

        return problem_solved, arch_summary
