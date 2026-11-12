# RepoVerse Architecture Specification

## 1. System Vision
RepoVerse is an interactive GitHub Repository Digital Twin & AI Code Understanding Platform. It transforms public GitHub repositories into versioned, navigable architectural knowledge graphs with source-grounded intelligence and adaptive learning ("Explain This Repository Like I'm New Here").

Tagline: **Understand Code. Explore Architecture. Travel Through Git History.**

RepoVerse is built upon a fundamental architectural distinction:
**The Code Knowledge Graph is the deterministic source of truth; the LLM is an explanation layer.**

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

## 2. Core Components

### 2.1 Backend (Python 3.12+ / FastAPI / SQLAlchemy)
- `FastAPI`: High-performance asynchronous REST API handling repository ingestion, graph exploration, code flow tracing, and AI chat.
- `SQLAlchemy 2.x`: Asynchronous ORM models compatible with PostgreSQL (production) and SQLite (zero-config local development).
- `NetworkX`: Graph algorithms including PageRank centrality, Tarjan's Strongly Connected Components (SCC), elementary cycle enumeration, and reachability.

### 2.2 Multi-Language Parsing (Tree-sitter & Python AST)
- `PythonASTParser`: Zero-dependency, 100% accurate symbol, method, class, and call extraction using Python's native `ast`.
- `TreeSitterParser`: Native tree-sitter grammars (`tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`) for fast parsing of modern TypeScript, JavaScript, and JSX/TSX.

### 2.3 Frontend (Next.js App Router / React / Tailwind CSS)
- `@xyflow/react` (React Flow): Multi-level interactive architecture graph with level aggregation (Packages -> Modules -> Symbols).
- `@monaco-editor/react`: Embedded VS Code Monaco editor with line pinning, jump to definition, and commit-pinned GitHub links.
- `Zustand`: Reactive client state managing selected nodes, files, experience tiers, and active tools.
