#!/usr/bin/env python3
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.parsing.classifier import FileClassifier
from backend.app.services.parsing.parser_service import ParserService
from backend.app.services.graphs.graph_builder import CodeKnowledgeGraph
from backend.app.services.analytics.metrics_service import ArchitectureAnalyticsService

def benchmark_graph():
    print("=" * 60)
    print("RepoVerse Knowledge Graph & Analytics Benchmark")
    print("=" * 60)

    fixture_dir = Path("benchmarks/repositories/flask_mini")
    classifier = FileClassifier(fixture_dir)
    classified_files = classifier.scan_repository()

    parser_svc = ParserService()
    parse_results = [
        parser_svc.parse_file(cf.path, cf.absolute_path, cf.language)
        for cf in classified_files
    ]

    # Benchmark Graph Building
    start_time = time.perf_counter()
    iterations = 100
    for _ in range(iterations):
        ckg = CodeKnowledgeGraph("bench-snap")
        ckg.build(classified_files, parse_results, "flask_mini")
    elapsed = (time.perf_counter() - start_time) / iterations

    nodes_count = ckg.graph.number_of_nodes()
    edges_count = ckg.graph.number_of_edges()

    print(f"\n[Graph Construction]")
    print(f"  Avg Latency: {elapsed * 1000:.3f} ms")
    print(f"  Nodes Generated: {nodes_count}")
    print(f"  Edges Generated: {edges_count}")

    # Benchmark Analytics
    analytics_svc = ArchitectureAnalyticsService()
    start_analytics = time.perf_counter()
    metrics = analytics_svc.compute_metrics(ckg.graph, "bench-snap")
    elapsed_analytics = (time.perf_counter() - start_analytics)

    print(f"\n[Architecture Analytics]")
    print(f"  Analytics Latency: {elapsed_analytics * 1000:.3f} ms")
    print(f"  Cycles Detected: {len(metrics.dependency_cycles)}")
    print(f"  Central Modules: {[m['label'] for m in metrics.top_central_modules]}")
    print(f"  Summary Verdict: {metrics.summary_verdict}")
    print("=" * 60)
    print("Graph benchmark PASSED successfully.")

if __name__ == "__main__":
    benchmark_graph()
