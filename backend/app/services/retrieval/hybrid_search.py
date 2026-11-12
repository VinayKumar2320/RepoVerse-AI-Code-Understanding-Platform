import re
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import networkx as nx

from backend.app.services.parsing.classifier import ClassifiedFile
from backend.app.services.parsing.symbol_types import ParsedSymbol
from backend.app.schemas.chat import CitationSchema

class HybridRetrievalEngine:
    def __init__(self, commit_sha: str):
        self.commit_sha = commit_sha
        self.documents: List[Dict[str, Any]] = []
        self.bm25: Optional[BM25Okapi] = None

    def index_repository(
        self,
        files: List[ClassifiedFile],
        symbols: List[ParsedSymbol],
        nx_graph: nx.DiGraph
    ):
        """Indexes source code files, extracted symbols, and graph context into BM25 index."""
        corpus = []
        self.documents = []

        # 1. Index symbols
        for sym in symbols:
            text = f"{sym.name} {sym.qualified_name} {sym.kind} {sym.docstring or ''} {' '.join(sym.decorators)} {' '.join(sym.parameters)}"
            tokens = self._tokenize(text)
            corpus.append(tokens)
            fpath = sym.qualified_name.split("::")[0]
            self.documents.append({
                "type": "symbol",
                "name": sym.name,
                "qualified_name": sym.qualified_name,
                "file_path": fpath,
                "start_line": sym.start_line,
                "end_line": sym.end_line,
                "docstring": sym.docstring,
                "snippet": f"{sym.kind} {sym.name}({', '.join(sym.parameters)})",
            })

        # 2. Index files & documentation
        for f in files:
            text = f"{f.path} {f.language} {f.category}"
            tokens = self._tokenize(text)
            corpus.append(tokens)
            self.documents.append({
                "type": "file",
                "name": Path(f.path).name,
                "qualified_name": f.path,
                "file_path": f.path,
                "start_line": 1,
                "end_line": min(f.loc, 50),
                "snippet": f"File: {f.path} ({f.language}, {f.loc} LOC)",
            })

        if corpus:
            self.bm25 = BM25Okapi(corpus)

    def _tokenize(self, text: str) -> List[str]:
        # Split camelCase, snake_case, punctuation
        cleaned = re.sub(r"[^a-zA-Z0-9_]", " ", text)
        words = re.sub(r"([a-z])([A-Z])", r"\1 \2", cleaned).lower().split()
        return words

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search query using lexical and symbol matching."""
        if not self.bm25 or not self.documents:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return self.documents[:top_k]

        scores = self.bm25.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]

        results = []
        for idx in top_indices:
            doc = dict(self.documents[idx])
            doc["score"] = float(scores[idx])
            results.append(doc)
        return results

    def get_citations(self, search_results: List[Dict[str, Any]]) -> List[CitationSchema]:
        citations = []
        seen = set()
        for res in search_results:
            key = (res["file_path"], res["start_line"], res["end_line"])
            if key not in seen:
                seen.add(key)
                citations.append(CitationSchema(
                    file_path=res["file_path"],
                    start_line=res["start_line"],
                    end_line=res["end_line"],
                    symbol_name=res.get("name"),
                    commit_sha=self.commit_sha,
                    snippet=res.get("snippet")
                ))
        return citations
from pathlib import Path
