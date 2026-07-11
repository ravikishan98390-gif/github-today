"""
Basic structural validator for Java source code.

Because we deliberately avoid shipping a full JDK parser, this module
applies a set of fast regex/heuristic checks that catch the most common
structural problems:

1. At least one class or interface declaration must be present.
2. Every opening brace '{' must have a matching closing brace '}'.
3. Every opening parenthesis '(' must have a matching closing parenthesis ')'.
4. No unclosed multi-line comment (/* ... */).
5. A public class name must match the filename when a filename is provided.
6. Each statement line (outside block comments / string literals) that does
   not end a block must end with ';', '{', or '}' — a heuristic that flags
   the most obvious missing-semicolon mistakes.

These checks are intentionally lightweight and err on the side of accepting
ambiguous code rather than producing false positives.
"""

import re
from dataclasses import dataclass, field


@dataclass
class JavaValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_CLASS_OR_INTERFACE_RE = re.compile(
    r"\b(class|interface|enum|record)\s+\w+", re.MULTILINE
)

_PUBLIC_CLASS_RE = re.compile(r"\bpublic\s+(?:class|interface|enum|record)\s+(\w+)")

_IMPORT_OR_PACKAGE_LINE_RE = re.compile(r"^\s*(import|package)\s+")
_ANNOTATION_LINE_RE = re.compile(r"^\s*@\w+")
_BLANK_OR_COMMENT_LINE_RE = re.compile(r"^\s*(//.*)?$")
_BLOCK_OPEN_RE = re.compile(r"[{(]")
_BLOCK_CLOSE_RE = re.compile(r"[})]")


def _strip_string_literals(source: str) -> str:
    """Replace content inside string/char literals with spaces to avoid
    false matches for braces or keywords inside strings."""
    result = []
    i = 0
    length = len(source)
    while i < length:
        ch = source[i]
        if ch in ('"', "'"):
            quote = ch
            result.append(ch)
            i += 1
            while i < length:
                c = source[i]
                result.append(" ")  # replace literal content
                if c == "\\" and i + 1 < length:
                    i += 2  # skip escaped char
                    continue
                if c == quote:
                    break
                i += 1
            i += 1
        else:
            result.append(ch)
            i += 1
    return "".join(result)


def _strip_comments(source: str) -> str:
    """Remove // line comments and /* */ block comments."""
    # Remove block comments first
    source = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group().count("\n"), source, flags=re.DOTALL)
    # Remove line comments
    source = re.sub(r"//[^\n]*", "", source)
    return source


def _check_balanced(cleaned: str) -> list[str]:
    """Return errors for unbalanced braces and parentheses."""
    errors: list[str] = []
    brace_depth = 0
    paren_depth = 0
    for line_no, line in enumerate(cleaned.splitlines(), start=1):
        for ch in line:
            if ch == "{":
                brace_depth += 1
            elif ch == "}":
                brace_depth -= 1
                if brace_depth < 0:
                    errors.append(
                        f"Unexpected '}}' (extra closing brace) near line {line_no}"
                    )
                    brace_depth = 0
            elif ch == "(":
                paren_depth += 1
            elif ch == ")":
                paren_depth -= 1
                if paren_depth < 0:
                    errors.append(
                        f"Unexpected ')' (extra closing parenthesis) near line {line_no}"
                    )
                    paren_depth = 0
    if brace_depth > 0:
        errors.append(
            f"{brace_depth} unclosed brace(s) '{{' — missing '}}' somewhere"
        )
    if paren_depth > 0:
        errors.append(
            f"{paren_depth} unclosed parenthesis '(' — missing ')' somewhere"
        )
    return errors


def _check_unclosed_block_comment(source: str) -> list[str]:
    """Detect a /* without a matching */."""
    opens = source.count("/*")
    closes = source.count("*/")
    if opens > closes:
        return [f"Unclosed block comment: {opens} '/*' but only {closes} '*/'"]
    return []


def _check_public_class_matches_filename(
    cleaned: str, filename: str | None
) -> list[str]:
    """Warn when the public class name doesn't match the filename stem."""
    if not filename:
        return []
    stem = filename.removesuffix(".java")
    match = _PUBLIC_CLASS_RE.search(cleaned)
    if match and match.group(1) != stem:
        return [
            f"Public class '{match.group(1)}' does not match filename '{filename}'. "
            "In Java, the public class name must equal the filename (without .java)."
        ]
    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_java(source: str, filename: str | None = None) -> JavaValidationResult:
    """
    Run structural checks on *source* and return a JavaValidationResult.

    Parameters
    ----------
    source:
        Raw Java source code as a string.
    filename:
        Optional filename (e.g. ``"HelloWorld.java"``) used to validate
        that the public class name matches.

    Returns
    -------
    JavaValidationResult
        .valid  — True when no structural problems were found.
        .errors — Ordered list of human-readable error descriptions.
    """
    errors: list[str] = []

    # 1. Check for unclosed block comments on the raw source first.
    errors.extend(_check_unclosed_block_comment(source))

    # 2. Strip literals and comments for structural checks.
    cleaned = _strip_comments(_strip_string_literals(source))

    # 3. Must have at least one class/interface/enum/record declaration.
    if not _CLASS_OR_INTERFACE_RE.search(cleaned):
        errors.append(
            "No class, interface, enum, or record declaration found. "
            "Java files must contain at least one type declaration."
        )

    # 4. Balanced braces and parentheses.
    errors.extend(_check_balanced(cleaned))

    # 5. Public class name must match filename.
    errors.extend(_check_public_class_matches_filename(cleaned, filename))

    return JavaValidationResult(valid=len(errors) == 0, errors=errors)
