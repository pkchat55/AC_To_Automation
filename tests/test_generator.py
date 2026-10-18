import ast
import zipfile
from io import BytesIO

from reqauto.demo import demo_requirements
from reqauto.generator import generate_project, project_zip, safe_name
from reqauto.runner import validate_test_code


def test_safe_name_is_valid_identifier():
    assert safe_name("123 Login / user!").isidentifier()


def test_generates_api_and_ui_tests():
    files = generate_project(demo_requirements(), ["API", "Web UI"])
    tests = {name: code for name, code in files.items() if name.endswith(".py")}
    assert len(tests) == 4
    for code in tests.values():
        ast.parse(code)
        assert validate_test_code(code) == []
    assert "requirements.json" in files


def test_zip_contains_project_files():
    files = generate_project(demo_requirements()[:1], ["API"])
    with zipfile.ZipFile(BytesIO(project_zip(files))) as archive:
        assert "requirements.txt" in archive.namelist()
        assert any(name.startswith("tests/test_api_") for name in archive.namelist())
