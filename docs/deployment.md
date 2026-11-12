# Zero-Cost Production Deployment Guide

RepoVerse is architected to run permanently on $0/month free-tier cloud infrastructure while maintaining high availability, responsive static-analysis response times, and full feature fidelity.

---

## 1. Production Architecture Overview

```
┌─────────────────────────────────┐       ┌─────────────────────────────────┐
│     Vercel Edge Network         │       │        Render Web Service       │
│  (Next.js 14 Frontend App)      │       │     (FastAPI Docker Backend)    │
│                                 │       │                                 │
│  - React Flow Visualization     │──────▶│  - Python AST & Tree-sitter     │
│  - Adaptive Learning Studio     │ HTTP  │  - NetworkX Code Graph Engine   │
│  - Monaco Code Viewer           │ (CORS)│  - BM25 Grounded Retrieval      │
│  - What-If Architecture Lab     │       │  - Bounded Ingestion Sandbox    │
└─────────────────────────────────┘       └────────────────┬────────────────┘
                                                           │
                                                           ▼
                                          ┌─────────────────────────────────┐
                                          │      Managed PostgreSQL         │
                                          │     (Neon.tech Free Tier)       │
                                          │                                 │
                                          │  - Persistent Snapshots         │
                                          │  - Extracted Symbols Index      │
                                          │  - Bookmarks & Diff Cache       │
                                          └─────────────────────────────────┘
```

---

## 2. Deploying Backend on Render ($0/month)

### Option A: Using `render.yaml` Blueprint (Recommended)
1. In the Render Dashboard, click **New** > **Blueprint**.
2. Connect your GitHub repository `https://github.com/VinayKumar2320/RepoVerse-AI-Code-Understanding-Platform`.
3. Render automatically detects `render.yaml` and deploys the `repoverse-api` Docker service.

### Option B: Manual Web Service Setup
1. **New Web Service** > Connect GitHub repository.
2. Select **Docker** runtime.
3. **Dockerfile Path**: `backend/Dockerfile`
4. **Docker Context**: `.`
5. **Health Check Path**: `/api/v1/health`
6. Set Environment Variables:
   - `ENV`: `production`
   - `PORT`: `10000`
   - `LLM_PROVIDER`: `none` (or `openai`/`gemini` if API key configured)
   - `DATABASE_URL`: `sqlite+aiosqlite:///./repoverse.db` (or your Neon/Supabase URL)
   - `MAX_REPO_SIZE_MB`: `100`
   - `MAX_FILE_COUNT`: `2000`
   - `CLONE_TIMEOUT_SECONDS`: `60`
7. Click **Deploy Web Service**. Render assigns a URL like `https://repoverse-api.onrender.com`.

---

## 3. Deploying Frontend on Vercel ($0/month)

1. Open [Vercel Dashboard](https://vercel.com) and click **Add New** > **Project**.
2. Import repository `VinayKumar2320/RepoVerse-AI-Code-Understanding-Platform`.
3. Configure project settings:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `next build`
   - **Output Directory**: `.next`
   - **Install Command**: `npm install`
4. Add Environment Variable:
   - `NEXT_PUBLIC_API_URL`: `https://<your-render-backend-url>` (e.g. `https://repoverse-api.onrender.com`)
5. Click **Deploy**. Vercel provides a custom URL like `https://repoverse.vercel.app`.

---

## 4. Free-Tier Managed PostgreSQL (Optional Persistence)

On Render's free tier, the local container disk is ephemeral. To persist repository analyses permanently across container restarts:
1. Create a free PostgreSQL database at [Neon.tech](https://neon.tech) (0.5GB storage, 100% free forever).
2. Copy the Connection String: `postgres://user:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require`
3. Add it as `DATABASE_URL` in your Render Environment Variables.
4. RepoVerse's `normalize_database_url` automatically adapts this connection string for SQLAlchemy 2.0 async.

---

## 5. Free-Tier Resource Safeguards

- **Cold Starts**: Render free-tier spins down after 15 minutes of inactivity. RepoVerse frontend includes clear cold-start detection advising users of initial 30-45s wake-up times.
- **Cache Eviction**: `CloneService._prune_old_caches()` automatically keeps at most 5 cached clones to stay strictly within ephemeral disk limits.
- **Graph Clustering**: React Flow view pagination caps Level 3 symbols to the top 150 highest-degree nodes for 60fps rendering.
