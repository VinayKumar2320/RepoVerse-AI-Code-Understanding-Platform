# RepoVerse Development Plan & Engineering Specification

## 1. System Vision & Overview
RepoVerse is an interactive GitHub Repository Digital Twin & AI Code Understanding Platform. It transforms public GitHub repositories into versioned, navigable architectural knowledge graphs with source-grounded intelligence and adaptive learning ("Explain This Repository Like I'm New Here").

Tagline: **Understand Code. Explore Architecture. Travel Through Git History.**

RepoVerse is built upon a fundamental architectural distinction:
**The Code Knowledge Graph is the deterministic source of truth; the LLM is an explanation layer.**

---

## 2. Environment & Tooling Verification
- **Host OS**: macOS ARM64 (Apple Silicon)
- **Runtime**: Python 3.13 / 3.12 compatible (`.venv`), Node v26, Next.js 14/15, React 18/19
- **Parsing**: Tree-sitter 0.26+ (`tree-sitter-python`, `tree-sitter-javascript`, `tree-sitter-typescript`), Python built-in AST
- **Graph & Algorithms**: NetworkX 3.7, PostgreSQL 16 / SQLite local fallback
- **Frontend Stack**: Next.js App Router, TypeScript, Tailwind CSS, Lucide React, `@xyflow/react` (React Flow), `@monaco-editor/react`, Zustand, TanStack Query

---

## 3. Supported Languages & Parsing Strategy
1. **Python**:
   - Primary: Built-in `ast` module (100% complete symbol, import, call, docstring extraction)
   - Secondary: Tree-sitter Python for AST traversal and token alignment
2. **TypeScript & JavaScript**:
   - Tree-sitter TypeScript & JavaScript parsers
   - Extracts: Imports, exports, classes, functions, arrow functions, interfaces, methods, calls, JSX components
3. **Other Languages**:
   - Structural file classification, LOC counting, directory hierarchy, basic pattern/regex symbol extraction

---

## 4. Limitations & Non-Goals
- **Dynamic Resolution**: Dynamic Python imports (`__import__`, `getattr`) or runtime JS `eval()` are marked with `confidence: inferred` or `unresolved` rather than guessed.
- **Untrusted Code Execution**: RepoVerse **never** executes repository code, scripts, or installs packages from ingested repositories.
- **Offline / Zero-API Key Guarantee**: Fully functioning non-LLM mode provides deterministic architecture summaries, graph metrics, codeflow tracing, and symbol navigation.
- **Memory & Scale Bounding**: Very large repositories are filtered (configurable file size max 1MB, excludes `node_modules`, `.git`, `dist`, `__pycache__`, etc.).

---

## 5. Architectural Blueprint

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

## 6. Database Models Specification (SQLAlchemy 2.x)

1. **`Repository`**: `id`, `url`, `owner`, `name`, `default_branch`, `description`, `stars`, `primary_language`, `created_at`
2. **`RepositorySnapshot`**: `id`, `repository_id`, `commit_sha`, `branch`, `analyzed_at`, `status`, `total_files`, `total_lines`, `languages_summary`, `overview_json`
3. **`SourceFile`**: `id`, `snapshot_id`, `path`, `language`, `category` (source/test/config/doc), `loc`, `size_bytes`, `content_snippet`
4. **`CodeSymbol`**: `id`, `snapshot_id`, `file_id`, `name`, `qualified_name`, `kind` (function/class/method/endpoint/module), `start_line`, `end_line`, `docstring`
5. **`GraphNode`**: `id`, `snapshot_id`, `entity_type`, `name`, `qualified_name`, `file_path`, `metadata_json`
6. **`GraphEdge`**: `id`, `snapshot_id`, `source_node_id`, `target_node_id`, `edge_type` (CONTAINS/IMPORTS/CALLS/INHERITS/DEFINES/TESTS), `evidence`, `confidence`, `source_line`
7. **`LearningStep` / `LearningPath`**: Guided repository walkthrough per experience tier
8. **`Bookmark`**: Saved files, symbols, and notes
9. **`ArchitectureDiff`**: Computed comparison between two snapshots (added/removed nodes, edges, cycles)

---

## 7. API Contracts (FastAPI v1)

- `GET  /api/v1/health` -> Status & system diagnostics
- `POST /api/v1/repositories/analyze` -> Start ingestion & analysis job
- `GET  /api/v1/repositories/{id}` -> Repository metadata
- `GET  /api/v1/repositories/{id}/status` -> Analysis progress & job state
- `GET  /api/v1/repositories/{id}/overview` -> Architecture overview & tech stack
- `GET  /api/v1/repositories/{id}/files` -> Hierarchical file tree
- `GET  /api/v1/repositories/{id}/architecture` -> React Flow node/edge payload with level filters (1=Packages, 2=Modules, 3=Symbols)
- `GET  /api/v1/repositories/{id}/symbols` -> Symbol index & definitions
- `GET  /api/v1/repositories/{id}/codeflow` -> Static call graph & execution traces
- `GET  /api/v1/repositories/{id}/learning` -> Adaptive learning content (Beginner, Developer, Senior)
- `POST /api/v1/repositories/{id}/questions` -> Source-grounded Q&A with citations
- `GET  /api/v1/repositories/{id}/history` -> Commit timeline and analyzed revisions
- `GET  /api/v1/repositories/{id}/diff` -> Architecture diff between two commit SHAs
- `POST /api/v1/repositories/{id}/simulations` -> What-If graph mutations & impact analysis
- `GET  /api/v1/repositories/{id}/analytics` -> Graph metrics: fan-in/out, cycles, coupling, SCC

---

## 8. Phased Implementation Roadmap

- **Milestone 1: Working MVP**
  - Project foundation (backend + frontend + configs + docker-compose)
  - Safe ingestion service & GitHub URL validator
  - File classifier & ignore engine
  - Python AST parser & symbol extractor
  - Graph builder (NetworkX + storage)
  - Overview generator (deterministic + adaptive)
  - Frontend shell with file tree, overview, and 3-mode switch (Beginner/Dev/Senior)
  
- **Milestone 2: Code Intelligence**
  - Tree-sitter parsers for TypeScript & JavaScript
  - Symbol resolution & import linking
  - Code Flow Explorer with static trace hierarchies
  - Monaco editor with commit-pinned line jump and source inspection
  - React Flow multi-level architecture graph

- **Milestone 3: AI Understanding & Adaptive Learning**
  - Hybrid retrieval engine (BM25 lexical + symbol lookup + graph neighborhood)
  - Provider-agnostic LLM client (with rich deterministic no-LLM mode)
  - "Explain This Repository Like I'm New Here" adaptive prompt engineering
  - Guided learning journeys with comprehension checkpoints
  - Source-grounded Q&A with verifiable file/line citations

- **Milestone 4: Digital Twin & Advanced Capabilities**
  - Git Time Machine: commit comparisons, architecture diffing
  - Architecture Health Analytics: fan-in/fan-out, cycle detection, coupling
  - Architecture Lab: What-If structural simulator (in-memory graph copy)
  - User bookmarks and session persistence

- **Milestone 5: Production Quality, Benchmarking & Deployment**
  - Comprehensive unit and integration test suite
  - Ground-truth evaluation benchmarks on real repositories
  - Docker Compose configuration and production build verification
  - Complete documentation suite
