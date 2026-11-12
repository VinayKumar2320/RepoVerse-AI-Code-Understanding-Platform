from typing import Dict, List, Any
import networkx as nx
from backend.app.schemas.architecture import ArchitectureAnalyticsResponse
from backend.app.core.logging import logger

class ArchitectureAnalyticsService:
    def compute_metrics(self, nx_graph: nx.DiGraph, snapshot_id: str) -> ArchitectureAnalyticsResponse:
        """
        Calculates verified graph metrics:
        - Fan-in (incoming edges)
        - Fan-out (outgoing edges)
        - Elementary dependency cycles (using simple_cycles or SCCs)
        - Strongly Connected Components (Tarjan's algorithm)
        - Degree & PageRank centrality
        - Martin's Instability Metric: I = Ce / (Ca + Ce)
        """
        # Focus on File / Module level nodes for architecture metrics
        module_subgraph = nx.DiGraph()
        for u, v, data in nx_graph.edges(data=True):
            if data.get("edge_type") in ("IMPORTS", "DEPENDS_ON"):
                u_data = nx_graph.nodes.get(u, {})
                v_data = nx_graph.nodes.get(v, {})
                module_subgraph.add_node(u, **u_data)
                module_subgraph.add_node(v, **v_data)
                module_subgraph.add_edge(u, v, **data)

        total_modules = module_subgraph.number_of_nodes()
        total_dependencies = module_subgraph.number_of_edges()

        # 1. Dependency Cycles
        cycles = []
        try:
            # nx.simple_cycles generator bounded to first 10 cycles for performance
            cycle_gen = nx.simple_cycles(module_subgraph)
            for i, c in enumerate(cycle_gen):
                if i >= 10:
                    break
                cycles.append(c)
        except Exception as e:
            logger.warning(f"Cycle detection error: {e}")

        # 2. Strongly Connected Components (components with size > 1 are cyclic subsystems)
        sccs = []
        try:
            for scc in nx.strongly_connected_components(module_subgraph):
                if len(scc) > 1:
                    sccs.append(list(scc))
        except Exception:
            pass

        # 3. Centrality (PageRank or In-degree)
        pagerank = {}
        if total_modules > 0:
            try:
                pagerank = nx.pagerank(module_subgraph, alpha=0.85, max_iter=100)
            except Exception:
                pagerank = {n: 1.0 / total_modules for n in module_subgraph.nodes()}

        sorted_central = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
        top_central = [
            {
                "node_id": nid,
                "label": module_subgraph.nodes[nid].get("label", nid),
                "centrality_score": round(score, 4),
                "entity_type": module_subgraph.nodes[nid].get("entity_type", "Module")
            }
            for nid, score in sorted_central
        ]

        # 4. Fan-In (Afferent Coupling Ca) and Fan-Out (Efferent Coupling Ce)
        fan_in_map = dict(module_subgraph.in_degree())
        fan_out_map = dict(module_subgraph.out_degree())

        fan_in_hotspots = [
            {
                "node_id": nid,
                "label": module_subgraph.nodes[nid].get("label", nid),
                "fan_in": count,
                "description": f"Imported by {count} other modules (high structural dependence)"
            }
            for nid, count in sorted(fan_in_map.items(), key=lambda x: x[1], reverse=True)[:5]
            if count > 0
        ]

        fan_out_hotspots = [
            {
                "node_id": nid,
                "label": module_subgraph.nodes[nid].get("label", nid),
                "fan_out": count,
                "description": f"Depends on {count} external/internal modules (high efferent coupling)"
            }
            for nid, count in sorted(fan_out_map.items(), key=lambda x: x[1], reverse=True)[:5]
            if count > 0
        ]

        # 5. Instability Metric: I = Ce / (Ca + Ce)
        # 0 = Completely stable (independent), 1 = Completely unstable (dependent)
        instability_scores = {}
        for nid in module_subgraph.nodes():
            ca = fan_in_map.get(nid, 0)
            ce = fan_out_map.get(nid, 0)
            denom = ca + ce
            instability = round(ce / denom, 2) if denom > 0 else 0.5
            label = module_subgraph.nodes[nid].get("label", nid)
            instability_scores[label] = instability

        # Verdict
        if cycles:
            verdict = f"Found {len(cycles)} cyclic module dependencies. Consider decoupling shared interfaces."
        elif sccs:
            verdict = f"Detected {len(sccs)} tightly coupled component cluster(s)."
        else:
            verdict = "Clean acyclic architectural layout. Strong structural separation observed."

        return ArchitectureAnalyticsResponse(
            snapshot_id=snapshot_id,
            total_modules=total_modules,
            total_dependencies=total_dependencies,
            dependency_cycles=cycles,
            strongly_connected_components=sccs,
            top_central_modules=top_central,
            fan_in_hotspots=fan_in_hotspots,
            fan_out_hotspots=fan_out_hotspots,
            instability_scores=instability_scores,
            summary_verdict=verdict
        )
