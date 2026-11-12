from typing import List, Dict, Any
import copy
import networkx as nx

from backend.app.schemas.architecture import SimulationRequest, SimulationResponse

class ArchitectureSimulator:
    def simulate_mutations(
        self,
        base_graph: nx.DiGraph,
        snapshot_id: str,
        request: SimulationRequest
    ) -> SimulationResponse:
        """
        Runs speculative what-if structural modifications on an in-memory deep copy of the graph.
        Never mutates the underlying repository or stored snapshot.
        """
        # Deep copy ensures complete isolation
        sim_graph = copy.deepcopy(base_graph)

        def count_cycles(g: nx.DiGraph) -> int:
            try:
                # Count simple cycles bounded to small traversal
                count = 0
                for _ in nx.simple_cycles(g):
                    count += 1
                    if count >= 50:
                        break
                return count
            except Exception:
                return 0

        def calc_density(g: nx.DiGraph) -> float:
            v = g.number_of_nodes()
            if v <= 1:
                return 0.0
            return round(g.number_of_edges() / (v * (v - 1)), 4)

        orig_cycles = count_cycles(base_graph)
        orig_coupling = calc_density(base_graph)

        affected_nodes = []
        for mut in request.mutations:
            src = mut.source_node
            tgt = mut.target_node

            if mut.action == "remove_dependency":
                if tgt and sim_graph.has_edge(src, tgt):
                    sim_graph.remove_edge(src, tgt)
                    affected_nodes.extend([src, tgt])
                elif not tgt:
                    # Remove all outgoing edges from source
                    out_edges = list(sim_graph.out_edges(src))
                    for u, v in out_edges:
                        sim_graph.remove_edge(u, v)
                    affected_nodes.append(src)

            elif mut.action == "add_dependency":
                if tgt:
                    sim_graph.add_edge(src, tgt, edge_type="DEPENDS_ON", confidence="simulated")
                    affected_nodes.extend([src, tgt])

            elif mut.action == "move_module":
                if src in sim_graph:
                    sim_graph.nodes[src]["metadata"]["simulated_package"] = mut.new_package or "refactored"
                    affected_nodes.append(src)

            elif mut.action == "split_package":
                affected_nodes.append(src)

        sim_cycles = count_cycles(sim_graph)
        sim_coupling = calc_density(sim_graph)

        impact_summary = (
            f"Simulated {len(request.mutations)} architectural mutation(s). "
            f"Cycles went from {orig_cycles} to {sim_cycles} "
            f"({sim_cycles - orig_cycles:+d}). Structural coupling density shifted from "
            f"{orig_coupling:.4f} to {sim_coupling:.4f}."
        )

        return SimulationResponse(
            snapshot_id=snapshot_id,
            original_cycles_count=orig_cycles,
            simulated_cycles_count=sim_cycles,
            original_coupling=orig_coupling,
            simulated_coupling=sim_coupling,
            impact_summary=impact_summary,
            affected_nodes=list(set(affected_nodes)),
            cycle_changes={
                "before": orig_cycles,
                "after": sim_cycles,
                "cycles_eliminated": max(0, orig_cycles - sim_cycles)
            }
        )
