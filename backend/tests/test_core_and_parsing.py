import pytest
from pathlib import Path
from backend.app.core.security import validate_github_url, SecurityValidationError, sanitize_path
from backend.app.services.parsing.python_parser import PythonASTParser
from backend.app.services.parsing.treesitter_parser import TreeSitterParser
from backend.app.services.parsing.classifier import FileClassifier
from backend.app.services.graphs.graph_builder import CodeKnowledgeGraph
from backend.app.services.analytics.metrics_service import ArchitectureAnalyticsService
from backend.app.services.simulation.simulator import ArchitectureSimulator
from backend.app.schemas.architecture import SimulationRequest, SimulationMutation

def test_url_validation_valid():
    url, owner, repo = validate_github_url("https://github.com/pallets/flask")
    assert url == "https://github.com/pallets/flask"
    assert owner == "pallets"
    assert repo == "flask"

    url2, owner2, repo2 = validate_github_url("fastapi/fastapi")
    assert url2 == "https://github.com/fastapi/fastapi"
    assert owner2 == "fastapi"
    assert repo2 == "fastapi"

def test_url_validation_ssrf_and_invalid():
    with pytest.raises(SecurityValidationError):
        validate_github_url("http://localhost:8000/evil")
    with pytest.raises(SecurityValidationError):
        validate_github_url("https://evil-site.com/foo/bar")
    with pytest.raises(SecurityValidationError):
        validate_github_url("https://github.com/../escaped")

def test_path_sanitization():
    assert sanitize_path("../../etc/passwd") == "etc/passwd"
    assert sanitize_path("foo/./bar/../baz") == "foo/baz"

def test_python_ast_parser():
    code = """
import os
from math import sqrt

class Calculator:
    '''Simple calculator engine.'''
    def __init__(self, val: float):
        self.val = val

    def compute(self, x: float) -> float:
        res = sqrt(x)
        return self.val + res

def add(a: int, b: int) -> int:
    return a + b
"""
    parser = PythonASTParser()
    res = parser.parse_code("calc.py", code)
    assert res.syntax_error is None
    symbols_by_name = {s.name: s for s in res.symbols}
    assert "Calculator" in symbols_by_name
    assert symbols_by_name["Calculator"].kind == "class"
    assert "compute" in symbols_by_name
    assert symbols_by_name["compute"].kind == "method"
    assert "add" in symbols_by_name
    assert symbols_by_name["add"].kind == "function"
    assert len(res.imports) == 2

def test_treesitter_typescript_parser():
    ts_code = """
import { useState } from 'react';

export interface User {
    id: string;
    name: string;
}

export class UserService {
    async fetchUser(id: string) {
        return { id, name: 'Alice' };
    }
}

export function formatName(user: User): string {
    return user.name.toUpperCase();
}
"""
    parser = TreeSitterParser()
    res = parser.parse_code("user.ts", ts_code, "typescript")
    assert res.syntax_error is None
    names = {s.name for s in res.symbols}
    assert "UserService" in names
    assert "fetchUser" in names
    assert "formatName" in names
    assert "User" in names

def test_graph_and_metrics_and_simulation():
    py_code_a = """
from b import helper_b

def do_a():
    return helper_b()
"""
    py_code_b = """
from a import do_a

def helper_b():
    return do_a()
"""
    py_parser = PythonASTParser()
    res_a = py_parser.parse_code("a.py", py_code_a)
    res_b = py_parser.parse_code("b.py", py_code_b)

    from backend.app.services.parsing.classifier import ClassifiedFile
    cf_a = ClassifiedFile("a.py", Path("/tmp/a.py"), "python", "source", 5, 100)
    cf_b = ClassifiedFile("b.py", Path("/tmp/b.py"), "python", "source", 5, 100)

    ckg = CodeKnowledgeGraph("snap-1")
    ckg.build([cf_a, cf_b], [res_a, res_b], "test_repo")

    # Metrics
    analytics_svc = ArchitectureAnalyticsService()
    metrics = analytics_svc.compute_metrics(ckg.graph, "snap-1")
    # Verify cyclic dependency detected between a.py and b.py
    assert len(metrics.dependency_cycles) > 0

    # Simulation: remove the dependency edge from b.py to a.py
    sim = ArchitectureSimulator()
    req = SimulationRequest(mutations=[
        SimulationMutation(
            action="remove_dependency",
            source_node="file::b.py",
            target_node="file::a.py"
        )
    ])
    sim_res = sim.simulate_mutations(ckg.graph, "snap-1", req)
    assert sim_res.simulated_cycles_count < sim_res.original_cycles_count
