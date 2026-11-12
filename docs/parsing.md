# Multi-Language Parsing & Symbol Extraction

RepoVerse employs a dual-engine parsing pipeline:

## 1. Python Native AST (`backend/app/services/parsing/python_parser.py`)
- Leverages Python's native `ast` library.
- Extracts:
  - Top-level and nested classes with inheritance hierarchies (`bases`).
  - Top-level and nested functions, async functions, and class methods.
  - Decorator extraction (including endpoint identification `@app.get`, `@router.post`).
  - Module-level and member-level docstrings.
  - Call hierarchy parsing (`ast.Call` nodes) linking caller to callee.
  - Imports: `import x`, `import x as y`, `from . import z`, `from ...x import y`.

## 2. Tree-sitter Multi-Language Grammars (`backend/app/services/parsing/treesitter_parser.py`)
- Employs official native Tree-sitter grammars:
  - `tree-sitter-typescript` & `tree-sitter-typescript.language_tsx()`
  - `tree-sitter-javascript`
  - `tree-sitter-python`
- Extracts:
  - Interface declarations (`interface UserProfile { ... }`).
  - Class declarations and method definitions (`method_definition`).
  - Arrow functions and lexical declarations (`const handler = () => { ... }`).
  - ES6 Import statements (`import { x } from './utils'`).
  - Function invocations (`call_expression`).

## 3. Provenance & Stable Node Identifiers
Every extracted symbol receives a deterministic qualified name:
- Module: `app/main.py`
- Class: `app/models/user.py::User`
- Method: `app/models/user.py::User.save`
- Function: `app/services/auth.py::authenticate`
- Endpoint: `app/api/v1/routes.py::get_users`
