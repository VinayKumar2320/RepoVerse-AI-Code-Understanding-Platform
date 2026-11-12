FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (git, build tools for tree-sitter C extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and install Python packages
COPY backend/pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . greenlet

# Copy source code and scripts
COPY backend/ backend/
COPY analysis/ analysis/
COPY benchmarks/ benchmarks/
COPY scripts/ scripts/

ENV PYTHONPATH=/app/backend:/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Create repos directory with permissive access for ephemeral cloud containers
RUN mkdir -p /tmp/repoverse_repos /app/repoverse_repos && \
    chmod -R 777 /tmp/repoverse_repos /app/repoverse_repos

EXPOSE 8000 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/v1/health || exit 1

CMD ["/bin/sh", "backend/start.sh"]
