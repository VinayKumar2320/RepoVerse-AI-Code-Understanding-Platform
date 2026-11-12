from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ParsedImport:
    module: str
    names: List[str] # ["get", "post"] or ["*"] or class/func names
    alias: Optional[str] = None
    is_relative: bool = False
    level: int = 0
    line: int = 1

@dataclass
class ParsedCall:
    callee: str # "db.session.add", "render_template", "fetch"
    line: int
    context_symbol: Optional[str] = None # Symbol inside which the call occurred

@dataclass
class ParsedSymbol:
    name: str
    qualified_name: str
    kind: str # module, class, function, method, endpoint, interface
    start_line: int
    end_line: int
    docstring: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    bases: List[str] = field(default_factory=list) # Inherited classes
    calls: List[ParsedCall] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ParseResult:
    file_path: str
    language: str
    symbols: List[ParsedSymbol] = field(default_factory=list)
    imports: List[ParsedImport] = field(default_factory=list)
    calls: List[ParsedCall] = field(default_factory=list)
    syntax_error: Optional[str] = None
