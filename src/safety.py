"""Safety checks for generated local Python files."""

import ast
import re
from pathlib import Path

ALLOWED_GENERATED_FILES = {
    "generated_game.py",
    "generated_tests.py",
    "generated_streamlit_helpers.py",
}

DANGEROUS_PATTERNS = [
    r"os\.system",
    r"subprocess",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__",
    r"socket",
    r"requests",
    r"urllib\.request",
    r"http://",
    r"https://",
    r"open\s*\(",
    r"Path\s*\(",
]


def validate_generated_path(project_root, target):
    root = Path(project_root).resolve()
    path = Path(target)
    if path.is_absolute() or ".." in path.parts or "~" in str(path) or re.match(r"^[A-Za-z]:", str(path)):
        raise ValueError("Generated path is not allowed.")
    full = (root / path).resolve()
    allowed_dir = (root / "generated_code").resolve()
    if full.parent != allowed_dir or full.name not in ALLOWED_GENERATED_FILES:
        raise ValueError("Generated files must stay inside generated_code with approved names.")
    return full


def scan_code(code):
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, code):
            return False, f"Blocked dangerous pattern: {pattern}"
    try:
        ast.parse(code)
    except SyntaxError as exc:
        return False, f"Syntax error: {exc}"
    return True, "Safety scan passed."


def safe_write(project_root, relative_path, code):
    ok, message = scan_code(code)
    if not ok:
        raise ValueError(message)
    path = validate_generated_path(project_root, relative_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")
    return path

