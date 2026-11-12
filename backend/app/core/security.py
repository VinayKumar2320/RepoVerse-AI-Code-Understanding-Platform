import re
from urllib.parse import urlparse
from typing import Tuple, Optional
from backend.app.core.logging import logger

ALLOWED_HOSTS = {"github.com", "www.github.com"}
GITHUB_REPO_REGEX = re.compile(r"^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$")

class SecurityValidationError(ValueError):
    pass

def sanitize_path(path: str) -> str:
    """Ensure path doesn't escape boundaries with directory traversal."""
    cleaned = path.replace("\\", "/").strip()
    parts = []
    for part in cleaned.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)

def validate_github_url(raw_url: str) -> Tuple[str, str, str]:
    """
    Validate and parse a GitHub URL.
    Returns: (normalized_url, owner, repo_name)
    Raises: SecurityValidationError if invalid, SSRF risk, or unsupported host.
    """
    if not raw_url or not isinstance(raw_url, str):
        raise SecurityValidationError("URL must be a non-empty string.")
    
    url = raw_url.strip()
    
    # Check for invalid protocol or non-HTTP(S) schemes
    if not (url.startswith("https://") or url.startswith("http://")):
        # If user just typed github.com/owner/repo or owner/repo
        if re.match(r"^github\.com/[^/]+/[^/]+", url):
            url = f"https://{url}"
        elif GITHUB_REPO_REGEX.match(url):
            url = f"https://github.com/{url}"
        else:
            raise SecurityValidationError("Invalid URL format. Must be an HTTP(S) GitHub URL or owner/repo.")
    
    parsed = urlparse(url)
    
    # Enforce strict hostname allowlist (anti-SSRF)
    if not parsed.hostname or parsed.hostname.lower() not in ALLOWED_HOSTS:
        raise SecurityValidationError(
            f"Host '{parsed.hostname}' is not allowed. Only public 'github.com' repositories are supported."
        )
    
    # Path should be /owner/repo or /owner/repo.git or /owner/repo/tree/branch
    path = parsed.path.strip("/")
    if path.endswith(".git"):
        path = path[:-4]
    
    segments = [s for s in path.split("/") if s]
    if len(segments) < 2:
        raise SecurityValidationError("GitHub URL must contain both an owner and a repository name.")
    
    owner = segments[0]
    repo_name = segments[1]
    
    if not GITHUB_REPO_REGEX.match(f"{owner}/{repo_name}"):
        raise SecurityValidationError(f"Invalid owner or repository name: {owner}/{repo_name}")
    
    # Disallow dangerous names
    for bad in ["..", ".", "~", "$", ";", "&", "|", "`"]:
        if bad in owner or bad in repo_name:
            raise SecurityValidationError("Repository identifier contains forbidden characters.")
    
    normalized_url = f"https://github.com/{owner}/{repo_name}"
    return normalized_url, owner, repo_name
