"""
Python syntax validator using the built-in `ast` module.

Attempts to parse the source code string into an AST. If parsing
succeeds, the code is syntactically valid Python. Any SyntaxError or
ValueError raised by ast.parse is caught and surfaced as a structured
error list.
"""

import ast
from dataclasses import dataclass, field


@dataclass
class PythonValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


def validate_python(source: str) -> PythonValidationResult:
    """
    Parse *source* with ast.parse and return a PythonValidationResult.

    Parameters
    ----------
    source:
        Raw Python source code as a string.

    Returns
    -------
    PythonValidationResult
        .valid  — True when the source is syntactically correct.
        .errors — List of human-readable error messages (empty on success).
    """
    try:
        ast.parse(source)
        return PythonValidationResult(valid=True)
    except SyntaxError as exc:
        # Build a detailed message that mirrors what the interpreter shows.
        detail = f"SyntaxError at line {exc.lineno}, col {exc.offset}: {exc.msg}"
        if exc.text:
            detail += f"\n    {exc.text.rstrip()}"
            if exc.offset:
                detail += "\n    " + " " * (exc.offset - 1) + "^"
        return PythonValidationResult(valid=False, errors=[detail])
    except ValueError as exc:
        # ast.parse raises ValueError for source with null bytes, etc.
        return PythonValidationResult(
            valid=False, errors=[f"ValueError during parsing: {exc}"]
        )
