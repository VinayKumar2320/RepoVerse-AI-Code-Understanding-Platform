from typing import Dict, Any, List, Set
import networkx as nx

from backend.app.schemas.history import ArchitectureDiffResponse

class ArchitectureDiffService:
    def compare_snapshots(
        self,
        base_commit: str,
        target_commit: str,
        base_graph: nx.DiGraph,
        target_graph: nx.DiGraph
    ) -> ArchitectureDiffResponse:
        """
        Calculates exact graph delta between two commit snapshots:
        - Added / Removed Nodes
        - Added / Removed Edges
        - Cycle count delta
        - Structural coupling change
        """
        base_nodes: Set[str] = set(base_graph.nodes())
        target_nodes: Set[str] = set(target_graph.nodes())

        added_node_ids = target_nodes - base_nodes
        removed_node_ids = base_nodes - target_nodes

        added_nodes = [
            {
                "id": nid,
                "label": target_graph.nodes[nid].get("label", nid),
                "type": target_graph.nodes[nid].get("entity_type", "Unknown")
            }
            for nid in added_node_ids
        ]
        removed_nodes = [
            {
                "id": nid,
                "label": base_graph.nodes[nid].get("label", nid),
                "type": base_graph.nodes[nid].get("entity_type", "Unknown")
            }
            for nid in removed_node_ids
        ]

        # Edges comparison
        base_edges = {(u, v): d.get("edge_type") for u, v, d in base_graph.edges(data=True)}
        target_edges = {(u, v): d.get("edge_type") for u, v, d in target_graph.edges(data=True)}

        added_edges_keys = set(target_edges.keys()) - set(base_edges.keys())
        removed_edges_keys = set(base_edges.keys()) - set(target_edges.keys())

        added_deps = [
            {"source": u, "target": v, "type": target_edges[(u, v)]}
            for u, v in added_edges_keys
        ]
        removed_deps = [
            {"source": u, "target": v, "type": base_edges[(u, v)]}
            for u, v in removed_edges_keys
        ]

        # Cycles count delta
        base_cycles = len(list(nx.simple_cycles(base_graph))) if base_graph.number_of_nodes() < 200 else 0
        target_cycles = len(list(nx.simple_cycles(target_graph))) if target_graph.number_of_nodes() < 200 else 0
        cycle_delta = target_cycles - base_cycles

        # Coupling density: E / (V * (V - 1))
        def calc_density(g: nx.DiGraph) -> float:
            v = g.number_of_nodes()
            if v <= 1:
                return 0.0
            return round(g.number_of_edges() / (v * (v - 1)), 4)

        base_coupling = calc_density(base_graph)
        target_coupling = calc_density(target_graph)
        coupling_delta = round(target_coupling - base_coupling, 4)

        summary = (
            f"Comparing {base_commit[:8]} -> {target_commit[:8]}: "
            f"+{len(added_nodes)} nodes, -{len(removed_nodes)} nodes, "
            f"+{len(added_deps)} dependencies, -{len(removed_deps)} dependencies. "
            f"Cycles delta: {cycle_delta:+d}, Coupling delta: {coupling_delta:+f}."
        )

        return ArchitectureDiffResponse(
            base_commit=base_commit,
            target_commit=target_commit,
            added_nodes=added_nodes,
            removed_nodes=removed_nodes,
            modified_symbols=[],
            added_dependencies=added_deps,
            removed_dependencies=removed_deps,
            cycle_delta=cycle_delta,
            coupling_delta=coupling_delta,
            structural_summary=summary
        )
