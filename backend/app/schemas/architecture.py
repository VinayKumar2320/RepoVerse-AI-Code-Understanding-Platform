from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class GraphNodeSchema(BaseModel):
    id: str
    entity_type: str # Package, Directory, File, Module, Class, Function, Endpoint
    label: str
    qualified_name: str
    file_path: Optional[str] = None
    level: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphEdgeSchema(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str # CONTAINS, IMPORTS, CALLS, INHERITS, DEFINES, TESTS
    evidence: Optional[str] = None
    confidence: str = "statically_resolved"
    source_line: Optional[int] = None

class ArchitectureGraphResponse(BaseModel):
    snapshot_id: str
    level: int
    nodes: List[GraphNodeSchema]
    edges: List[GraphEdgeSchema]
    total_nodes: int
    total_edges: int

class ArchitectureAnalyticsResponse(BaseModel):
    snapshot_id: str
    total_modules: int
    total_dependencies: int
    dependency_cycles: List[List[str]]
    strongly_connected_components: List[List[str]]
    top_central_modules: List[Dict[str, Any]]
    fan_in_hotspots: List[Dict[str, Any]]
    fan_out_hotspots: List[Dict[str, Any]]
    instability_scores: Dict[str, float]
    summary_verdict: str

class SimulationMutation(BaseModel):
    action: str # "remove_dependency", "add_dependency", "move_module", "split_package"
    source_node: str
    target_node: Optional[str] = None
    new_package: Optional[str] = None

class SimulationRequest(BaseModel):
    mutations: List[SimulationMutation]

class SimulationResponse(BaseModel):
    snapshot_id: str
    original_cycles_count: int
    simulated_cycles_count: int
    original_coupling: float
    simulated_coupling: float
    impact_summary: str
    affected_nodes: List[str]
    cycle_changes: Dict[str, Any]
