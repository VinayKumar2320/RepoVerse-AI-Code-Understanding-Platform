# Deployment Guide

RepoVerse is designed to run in zero-cost or low-cost self-hosted environments.

## 1. Quick Start via Docker Compose
Run the entire production stack (FastAPI backend + Next.js frontend + PostgreSQL + Redis):

```bash
# 1. Clone repository
git clone https://github.com/vinaykumar/repoverse.git
cd repoverse

# 2. Configure environment
cp .env.example .env

# 3. Launch stack
docker compose up --build
```
- Frontend UI: `http://localhost:3000`
- Backend API & OpenAPI Docs: `http://localhost:8000/docs`

## 2. Local Standalone Development (macOS ARM64 / Linux)

### Backend
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/bootstrap_demo.py
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 3. Production Deployment Options
- **Frontend**: Deploy `frontend/` to Vercel or Netlify with `NEXT_PUBLIC_API_URL=https://api.yourdomain.com`.
- **Backend**: Deploy `backend/` to Render, Railway, or Fly.io using `backend/Dockerfile`.
- **Database**: PostgreSQL on Supabase or Neon (free tier), or local SQLite fallback.
