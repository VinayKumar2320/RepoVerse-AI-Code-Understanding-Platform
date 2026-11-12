import ast
from typing import List, Optional
from backend.app.services.parsing.symbol_types import (
    ParseResult, ParsedSymbol, ParsedImport, ParsedCall
)

class PythonASTParser:
    def parse_code(self, file_path: str, source_code: str) -> ParseResult:
        result = ParseResult(file_path=file_path, language="python")
        try:
            tree = ast.parse(source_code, filename=file_path)
        except SyntaxError as e:
            result.syntax_error = f"Syntax error at line {e.lineno}: {e.msg}"
            return result
        except Exception as e:
            result.syntax_error = str(e)
            return result

        # Extract module docstring
        module_doc = ast.get_docstring(tree)
        lines = source_code.splitlines()
        total_lines = len(lines)

        module_symbol = ParsedSymbol(
            name=file_path.split("/")[-1],
            qualified_name=file_path,
            kind="module",
            start_line=1,
            end_line=total_lines if total_lines > 0 else 1,
            docstring=module_doc,
        )
        result.symbols.append(module_symbol)

        # Traverse AST
        self._extract_symbols_and_relationships(tree, file_path, result)
        return result

    def _get_call_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._get_call_name(node.value)
            return f"{val}.{node.attr}" if val else node.attr
        return None

    def _extract_decorator_name(self, dec_node: ast.AST) -> str:
        if isinstance(dec_node, ast.Name):
            return dec_node.id
        elif isinstance(dec_node, ast.Attribute):
            val = self._get_call_name(dec_node.value)
            return f"{val}.{dec_node.attr}" if val else dec_node.attr
        elif isinstance(dec_node, ast.Call):
            return self._extract_decorator_name(dec_node.func)
        return ""

    def _extract_symbols_and_relationships(
        self,
        node: ast.AST,
        file_path: str,
        result: ParseResult,
        scope_prefix: str = ""
    ):
        for item in getattr(node, "body", []):
            # 1. Imports
            if isinstance(item, ast.Import):
                for alias in item.names:
                    result.imports.append(ParsedImport(
                        module=alias.name,
                        names=[alias.name],
                        alias=alias.asname,
                        is_relative=False,
                        line=item.lineno
                    ))
            elif isinstance(item, ast.ImportFrom):
                mod_name = item.module or ""
                names = [n.name for n in item.names]
                result.imports.append(ParsedImport(
                    module=mod_name,
                    names=names,
                    is_relative=item.level > 0,
                    level=item.level,
                    line=item.lineno
                ))

            # 2. Classes
            elif isinstance(item, ast.ClassDef):
                cls_name = item.name
                qname = f"{scope_prefix}{cls_name}" if scope_prefix else f"{file_path}::{cls_name}"
                doc = ast.get_docstring(item)
                decorators = [self._extract_decorator_name(d) for d in item.decorator_list if self._extract_decorator_name(d)]
                bases = []
                for b in item.bases:
                    name = self._get_call_name(b)
                    if name:
                        bases.append(name)

                cls_symbol = ParsedSymbol(
                    name=cls_name,
                    qualified_name=qname,
                    kind="class",
                    start_line=item.lineno,
                    end_line=getattr(item, "end_lineno", item.lineno),
                    docstring=doc,
                    decorators=decorators,
                    bases=bases,
                )
                result.symbols.append(cls_symbol)

                # Recursively parse class body (methods)
                self._extract_symbols_and_relationships(
                    item, file_path, result, scope_prefix=f"{qname}."
                )

            # 3. Functions & Methods
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fn_name = item.name
                qname = f"{scope_prefix}{fn_name}" if scope_prefix else f"{file_path}::{fn_name}"
                doc = ast.get_docstring(item)
                decorators = [self._extract_decorator_name(d) for d in item.decorator_list if self._extract_decorator_name(d)]
                params = [arg.arg for arg in item.args.args]

                kind = "method" if scope_prefix else "function"

                # Check if it's an API route endpoint (e.g., @app.get, @router.post, @blueprint.route)
                is_endpoint = any(
                    any(endpoint_kw in dec.lower() for endpoint_kw in ["route", "get", "post", "put", "delete", "patch"])
                    for dec in decorators
                )
                if is_endpoint:
                    kind = "endpoint"

                fn_calls: List[ParsedCall] = []
                # Extract calls inside this function
                for sub_node in ast.walk(item):
                    if isinstance(sub_node, ast.Call):
                        callee_name = self._get_call_name(sub_node.func)
                        if callee_name:
                            call = ParsedCall(
                                callee=callee_name,
                                line=sub_node.lineno,
                                context_symbol=qname
                            )
                            fn_calls.append(call)
                            result.calls.append(call)

                fn_symbol = ParsedSymbol(
                    name=fn_name,
                    qualified_name=qname,
                    kind=kind,
                    start_line=item.lineno,
                    end_line=getattr(item, "end_lineno", item.lineno),
                    docstring=doc,
                    parameters=params,
                    decorators=decorators,
                    calls=fn_calls,
                )
                result.symbols.append(fn_symbol)
