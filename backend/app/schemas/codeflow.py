from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CodeFlowNode(BaseModel):
    id: str
    symbol_name: str
    qualified_name: str
    kind: str # endpoint, function, method, service, db
    file_path: str
    start_line: int
    end_line: int
    snippet: Optional[str] = None
    step_order: int
    confidence: str = "statically_resolved" # observed_syntax, statically_resolved, inferred

class CodeFlowTraceResponse(BaseModel):
    entry_point_id: str
    entry_symbol: str
    entry_file: str
    nodes: List[CodeFlowNode]
    call_edges: List[Dict[str, Any]]
    narrative: str
