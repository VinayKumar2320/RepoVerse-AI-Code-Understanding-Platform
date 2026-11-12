# Security & Ingestion Safeguards

Ingesting public code from GitHub presents serious security attack vectors. RepoVerse enforces defense-in-depth isolation across all boundaries:

## 1. URL & Host Allowlisting
- Only `github.com` and `www.github.com` URLs are accepted.
- Strict anti-SSRF: Private IP ranges (`127.0.0.1`, `169.254.169.254`, `10.x.x.x`, `192.168.x.x`) and alternate protocols (`file://`, `ssh://`, `ftp://`) are rejected at the edge.

## 2. Shell Injection Defense
- Git commands are executed exclusively via subprocess argument lists (`["git", "clone", ...]`).
- `shell=True` is forbidden throughout the codebase.

## 3. Quotas & Resource Limiting
- `MAX_REPO_SIZE_MB`: 150MB maximum repository storage.
- `MAX_FILE_COUNT`: 3,000 files limit.
- `MAX_FILE_SIZE_BYTES`: 1MB per single file (skips massive minified bundles).
- `CLONE_TIMEOUT_SECONDS`: 60 seconds hard timeout on network git clone operations.

## 4. No Execution Policy
- RepoVerse **never** installs dependencies (`pip install`, `npm install`) from analyzed repositories.
- Ingested repository scripts or setup files are parsed statically as plain text, never executed.
- Symlinks pointing outside repository bounds are pruned.
