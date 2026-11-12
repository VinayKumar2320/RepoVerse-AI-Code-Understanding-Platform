# Code Knowledge Graph Schema

The Code Knowledge Graph is a versioned, directed multi-level graph representing syntactic and static semantics of a repository commit.

## 1. Node Types
- `Repository`: Root repository entity.
- `Package`: Top-level package namespace.
- `Directory`: Physical folder on disk.
- `File`: Single source, test, or config file.
- `Module`: Logical executable or importable unit.
- `Class`: Class or struct definition.
- `Function`: Standalone function or procedure.
- `Method`: Member function of a class.
- `Endpoint`: Detected API route handler.
- `ExternalDependency`: Third-party library or package (e.g. `fastapi`, `react`, `sqlalchemy`).

## 2. Edge Types
- `CONTAINS`: Structural containment (e.g., Folder contains File, Class contains Method).
- `IMPORTS`: Direct module dependency import.
- `CALLS`: Method or function invocation.
- `INHERITS`: Class inheritance relationship.
- `DEFINES`: File defines class or function symbol.
- `DEPENDS_ON`: Module depends on external package.
- `TESTS`: Test file verifies source module.

## 3. Resolution Confidence
Edges maintain an explicit confidence classification:
- `directly_observed_syntax`: Unambiguously present in AST.
- `statically_resolved`: Resolved to a concrete file or symbol via static import resolution.
- `heuristically_inferred`: Discovered via naming conventions or fuzzy matches.
- `simulated`: Created dynamically during What-If architecture simulation.
