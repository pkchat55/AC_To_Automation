"""LangChain tool-calling agent that automates requirement -> pytest/Playwright test generation.

Wraps the existing connectors/generator/runner functions as LangChain tools so an
OpenAI chat model can decide which actions to take from a plain-language instruction,
e.g. "Load the demo requirements, generate API and Playwright UI tests, then run them."
"""
import os

from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from .connectors import ConnectorError, fetch_azure_requirements, fetch_jira_requirements
from .demo import demo_requirements
from .generator import generate_project, project_zip
from .models import Requirement
from .runner import run_demo_api_tests, validate_test_code

SYSTEM_PROMPT = (
    "You are an automation engineer agent. You turn Azure Boards or Jira requirements "
    "and their acceptance criteria into reviewable pytest API tests and Playwright UI "
    "tests. Load requirements with a tool before generating tests. After generating "
    "tests, summarize what was produced and what a human should review before using "
    "them in CI. Never claim a test is production-ready without review."
)


class RequirementAutomationAgent:
    """Stateful wrapper: holds loaded requirements and generated files across tool calls."""

    def __init__(self, openai_api_key: str, model: str = "gpt-4o-mini", temperature: float = 0.0):
        if not openai_api_key:
            raise ValueError("An OpenAI API key is required.")
        self.requirements: list[Requirement] = []
        self.generated_files: dict[str, str] = {}
        self.llm = ChatOpenAI(model=model, temperature=temperature, api_key=openai_api_key)
        self.tools = [
            self._tool_load_demo_requirements(),
            self._tool_load_azure_requirements(),
            self._tool_load_jira_requirements(),
            self._tool_list_requirements(),
            self._tool_generate_tests(),
            self._tool_list_generated_files(),
            self._tool_validate_test(),
            self._tool_run_api_tests(),
        ]
        self.graph = create_agent(self.llm, self.tools, system_prompt=SYSTEM_PROMPT)

    def run(self, instruction: str) -> str:
        result = self.graph.invoke({"messages": [("user", instruction)]})
        return result["messages"][-1].content

    # ---- tools ------------------------------------------------------------
    def _tool_load_demo_requirements(self):
        @tool("load_demo_requirements")
        def _run() -> str:
            """Load the built-in safe sample requirements. Use this when no real credentials are available."""
            self.requirements = demo_requirements()
            return f"Loaded {len(self.requirements)} demo requirements: " + ", ".join(r.key for r in self.requirements)
        return _run

    def _tool_load_azure_requirements(self):
        @tool("load_azure_requirements")
        def _run(organization: str, project: str, personal_access_token: str, wiql: str = "") -> str:
            """Load requirements and acceptance criteria from Azure Boards.
            Args: organization, project, personal_access_token, and an optional WIQL query."""
            query = wiql or (
                "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project "
                "AND [System.WorkItemType] IN ('User Story','Product Backlog Item') ORDER BY [System.ChangedDate] DESC"
            )
            try:
                self.requirements = fetch_azure_requirements(organization, project, personal_access_token, query)
            except ConnectorError as exc:
                return f"Azure Boards load failed: {exc}"
            return f"Loaded {len(self.requirements)} requirements from Azure Boards."
        return _run

    def _tool_load_jira_requirements(self):
        @tool("load_jira_requirements")
        def _run(site_url: str, email: str, api_token: str, jql: str = "", acceptance_field: str = "") -> str:
            """Load requirements and acceptance criteria from Jira.
            Args: site_url, email, api_token, optional jql, optional acceptance_field custom field id."""
            query = jql or "project = DEMO ORDER BY updated DESC"
            try:
                self.requirements = fetch_jira_requirements(site_url, email, api_token, query, acceptance_field)
            except ConnectorError as exc:
                return f"Jira load failed: {exc}"
            return f"Loaded {len(self.requirements)} requirements from Jira."
        return _run

    def _tool_list_requirements(self):
        @tool("list_loaded_requirements")
        def _run() -> str:
            """List requirements currently loaded, with key, title, and acceptance criteria count."""
            if not self.requirements:
                return "No requirements loaded yet. Load demo, Azure, or Jira requirements first."
            return "\n".join(
                f"{r.key} - {r.title} ({len(r.acceptance_criteria)} acceptance criteria)"
                for r in self.requirements
            )
        return _run

    def _tool_generate_tests(self):
        @tool("generate_tests")
        def _run(requirement_keys: str = "", kinds: str = "API,Web UI") -> str:
            """Generate pytest API tests and/or Playwright UI tests for loaded requirements.
            requirement_keys: comma-separated keys to include, empty means all loaded requirements.
            kinds: comma-separated subset of 'API' and 'Web UI'."""
            if not self.requirements:
                return "No requirements loaded. Load requirements before generating tests."
            keys = {k.strip() for k in requirement_keys.split(",") if k.strip()}
            selected = [r for r in self.requirements if not keys or r.key in keys]
            if not selected:
                return f"No loaded requirements matched keys: {requirement_keys}"
            kind_list = [k.strip() for k in kinds.split(",") if k.strip()] or ["API", "Web UI"]
            self.generated_files = generate_project(selected, kind_list)
            test_files = [name for name in self.generated_files if name.startswith("tests/")]
            return f"Generated {len(test_files)} test files: " + ", ".join(test_files)
        return _run

    def _tool_list_generated_files(self):
        @tool("list_generated_files")
        def _run() -> str:
            """List file names currently generated and ready to save, validate, or run."""
            if not self.generated_files:
                return "No files generated yet."
            return "\n".join(self.generated_files)
        return _run

    def _tool_validate_test(self):
        @tool("validate_test_script")
        def _run(file_name: str) -> str:
            """Validate the syntax and safety of a generated test file, e.g. 'tests/test_api_x.py'."""
            if file_name not in self.generated_files:
                return f"Unknown file: {file_name}. Known files: {', '.join(self.generated_files)}"
            issues = validate_test_code(self.generated_files[file_name])
            return "OK, no issues found." if not issues else "Issues found: " + "; ".join(issues)
        return _run

    def _tool_run_api_tests(self):
        @tool("run_generated_api_tests")
        def _run() -> str:
            """Run the generated pytest API tests in an isolated temp folder against the demo API (dummyjson.com) and report pass/fail."""
            if not self.generated_files:
                return "No files generated yet."
            code, output = run_demo_api_tests(self.generated_files)
            status = "PASSED" if code == 0 else f"FAILED (exit code {code})"
            return f"{status}\n{output[-4000:]}"
        return _run

    # ---- helpers outside the agent loop -----------------------------------
    def save_generated_files(self, output_dir: str) -> list[str]:
        """Write generated files to disk under output_dir. Returns written file paths."""
        written = []
        for rel_path, content in self.generated_files.items():
            full_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as handle:
                handle.write(content)
            written.append(full_path)
        return written

    def zip_bytes(self) -> bytes:
        return project_zip(self.generated_files)
