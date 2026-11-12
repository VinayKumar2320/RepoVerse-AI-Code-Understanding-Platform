import os
import shutil
import subprocess
import asyncio
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import httpx

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import validate_github_url, SecurityValidationError

class IngestionError(Exception):
    pass

class CloneService:
    def __init__(self, storage_root: Optional[str] = None):
        self.storage_root = Path(storage_root or settings.REPO_STORAGE_PATH).resolve()
        self.storage_root.mkdir(parents=True, exist_ok=True)

    async def get_remote_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Fetch repository public metadata from GitHub API if available, or generate standard metadata."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "RepoVerse-Engine",
        }
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(api_url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return {
                        "owner": owner,
                        "name": repo,
                        "description": data.get("description") or "",
                        "default_branch": data.get("default_branch") or "main",
                        "stars": data.get("stargazers_count", 0),
                        "primary_language": data.get("language") or "Python",
                        "size_kb": data.get("size", 0),
                    }
        except Exception as e:
            logger.warning(f"Failed to query GitHub REST API for {owner}/{repo}: {e}")

        # Fallback if unauthenticated / offline / rate-limited
        return {
            "owner": owner,
            "name": repo,
            "description": f"Repository {owner}/{repo}",
            "default_branch": "main",
            "stars": 0,
            "primary_language": None,
            "size_kb": 0,
        }

    def _run_git_cmd(self, args: list[str], cwd: Optional[Path] = None, timeout: int = 60) -> str:
        """Run git safely with no shell injection."""
        try:
            result = subprocess.run(
                args,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise IngestionError(f"Git command timed out after {timeout} seconds.")
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() or e.stdout.strip()
            raise IngestionError(f"Git execution failed: {err}")

    async def clone_or_checkout(
        self,
        raw_url: str,
        branch: Optional[str] = None,
        commit_sha: Optional[str] = None
    ) -> Tuple[Path, str, Dict[str, Any]]:
        """
        Clones or fetches the repository into secure isolated storage.
        Returns: (repo_dir, resolved_commit_sha, repo_metadata)
        """
        normalized_url, owner, repo = validate_github_url(raw_url)
        meta = await self.get_remote_repo_info(owner, repo)

        target_branch = branch or meta["default_branch"]
        repo_base_dir = self.storage_root / f"{owner}_{repo}"
        repo_base_dir.mkdir(parents=True, exist_ok=True)

        # Clone into a canonical directory
        git_dir = repo_base_dir / "repo"

        # Safe non-blocking execution in threadpool
        loop = asyncio.get_event_loop()

        def do_git():
            if not (git_dir / ".git").exists():
                logger.info(f"Cloning {normalized_url} to {git_dir}...")
                clone_args = [
                    "git", "clone",
                    "--no-tags",
                    "--single-branch",
                    "--branch", target_branch,
                    "--depth", "50",
                    normalized_url,
                    str(git_dir)
                ]
                self._run_git_cmd(clone_args, timeout=settings.CLONE_TIMEOUT_SECONDS)
            else:
                logger.info(f"Repository already cloned in {git_dir}. Fetching updates...")
                self._run_git_cmd(["git", "fetch", "--depth", "50", "origin", target_branch], cwd=git_dir)

            # Checkout specific commit or branch
            if commit_sha:
                logger.info(f"Checking out commit {commit_sha}...")
                self._run_git_cmd(["git", "checkout", commit_sha], cwd=git_dir)
            else:
                self._run_git_cmd(["git", "checkout", target_branch], cwd=git_dir)

            current_sha = self._run_git_cmd(["git", "rev-parse", "HEAD"], cwd=git_dir)
            return current_sha

        current_sha = await loop.run_in_executor(None, do_git)

        # Enforce file count and size limits for safety
        self._check_safety_limits(git_dir)

        return git_dir, current_sha, meta

    def _check_safety_limits(self, repo_dir: Path):
        """Enforce strict resource quotas to protect against malicious large repos / zipbombs."""
        total_size = 0
        file_count = 0
        max_bytes = settings.MAX_REPO_SIZE_MB * 1024 * 1024

        for root, dirs, files in os.walk(repo_dir):
            if ".git" in dirs:
                dirs.remove(".git")
            for f in files:
                file_count += 1
                if file_count > settings.MAX_FILE_COUNT:
                    logger.warning(f"Repo exceeds maximum file count limit ({settings.MAX_FILE_COUNT}).")
                    break
                fp = Path(root) / f
                if not fp.is_symlink() and fp.exists():
                    total_size += fp.stat().st_size
                    if total_size > max_bytes:
                        raise IngestionError(
                            f"Repository size exceeds maximum limit of {settings.MAX_REPO_SIZE_MB}MB."
                        )

    def get_commit_history(self, repo_dir: Path, max_count: int = 30) -> list[Dict[str, Any]]:
        """Extract recent commit history log."""
        log_format = "%H%x1f%s%x1f%an%x1f%ad%x1f%h"
        raw_log = self._run_git_cmd(
            ["git", "log", f"-{max_count}", f"--pretty=format:{log_format}", "--date=iso"],
            cwd=repo_dir
        )
        commits = []
        if not raw_log:
            return commits

        for line in raw_log.split("\n"):
            parts = line.strip().split("\x1f")
            if len(parts) >= 5:
                commits.append({
                    "sha": parts[0],
                    "short_sha": parts[4],
                    "message": parts[1],
                    "author": parts[2],
                    "date": parts[3],
                })
        return commits
