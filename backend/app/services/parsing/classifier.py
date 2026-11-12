import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

IGNORED_DIRS = {
    ".git", ".github", ".venv", "venv", "env", "node_modules", "dist", "build",
    "__pycache__", ".pytest_cache", ".coverage", "htmlcov", ".idea", ".vscode",
    ".next", ".turbo", "out", "coverage", ".tox", ".mypy_cache", ".ruff_cache",
    "eggs", "develop-eggs", ".eggs", "site-packages"
}

EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".md": "markdown",
    ".rst": "restructuredtext",
    ".txt": "text",
    ".html": "html",
    ".css": "css",
    ".scss": "scss",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".zsh": "shell",
    ".dockerfile": "dockerfile",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c_header",
    ".rb": "ruby",
}

SPECIAL_FILENAMES = {
    "dockerfile": ("dockerfile", "build"),
    "docker-compose.yml": ("yaml", "config"),
    "docker-compose.yaml": ("yaml", "config"),
    "makefile": ("makefile", "build"),
    "package.json": ("json", "build"),
    "tsconfig.json": ("json", "config"),
    "pyproject.toml": ("toml", "build"),
    "setup.py": ("python", "build"),
    "setup.cfg": ("ini", "build"),
    "requirements.txt": ("text", "build"),
    "pipfile": ("toml", "build"),
    "poetry.lock": ("toml", "build"),
    "cargo.toml": ("toml", "build"),
    ".env.example": ("config", "config"),
    "readme.md": ("markdown", "doc"),
    "license": ("text", "doc"),
    "contributing.md": ("markdown", "doc"),
}

@dataclass
class ClassifiedFile:
    path: str
    absolute_path: Path
    language: str
    category: str # source, test, config, doc, build, asset
    loc: int
    size_bytes: int

class FileClassifier:
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir

    def is_ignored(self, relative_path: Path) -> bool:
        for part in relative_path.parts:
            if part in IGNORED_DIRS or part.startswith("."):
                if part in {".env.example", ".gitignore"}:
                    continue
                return True
        return False

    def classify_file(self, file_path: Path) -> ClassifiedFile:
        rel_path = file_path.relative_to(self.repo_dir)
        rel_str = str(rel_path).replace("\\", "/")
        filename_lower = file_path.name.lower()
        ext = file_path.suffix.lower()

        # Check special filenames first
        if filename_lower in SPECIAL_FILENAMES:
            lang, cat = SPECIAL_FILENAMES[filename_lower]
        else:
            lang = EXTENSION_LANGUAGE_MAP.get(ext, "unknown")
            cat = "source"

            # Check test heuristic
            if "test" in rel_str.lower() or "spec" in rel_str.lower():
                cat = "test"
            elif ext in {".md", ".rst", ".txt", ".pdf"}:
                cat = "doc"
            elif ext in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".xml"}:
                cat = "config"
            elif ext in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".woff", ".woff2", ".ttf"}:
                cat = "asset"
            elif ext in {".lock"}:
                cat = "build"

        # Count LOC safely
        loc = 0
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                loc = sum(1 for line in f if line.strip())
        except Exception:
            loc = 0

        size_bytes = 0
        try:
            size_bytes = file_path.stat().st_size
        except Exception:
            pass

        return ClassifiedFile(
            path=rel_str,
            absolute_path=file_path,
            language=lang,
            category=cat,
            loc=loc,
            size_bytes=size_bytes,
        )

    def scan_repository(self) -> List[ClassifiedFile]:
        classified = []
        for root, dirs, files in os.walk(self.repo_dir):
            # Prune ignored directories in-place for fast traversal
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]

            for fname in files:
                fpath = Path(root) / fname
                if fpath.is_symlink():
                    continue
                rel_path = fpath.relative_to(self.repo_dir)
                if self.is_ignored(rel_path):
                    continue

                cf = self.classify_file(fpath)
                classified.append(cf)

        return classified
