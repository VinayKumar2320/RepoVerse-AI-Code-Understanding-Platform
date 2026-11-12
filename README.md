# RepoVerse — Interactive GitHub Repository Digital Twin & AI Code Understanding Platform

[![RepoVerse CI](https://github.com/VinayKumar2320/RepoVerse-AI-Code-Understanding-Platform/actions/workflows/ci.yml/badge.svg)](https://github.com/VinayKumar2320/RepoVerse-AI-Code-Understanding-Platform/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
[![Next.js 14](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org)

> **Tagline:** *Understand Code. Explore Architecture. Travel Through Git History.*

RepoVerse transforms any public GitHub repository into a versioned, navigable architectural digital twin with source-grounded code intelligence and adaptive multi-tier learning.

---

## 1. Architectural Philosophy

RepoVerse operates on a fundamental distinction:
> **The Code Knowledge Graph is the deterministic source of truth. The LLM is an explanation layer, not the foundation.**

Rather than sending raw repository text directly to an LLM context, RepoVerse parses abstract syntax trees, resolves imports, constructs a versioned dependency graph, and grounds all AI explanations in verifiable file and line citations.

```
GitHub Repository URL / Local Git
        │
        ▼
[ Security & URL Validation ]  <-- Host allowlist, SSRF, path traversal protection
        │
        ▼
[ Ingestion & Clone Engine ]   <-- Shallow clone / commit checkout / cache by SHA
        │
        ▼
[ File Classifier ]            <-- Source, tests, configs, build, docs; ignore rules
        │
        ▼
[ Multi-Language AST Parsers ] <-- Python AST + Tree-sitter (Python, JS, TS)
        │
        ▼
[ Symbol & Import Resolver ]   <-- Canonical symbol IDs, import graph, call resolution
        │
        ▼
[ Versioned Code Graph ]       <-- Nodes (Repo, Module, Class, Func), Edges (IMPORTS, CALLS, CONTAINS)
        │
        ├────────────────────────────┬─────────────────────────────┐
        ▼                            ▼                             ▼
[ Architecture Analytics ]     [ CodeFlow Engine ]         [ Hybrid Retrieval & Search ]
(Cycles, coupling, centrality) (Call hierarchy tracing)   (BM25 + Symbol + Graph + Vector)
        │                            │                             │
        └────────────────────────────┼─────────────────────────────┘
                                     ▼
                      [ Adaptive Learning Engine ]
                  (Beginner, Developer, Senior Engineer)
                                     ▼
                           [ FastAPI REST APIs ]
                                     ▼
                         [ RepoVerse Next.js UI ]
             (React Flow Map, Monaco Editor, Time Machine, Lab)
```

---

## 2. Core Features

### 1. Interactive Architecture Map (`React Flow`)
- Multi-level abstraction:
  - **Level 1 (Packages)**: Architectural boundaries, packages, and folders.
  - **Level 2 (Modules)**: Source files, internal imports, and third-party dependencies.
  - **Level 3 (Symbols)**: Classes, methods, functions, and endpoints.
- Color-coded edge semantics (`IMPORTS`, `CALLS`, `INHERITS`, `DEFINES`, `DEPENDS_ON`).
- Interactive zoom, pan, search filtering, and node detail side-panels.

### 2. Adaptive Repository Learning ("Explain This Repository Like I'm New Here")
- **Beginner Mode**: Conceptual analogies, simple language, folder roles, execution entry points, and comprehension checks.
- **Developer Mode**: Layered architecture, API routing, data flow, service contracts, and development commands.
- **Senior Engineer Mode**: Martin's instability metric ($I = \frac{C_e}{C_a + C_e}$), Tarjan's Strongly Connected Components (SCC), dependency cycle analysis, coupling hotspots, and refactoring recommendations.
- **Shared Evidence Guarantee**: Switching levels adapts explanation depth without reindexing.

### 3. Code Flow Explorer
- Traces execution paths from entry points (`main.py`, route handlers, endpoints) through service layers and data access models.
- Step-by-step sequential invocation timeline with confidence indicators (`statically_resolved`, `inferred`).

### 4. Git Time Machine
- Interactive historical commit timeline.
- Select any two commits to compute an exact structural diff: added/removed nodes, added/removed dependencies, and cycle count deltas.

### 5. Architecture Lab (What-If Simulator)
- Speculative structural mutations on an in-memory deep copy of the repository graph.
- Test removing dependency edges or moving modules to observe changes in coupling and cycle count before refactoring.

### 6. Source-Grounded Q&A & Embedded Monaco Editor
- Hybrid retrieval (BM25 lexical ranking + graph neighborhood traversal).
- Verifiable citations with commit-pinned GitHub links (`#L{start}-#L{end}`).
- Zero-token deterministic mode when running offline or without an LLM key.
- Monaco Editor with syntax highlighting and jump-to-line capability.

---

## 3. Technology Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS, `@xyflow/react`, `@monaco-editor/react`, Zustand, Lucide React.
- **Backend**: Python 3.12+ (tested on Python 3.13 macOS ARM64), FastAPI, SQLAlchemy 2.x (asyncio), NetworkX 3.7.
- **Parsing**: Tree-sitter (`tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`), Python native AST.
- **Storage**: SQLite (`aiosqlite`) for zero-config local development; PostgreSQL for production containers.
- **Testing**: Pytest, Pytest-asyncio, HTTPX.

---

## 4. Benchmark & Evaluation Results

Tested on macOS ARM64 (Apple Silicon):
- **Python AST Parser**: 0.126 ms per file (100% ground-truth symbol recall).
- **Tree-sitter TypeScript Parser**: 0.203 ms per file.
- **Graph Construction**: 0.085 ms for full modular graph assembly.
- **Tarjan SCC & Centrality**: 32.76 ms for complete PageRank and instability metrics.

---

## 5. Quick Start

### Option A: Docker Compose (All-in-One)
```bash
docker compose up --build
```
- Frontend UI: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`

### Option B: Local Standalone Development

#### 1. Backend Setup
```bash
# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
pip install greenlet

# Seed demo repositories & run tests
python scripts/bootstrap_demo.py
pytest

# Launch FastAPI server
uvicorn backend.app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 6. Free-Tier Cloud Deployment ($0/month)

- **Backend**: Deployed on [Render](https://render.com) using the included `render.yaml` blueprint.
- **Frontend**: Deployed on [Vercel](https://vercel.com) connecting to Render API via `NEXT_PUBLIC_API_URL`.
- **Database**: Ephemeral SQLite by default, or persistent serverless PostgreSQL on [Neon.tech](https://neon.tech).

Detailed instructions are available in [docs/deployment.md](docs/deployment.md).

---

## 7. Security & Ingestion Safeguards

- **SSRF Defense**: Strict hostname allowlisting (`github.com` only); private IP ranges and alternate URI schemes are rejected.
- **Command Injection Prevention**: All Git commands execute via structured argument lists; `shell=True` is prohibited.
- **Untrusted Code Isolation**: Ingested code is never executed or compiled; repository scripts and dependency installers are blocked.
- **Resource Quotas**: Maximum 150MB repository size, 3,000 file ceiling, and 60-second clone timeout.

---

## 8. Repository Link
- GitHub: [https://github.com/VinayKumar2320/RepoVerse-AI-Code-Understanding-Platform](https://github.com/VinayKumar2320/RepoVerse-AI-Code-Understanding-Platform)

## 9. License
MIT
