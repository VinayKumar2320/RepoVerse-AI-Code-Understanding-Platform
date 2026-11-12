from pathlib import Path
from typing import Optional, List, Dict
from backend.app.services.parsing.symbol_types import ParseResult, ParsedSymbol
from backend.app.services.parsing.python_parser import PythonASTParser
from backend.app.services.parsing.treesitter_parser import TreeSitterParser
from backend.app.core.logging import logger

class ParserService:
    def __init__(self):
        self.py_parser = PythonASTParser()
        self.ts_parser = TreeSitterParser()

    def parse_file(self, file_path: str, absolute_path: Path, language: str) -> ParseResult:
        try:
            with open(absolute_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            return ParseResult(
                file_path=file_path,
                language=language,
                syntax_error=f"Could not read file: {e}"
            )

        if language == "python":
            return self.py_parser.parse_code(file_path, content)
        elif language in ("typescript", "javascript"):
            return self.ts_parser.parse_code(file_path, content, language)
        else:
            # Generic fallback: creates a module symbol and counts lines
            lines = content.splitlines()
            res = ParseResult(file_path=file_path, language=language)
            res.symbols.append(ParsedSymbol(
                name=file_path.split("/")[-1],
                qualified_name=file_path,
                kind="file",
                start_line=1,
                end_line=len(lines) if lines else 1,
            ))
            return res
