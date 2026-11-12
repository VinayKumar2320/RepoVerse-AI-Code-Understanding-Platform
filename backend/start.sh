#!/bin/sh
set -e

PORT="${PORT:-8000}"
echo "Starting RepoVerse API on port ${PORT}..."

# Initialize database tables and demo fixtures
python -c "
import asyncio
from backend.app.core.database import init_db
asyncio.run(init_db())
"

exec uvicorn backend.app.main:app --host 0.0.0.0 --port "$PORT" --workers 1
