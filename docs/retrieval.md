# Hybrid Retrieval & Grounded AI

RepoVerse enforces strict factual grounding for all explanations and AI interactions.

## 1. Dual Retrieval Engine
- **BM25 Lexical Ranking**: Pure-Python Okapi BM25 (`rank-bm25`) indexing all parsed symbols, docstrings, method signatures, and file paths.
- **Graph Traversal Expansion**: Given candidate symbol hits, the engine expands the 1-hop neighborhood in the NetworkX graph to include callers, callees, and imported modules.

## 2. Verifiable Citations
Every response includes structured citations:
- `file_path`: Exact file in the repository.
- `start_line` / `end_line`: Precise line range.
- `commit_sha`: The specific commit SHA analyzed (never a drifting branch head).
- `symbol_name`: Canonical symbol identifier.

## 3. Zero-LLM Deterministic Mode
When no API key is provided (`LLM_PROVIDER=none`), RepoVerse operates with 100% deterministic local intelligence:
- Queries are answered by inspecting graph centrality, symbol locations, and caller hierarchies.
- No hallucinations, zero token cost, complete privacy.
