import io
import json
import keyword
import re
import zipfile
from dataclasses import asdict

from .models import Requirement


def safe_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value).strip("_").lower()
    if not value or value[0].isdigit() or keyword.iskeyword(value):
        value = f"case_{value}"
    return value[:70]


def _criteria_comments(requirement: Requirement) -> list[str]:
    criteria = requirement.acceptance_criteria or [
        "No acceptance criteria supplied; review this test before use."
    ]
    return [
        f"# AC{index}: {criterion}"
        for index, criterion in enumerate(criteria, 1)
    ]


def generate_api_test(requirement: Requirement) -> str:
    name = safe_name(f"{requirement.key}_{requirement.title}")
    path = requirement.metadata.get("api_path", requirement.metadata.get("path", f"/requirements/{requirement.key}"))
    status = int(requirement.metadata.get("expected_status", 200))
    joined = " ".join(requirement.acceptance_criteria).lower()
    fields = [
        field
        for field in ("id", "title", "price", "name", "email", "status")
        if re.search(rf"\b{field}\b", joined)
    ]

    lines = [
        "import os",
        "import requests",
        "",
        *_criteria_comments(requirement),
        f"def test_{name}():",
        '    base_url = os.getenv("TARGET_API_URL", "https://dummyjson.com").rstrip("/")',
        f"    response = requests.get(f\"{{base_url}}{path}\", timeout=15)",
        f"    assert response.status_code == {status}, response.text[:500]",
        '    assert "application/json" in response.headers.get("content-type", "")',
        "    payload = response.json()",
    ]
    if fields:
        lines.extend(f"    assert {field!r} in payload" for field in fields)
    else:
        lines.append("    assert payload is not None")
    return "\n".join(lines) + "\n"


def generate_ui_test(requirement: Requirement) -> str:
    name = safe_name(f"{requirement.key}_{requirement.title}")
    path = requirement.metadata.get("ui_path", requirement.metadata.get("path", "/"))
    lines = [
        "import os",
        "import pytest",
        "",
        "pytestmark = pytest.mark.ui",
        "",
        *_criteria_comments(requirement),
        f"def test_{name}(page):",
        '    base_url = os.getenv("TARGET_WEB_URL")',
        "    if not base_url:",
        '        pytest.skip("Set TARGET_WEB_URL after reviewing selectors and test steps")',
        f"    page.goto(f\"{{base_url.rstrip('/')}}{path}\")",
        f"    expect_text = {requirement.title!r}",
        '    assert page.locator("body").is_visible()',
        "    # Replace this broad assertion with a stable product selector after review.",
        '    assert expect_text.lower() in page.locator("body").inner_text().lower()',
    ]
    return "\n".join(lines) + "\n"


def generate_project(requirements: list[Requirement], kinds: list[str]) -> dict[str, str]:
    files: dict[str, str] = {}
    for requirement in requirements:
        base = safe_name(f"{requirement.key}_{requirement.title}")
        if "API" in kinds:
            files[f"tests/test_api_{base}.py"] = generate_api_test(requirement)
        if "Web UI" in kinds:
            files[f"tests/test_ui_{base}.py"] = generate_ui_test(requirement)

    files["requirements.txt"] = "pytest\nrequests\nplaywright\npytest-playwright\n"
    files["pytest.ini"] = (
        "[pytest]\n"
        "markers =\n"
        "    ui: browser-based test\n"
        "addopts = -ra\n"
    )
    files["README.md"] = (
        "# Generated automation tests\n\n"
        "Review generated selectors, paths, expected values, and credentials before use.\n\n"
        "## Run API tests\n"
        "`TARGET_API_URL=https://your-api.example pytest -m \"not ui\" -v`\n\n"
        "## Run browser tests\n"
        "Install browsers with `playwright install chromium`, then run:\n"
        "`TARGET_WEB_URL=https://your-app.example pytest -m ui -v`\n\n"
        "Generated tests are a reviewed starting point, not a replacement for QA judgment.\n"
    )
    files["requirements.json"] = json.dumps(
        [asdict(item) for item in requirements], indent=2
    )
    return files


def project_zip(files: dict[str, str]) -> bytes:
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w", zipfile.ZIP_DEFLATED) as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return memory.getvalue()
