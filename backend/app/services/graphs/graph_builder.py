import os
from pathlib import Path
from typing import List, Dict, Set, Tuple, Optional, Any
import networkx as nx

from backend.app.services.parsing.symbol_types import ParseResult, ParsedSymbol, ParsedImport, ParsedCall
from backend.app.services.parsing.classifier import ClassifiedFile
from backend.app.schemas.architecture import GraphNodeSchema, GraphEdgeSchema
from backend.app.core.logging import logger

class CodeKnowledgeGraph:
    def __init__(self, snapshot_id: str):
        self.snapshot_id = snapshot_id
        self.graph = nx.DiGraph()
        self.files_map: Dict[str, ClassifiedFile] = {}
        self.symbol_index: Dict[str, ParsedSymbol] = {} # qname -> ParsedSymbol
        self.file_symbols: Dict[str, List[ParsedSymbol]] = {} # file_path -> symbols
        self.file_imports: Dict[str, List[ParsedImport]] = {} # file_path -> imports
        self.file_calls: Dict[str, List[ParsedCall]] = {}

    def build(
        self,
        classified_files: List[ClassifiedFile],
        parse_results: List[ParseResult],
        repo_name: str
    ):
        """Construct the multi-level versioned code knowledge graph."""
        self.files_map = {cf.path: cf for cf in classified_files}
        
        # Root repository node
        repo_node_id = f"repo::{repo_name}"
        self.graph.add_node(
            repo_node_id,
            entity_type="Repository",
            label=repo_name,
            qualified_name=repo_name,
            file_path=None,
            level=1,
            metadata={"total_files": len(classified_files)}
        )

        # 1. Directory & Package Nodes (Level 1)
        directories: Set[str] = set()
        for cf in classified_files:
            parts = Path(cf.path).parent.parts
            cur_dir = ""
            for part in parts:
                cur_dir = f"{cur_dir}/{part}" if cur_dir else part
                directories.add(cur_dir)

        for d in sorted(directories):
            dir_node_id = f"dir::{d}"
            parent_dir = str(Path(d).parent)
            parent_id = f"dir::{parent_dir}" if parent_dir != "." and parent_dir != "" else repo_node_id

            self.graph.add_node(
                dir_node_id,
                entity_type="Directory",
                label=Path(d).name,
                qualified_name=d,
                file_path=d,
                level=1,
                metadata={}
            )
            self.graph.add_edge(
                parent_id,
                dir_node_id,
                edge_type="CONTAINS",
                confidence="directly_observed_syntax",
                evidence=f"Directory hierarchy: {parent_id} contains {d}"
            )

        # 2. File & Module Nodes (Level 2)
        for cf in classified_files:
            file_node_id = f"file::{cf.path}"
            dir_path = str(Path(cf.path).parent)
            parent_id = f"dir::{dir_path}" if dir_path != "." and dir_path != "" else repo_node_id

            self.graph.add_node(
                file_node_id,
                entity_type="File",
                label=Path(cf.path).name,
                qualified_name=cf.path,
                file_path=cf.path,
                level=2,
                metadata={
                    "language": cf.language,
                    "category": cf.category,
                    "loc": cf.loc,
                    "size_bytes": cf.size_bytes
                }
            )
            self.graph.add_edge(
                parent_id,
                file_node_id,
                edge_type="CONTAINS",
                confidence="directly_observed_syntax",
                evidence=f"File belongs to folder {dir_path}"
            )

        # 3. Symbols (Classes, Functions, Methods, Endpoints) (Level 3)
        for pr in parse_results:
            self.file_symbols[pr.file_path] = pr.symbols
            self.file_imports[pr.file_path] = pr.imports
            self.file_calls[pr.file_path] = pr.calls

            file_node_id = f"file::{pr.file_path}"

            for sym in pr.symbols:
                if sym.kind == "module":
                    continue
                self.symbol_index[sym.qualified_name] = sym
                sym_node_id = f"sym::{sym.qualified_name}"

                self.graph.add_node(
                    sym_node_id,
                    entity_type=sym.kind.capitalize(),
                    label=sym.name,
                    qualified_name=sym.qualified_name,
                    file_path=pr.file_path,
                    level=3,
                    metadata={
                        "start_line": sym.start_line,
                        "end_line": sym.end_line,
                        "parameters": sym.parameters,
                        "decorators": sym.decorators,
                        "docstring": sym.docstring,
                    }
                )

                # Connect File -> Symbol (DEFINES)
                self.graph.add_edge(
                    file_node_id,
                    sym_node_id,
                    edge_type="DEFINES",
                    confidence="directly_observed_syntax",
                    evidence=f"Defined at lines {sym.start_line}-{sym.end_line}"
                )

                # Class inheritance (INHERITS)
                if sym.kind == "class" and sym.bases:
                    for base in sym.bases:
                        target_id = self._resolve_class_target(base, pr.file_path)
                        if target_id:
                            self.graph.add_edge(
                                sym_node_id,
                                target_id,
                                edge_type="INHERITS",
                                confidence="statically_resolved",
                                evidence=f"Class inherits from {base}"
                            )

        # 4. Resolve Imports (Module -> Module / Dependency)
        for pr in parse_results:
            source_file_id = f"file::{pr.file_path}"
            for imp in pr.imports:
                resolved_file = self._resolve_import_to_file(imp, pr.file_path)
                if resolved_file:
                    target_file_id = f"file::{resolved_file}"
                    if self.graph.has_node(target_file_id):
                        self.graph.add_edge(
                            source_file_id,
                            target_file_id,
                            edge_type="IMPORTS",
                            confidence="statically_resolved",
                            evidence=f"Imported '{imp.module}' at line {imp.line}"
                        )
                else:
                    # External Dependency node (e.g. FastAPI, React, PyTorch)
                    ext_name = imp.module.split(".")[0] if "." in imp.module else imp.module
                    if ext_name and not ext_name.startswith("."):
                        ext_node_id = f"dep::{ext_name}"
                        if not self.graph.has_node(ext_node_id):
                            self.graph.add_node(
                                ext_node_id,
                                entity_type="ExternalDependency",
                                label=ext_name,
                                qualified_name=ext_name,
                                file_path=None,
                                level=2,
                                metadata={"is_external": True}
                            )
                        self.graph.add_edge(
                            source_file_id,
                            ext_node_id,
                            edge_type="DEPENDS_ON",
                            confidence="statically_resolved",
                            evidence=f"External dependency '{ext_name}'"
                        )

        # 5. Resolve Calls (Level 3)
        for pr in parse_results:
            for call in pr.calls:
                target_sym_id = self._resolve_call_target(call, pr.file_path)
                if target_sym_id and call.context_symbol:
                    src_sym_id = f"sym::{call.context_symbol}"
                    if self.graph.has_node(src_sym_id) and self.graph.has_node(target_sym_id):
                        self.graph.add_edge(
                            src_sym_id,
                            target_sym_id,
                            edge_type="CALLS",
                            confidence="statically_resolved",
                            evidence=f"Call to '{call.callee}' at line {call.line}"
                        )

    def _resolve_import_to_file(self, imp: ParsedImport, current_file: str) -> Optional[str]:
        """Statically resolves an import path to a concrete repository file."""
        curr_dir = Path(current_file).parent

        # 1. Relative imports
        if imp.is_relative:
            target_path = (curr_dir / imp.module).resolve()
            # Try extensions
            for ext in [".py", ".ts", ".tsx", ".js", ".jsx"]:
                cand = str(target_path.with_suffix(ext))
                if cand in self.files_map:
                    return cand
            # Try index
            for ext in [".ts", ".tsx", ".js", ".py"]:
                cand = f"{target_path}/index{ext}"
                if cand in self.files_map:
                    return cand

        # 2. Absolute or package-rooted imports (e.g. "backend.app.core.config" -> "backend/app/core/config.py")
        mod_as_path = imp.module.replace(".", "/")
        for cand_file in self.files_map.keys():
            if cand_file.startswith(mod_as_path) or mod_as_path in cand_file:
                return cand_file

        return None

    def _resolve_class_target(self, base_name: str, current_file: str) -> Optional[str]:
        # Check current file first
        local_qname = f"{current_file}::{base_name}"
        if f"sym::{local_qname}" in self.graph:
            return f"sym::{local_qname}"
        # Search global index
        for qname in self.symbol_index.keys():
            if qname.endswith(f"::{base_name}"):
                return f"sym::{qname}"
        return None

    def _resolve_call_target(self, call: ParsedCall, current_file: str) -> Optional[str]:
        callee_simple = call.callee.split(".")[-1]
        # Match symbol name in index
        for qname, sym in self.symbol_index.items():
            if sym.name == callee_simple:
                # Prioritize same file
                if qname.startswith(current_file):
                    return f"sym::{qname}"
        # Fallback to any matching symbol
        for qname, sym in self.symbol_index.items():
            if sym.name == callee_simple:
                return f"sym::{qname}"
        return None

    def get_view_for_level(self, level: int = 1, max_nodes: int = 150) -> Tuple[List[GraphNodeSchema], List[GraphEdgeSchema]]:
        """Return aggregated graph representation filtered to specified abstraction level with performance bounding."""
        nodes = []
        edges = []

        valid_node_ids = set()
        level_candidates = []
        
        for nid, data in self.graph.nodes(data=True):
            node_level = data.get("level", 1)
            # Level 1: Packages / Directories / Repo
            # Level 2: Files / Modules / External Dependencies
            # Level 3: All symbols (Classes, Functions, Endpoints)
            if node_level <= level:
                degree = self.graph.degree(nid)
                level_candidates.append((degree, nid, data))

        # Prioritize higher-degree nodes if count exceeds max_nodes to ensure 60fps rendering
        if len(level_candidates) > max_nodes and level == 3:
            # Preserve all level 1 and 2 nodes
            core_nodes = [item for item in level_candidates if item[2].get("level", 1) < 3]
            symbol_nodes = sorted(
                [item for item in level_candidates if item[2].get("level", 1) == 3],
                key=lambda x: x[0],
                reverse=True
            )[: max_nodes - len(core_nodes)]
            level_candidates = core_nodes + symbol_nodes

        for _, nid, data in level_candidates:
            valid_node_ids.add(nid)
            nodes.append(GraphNodeSchema(
                id=nid,
                entity_type=data.get("entity_type", "Unknown"),
                label=data.get("label", nid),
                qualified_name=data.get("qualified_name", nid),
                file_path=data.get("file_path"),
                level=data.get("level", 1),
                metadata=data.get("metadata", {})
            ))

        for u, v, data in self.graph.edges(data=True):
            if u in valid_node_ids and v in valid_node_ids:
                edge_id = f"{u}-->{v}:{data.get('edge_type', 'LINK')}"
                edges.append(GraphEdgeSchema(
                    id=edge_id,
                    source=u,
                    target=v,
                    edge_type=data.get("edge_type", "DEPENDS_ON"),
                    evidence=data.get("evidence"),
                    confidence=data.get("confidence", "statically_resolved"),
                    source_line=data.get("source_line")
                ))

        return nodes, edges
