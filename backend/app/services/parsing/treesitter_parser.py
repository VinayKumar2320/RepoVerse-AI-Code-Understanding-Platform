from typing import List, Optional
import tree_sitter
import tree_sitter_javascript
import tree_sitter_typescript

from backend.app.services.parsing.symbol_types import (
    ParseResult, ParsedSymbol, ParsedImport, ParsedCall
)

class TreeSitterParser:
    def __init__(self):
        self.js_lang = tree_sitter.Language(tree_sitter_javascript.language())
        self.ts_lang = tree_sitter.Language(tree_sitter_typescript.language_typescript())
        self.tsx_lang = tree_sitter.Language(tree_sitter_typescript.language_tsx())
        self.js_parser = tree_sitter.Parser(self.js_lang)
        self.ts_parser = tree_sitter.Parser(self.ts_lang)
        self.tsx_parser = tree_sitter.Parser(self.tsx_lang)

    def parse_code(self, file_path: str, source_code: str, language: str) -> ParseResult:
        result = ParseResult(file_path=file_path, language=language)
        code_bytes = source_code.encode("utf-8", errors="ignore")

        if language == "typescript":
            parser = self.tsx_parser if file_path.endswith(".tsx") else self.ts_parser
        else:
            parser = self.js_parser

        try:
            tree = parser.parse(code_bytes)
        except Exception as e:
            result.syntax_error = str(e)
            return result

        lines = source_code.splitlines()
        total_lines = len(lines)

        module_symbol = ParsedSymbol(
            name=file_path.split("/")[-1],
            qualified_name=file_path,
            kind="module",
            start_line=1,
            end_line=total_lines if total_lines > 0 else 1,
        )
        result.symbols.append(module_symbol)

        self._walk_node(tree.root_node, code_bytes, file_path, result)
        return result

    def _get_node_text(self, node: tree_sitter.Node, code_bytes: bytes) -> str:
        return code_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="ignore")

    def _walk_node(
        self,
        node: tree_sitter.Node,
        code_bytes: bytes,
        file_path: str,
        result: ParseResult,
        scope_prefix: str = ""
    ):
        for child in node.children:
            # 1. Imports: import { a, b } from 'mod'
            if child.type == "import_statement":
                raw_text = self._get_node_text(child, code_bytes)
                # Extract source string (e.g. 'react' or './utils')
                source_node = child.child_by_field_name("source")
                mod_name = ""
                if source_node:
                    mod_name = self._get_node_text(source_node, code_bytes).strip("'\"")
                
                result.imports.append(ParsedImport(
                    module=mod_name or raw_text,
                    names=[raw_text],
                    is_relative=mod_name.startswith("."),
                    line=child.start_point.row + 1
                ))

            # 2. Export wrapping declaration
            elif child.type == "export_statement":
                for sub in child.children:
                    if sub.type in ("function_declaration", "class_declaration", "interface_declaration", "lexical_declaration"):
                        self._process_declaration(sub, code_bytes, file_path, result, scope_prefix)

            # 3. Direct declarations
            elif child.type in ("function_declaration", "class_declaration", "interface_declaration", "lexical_declaration"):
                self._process_declaration(child, code_bytes, file_path, result, scope_prefix)

            # 4. Method definition inside class body
            elif child.type == "method_definition":
                name_node = child.child_by_field_name("name")
                name = self._get_node_text(name_node, code_bytes) if name_node else "anonymous"
                qname = f"{scope_prefix}{name}" if scope_prefix else f"{file_path}::{name}"
                
                sym = ParsedSymbol(
                    name=name,
                    qualified_name=qname,
                    kind="method",
                    start_line=child.start_point.row + 1,
                    end_line=child.end_point.row + 1,
                )
                result.symbols.append(sym)

            # 5. Call expressions
            elif child.type == "call_expression":
                func_node = child.child_by_field_name("function")
                if func_node:
                    callee_text = self._get_node_text(func_node, code_bytes)
                    result.calls.append(ParsedCall(
                        callee=callee_text,
                        line=child.start_point.row + 1,
                        context_symbol=scope_prefix.rstrip(".") or file_path
                    ))

            # Recurse
            if child.type not in ("function_declaration", "class_declaration", "interface_declaration"):
                self._walk_node(child, code_bytes, file_path, result, scope_prefix)

    def _process_declaration(
        self,
        node: tree_sitter.Node,
        code_bytes: bytes,
        file_path: str,
        result: ParseResult,
        scope_prefix: str
    ):
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            name = self._get_node_text(name_node, code_bytes) if name_node else "anonymous"
            qname = f"{scope_prefix}{name}" if scope_prefix else f"{file_path}::{name}"

            sym = ParsedSymbol(
                name=name,
                qualified_name=qname,
                kind="function",
                start_line=node.start_point.row + 1,
                end_line=node.end_point.row + 1,
            )
            result.symbols.append(sym)

            body_node = node.child_by_field_name("body")
            if body_node:
                self._walk_node(body_node, code_bytes, file_path, result, scope_prefix=f"{qname}.")

        elif node.type == "class_declaration":
            name_node = node.child_by_field_name("name")
            name = self._get_node_text(name_node, code_bytes) if name_node else "AnonymousClass"
            qname = f"{scope_prefix}{name}" if scope_prefix else f"{file_path}::{name}"

            sym = ParsedSymbol(
                name=name,
                qualified_name=qname,
                kind="class",
                start_line=node.start_point.row + 1,
                end_line=node.end_point.row + 1,
            )
            result.symbols.append(sym)

            body_node = node.child_by_field_name("body")
            if body_node:
                self._walk_node(body_node, code_bytes, file_path, result, scope_prefix=f"{qname}.")

        elif node.type == "interface_declaration":
            name_node = node.child_by_field_name("name")
            name = self._get_node_text(name_node, code_bytes) if name_node else "Interface"
            qname = f"{scope_prefix}{name}" if scope_prefix else f"{file_path}::{name}"

            sym = ParsedSymbol(
                name=name,
                qualified_name=qname,
                kind="interface",
                start_line=node.start_point.row + 1,
                end_line=node.end_point.row + 1,
            )
            result.symbols.append(sym)

        elif node.type == "lexical_declaration":
            # const fn = () => { ... }
            text = self._get_node_text(node, code_bytes)
            if "=>" in text or "function" in text:
                declarator = next((c for c in node.children if c.type == "variable_declarator"), None)
                if declarator:
                    name_node = declarator.child_by_field_name("name")
                    if name_node:
                        name = self._get_node_text(name_node, code_bytes)
                        qname = f"{scope_prefix}{name}" if scope_prefix else f"{file_path}::{name}"
                        sym = ParsedSymbol(
                            name=name,
                            qualified_name=qname,
                            kind="function",
                            start_line=node.start_point.row + 1,
                            end_line=node.end_point.row + 1,
                        )
                        result.symbols.append(sym)
