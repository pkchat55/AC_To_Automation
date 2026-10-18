import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path


BLOCKED_CALLS = {"eval", "exec", "compile", "__import__"}
BLOCKED_MODULES = {"subprocess", "socket", "shutil", "ctypes", "multiprocessing"}


def validate_test_code(code: str) -> list[str]:
    issues = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"Syntax error on line {exc.lineno}: {exc.msg}"]
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name.split(".")[0] for alias in node.names] if isinstance(node, ast.Import) else [(node.module or "").split(".")[0]]
            for name in names:
                if name in BLOCKED_MODULES:
                    issues.append(f"Blocked import: {name}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
            issues.append(f"Blocked call: {node.func.id}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in {"system", "popen", "unlink", "rmtree"}:
                issues.append(f"Blocked operation: {node.func.attr}")
    return sorted(set(issues))


def run_demo_api_tests(files: dict[str, str], timeout: int = 40) -> tuple[int, str]:
    selected = {name: code for name, code in files.items() if name.startswith("tests/test_api_")}
    if not selected:
        return 0, "No API tests were generated."
    issues = [f"{name}: {issue}" for name, code in selected.items() for issue in validate_test_code(code)]
    if issues:
        return 2, "Safety validation failed:\n" + "\n".join(issues)
    with tempfile.TemporaryDirectory(prefix="reqauto_") as directory:
        root = Path(directory)
        for name, code in selected.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(code, encoding="utf-8")
        env = {"PATH": os.environ.get("PATH", ""), "TARGET_API_URL": "https://dummyjson.com", "PYTHONPATH": ""}
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-m", "not ui"],
                cwd=root,
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout,
            )
            return result.returncode, (result.stdout + "\n" + result.stderr).strip()
        except subprocess.TimeoutExpired:
            return 124, f"Test run stopped after {timeout} seconds."
