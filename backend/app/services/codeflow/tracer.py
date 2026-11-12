from typing import List, Dict, Any, Optional
import networkx as nx

from backend.app.schemas.codeflow import CodeFlowNode, CodeFlowTraceResponse
from backend.app.services.parsing.symbol_types import ParsedSymbol
from backend.app.core.logging import logger

class CodeFlowTracer:
    def trace_flow(
        self,
        nx_graph: nx.DiGraph,
        symbol_index: Dict[str, ParsedSymbol],
        start_symbol_name_or_qname: str,
        max_depth: int = 5
    ) -> CodeFlowTraceResponse:
        """
        Traces execution path starting from an entry point or function.
        Traverses CALLS edges recursively in the graph up to max_depth.
        """
        # 1. Locate starting symbol node
        start_node_id = None
        start_sym: Optional[ParsedSymbol] = None

        # Exact match
        cand_id = f"sym::{start_symbol_name_or_qname}"
        if nx_graph.has_node(cand_id):
            start_node_id = cand_id
            start_sym = symbol_index.get(start_symbol_name_or_qname)
        else:
            # Fuzzy / prefix search
            for nid, data in nx_graph.nodes(data=True):
                if data.get("label") == start_symbol_name_or_qname or nid.endswith(f"::{start_symbol_name_or_qname}"):
                    start_node_id = nid
                    start_sym = symbol_index.get(data.get("qualified_name"))
                    break

        # Fallback to first endpoint or first function if not found
        if not start_node_id:
            for nid, data in nx_graph.nodes(data=True):
                if data.get("entity_type") in ("Endpoint", "Function") and not data.get("file_path", "").startswith("test"):
                    start_node_id = nid
                    start_sym = symbol_index.get(data.get("qualified_name"))
                    break

        if not start_node_id:
            return CodeFlowTraceResponse(
                entry_point_id="none",
                entry_symbol="None",
                entry_file="",
                nodes=[],
                call_edges=[],
                narrative="No entry points or callable functions found in analyzed graph."
            )

        # 2. Traverse CALLS edges
        visited_nodes = []
        call_edges = []
        seen = {start_node_id}
        queue = [(start_node_id, 1)]

        order = 1
        while queue:
            curr_id, depth = queue.pop(0)
            data = nx_graph.nodes.get(curr_id, {})
            qname = data.get("qualified_name", curr_id)
            sym = symbol_index.get(qname)

            fpath = data.get("file_path") or (sym.qualified_name.split("::")[0] if sym else "unknown")
            sline = sym.start_line if sym else 1
            eline = sym.end_line if sym else 10
            kind = data.get("entity_type", "Function").lower()

            visited_nodes.append(CodeFlowNode(
                id=curr_id,
                symbol_name=data.get("label", curr_id),
                qualified_name=qname,
                kind=kind,
                file_path=fpath,
                start_line=sline,
                end_line=eline,
                snippet=sym.docstring or f"Calls inside {data.get('label')}",
                step_order=order,
                confidence="statically_resolved"
            ))
            order += 1

            if depth < max_depth:
                # Find outgoing CALLS edges
                for _, neighbor, edge_data in nx_graph.out_edges(curr_id, data=True):
                    if edge_data.get("edge_type") == "CALLS" and neighbor not in seen:
                        seen.add(neighbor)
                        call_edges.append({
                            "source": curr_id,
                            "target": neighbor,
                            "evidence": edge_data.get("evidence", "Function call invocation"),
                            "confidence": edge_data.get("confidence", "statically_resolved")
                        })
                        queue.append((neighbor, depth + 1))

        narrative = (
            f"Execution begins at `{visited_nodes[0].symbol_name}` in `{visited_nodes[0].file_path}`. "
            f"Static call tracing resolves {len(visited_nodes)} sequential execution steps "
            f"across {len(call_edges)} internal method invocations."
        )

        return CodeFlowTraceResponse(
            entry_point_id=start_node_id,
            entry_symbol=visited_nodes[0].symbol_name,
            entry_file=visited_nodes[0].file_path,
            nodes=visited_nodes,
            call_edges=call_edges,
            narrative=narrative
        )
