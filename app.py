import streamlit as st

from reqauto.connectors import ConnectorError, fetch_azure_requirements, fetch_jira_requirements
from reqauto.demo import demo_requirements
from reqauto.generator import generate_project, project_zip
from reqauto.runner import run_demo_api_tests, validate_test_code

st.set_page_config(page_title="Requirement → Automation", page_icon="✅", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1250px; padding-top: 2rem;}
[data-testid="stMetric"] {background:#f6f8fb;border:1px solid #e4e9f2;border-radius:12px;padding:12px;}
.small-note {color:#5f6b7a;font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

st.title("Requirement → Automation")
st.caption("Turn Azure Boards and Jira acceptance criteria into reviewable pytest API and browser tests.")

if "requirements" not in st.session_state:
    st.session_state.requirements = demo_requirements()
if "generated" not in st.session_state:
    st.session_state.generated = {}

with st.sidebar:
    st.header("1. Requirement source")
    source = st.radio("Choose a source", ["Demo", "Azure Boards", "Jira"], help="Demo works without credentials.")
    loaded = None
    if source == "Demo":
        st.success("Ready with safe sample requirements")
        if st.button("Reload demo requirements", use_container_width=True):
            loaded = demo_requirements()
    elif source == "Azure Boards":
        organization = st.text_input("Organization", placeholder="contoso")
        project = st.text_input("Project")
        pat = st.text_input("Personal access token", type="password")
        wiql = st.text_area("WIQL query", value="SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject] = @project AND [System.WorkItemType] IN ('User Story','Product Backlog Item') ORDER BY [System.ChangedDate] DESC")
        if st.button("Load from Azure Boards", type="primary", use_container_width=True):
            try:
                loaded = fetch_azure_requirements(organization, project, pat, wiql)
            except ConnectorError as exc:
                st.error(str(exc))
    else:
        site_url = st.text_input("Jira site URL", placeholder="https://company.atlassian.net")
        email = st.text_input("Jira account email")
        token = st.text_input("API token", type="password")
        jql = st.text_area("JQL query", value="project = DEMO ORDER BY updated DESC")
        acceptance_field = st.text_input("Acceptance criteria field ID (optional)", placeholder="customfield_10042")
        if st.button("Load from Jira", type="primary", use_container_width=True):
            try:
                loaded = fetch_jira_requirements(site_url, email, token, jql, acceptance_field)
            except ConnectorError as exc:
                st.error(str(exc))
    if loaded is not None:
        st.session_state.requirements = loaded
        st.session_state.generated = {}
        st.success(f"Loaded {len(loaded)} requirements")

requirements = st.session_state.requirements
criteria_count = sum(len(item.acceptance_criteria) for item in requirements)
col1, col2, col3 = st.columns(3)
col1.metric("Requirements", len(requirements))
col2.metric("Acceptance criteria", criteria_count)
col3.metric("Generated files", len(st.session_state.generated))

st.header("2. Review source requirements")
if not requirements:
    st.warning("No matching requirements were found. Adjust the source query and try again.")
else:
    selected_keys = st.multiselect(
        "Requirements to automate",
        options=[item.key for item in requirements],
        default=[item.key for item in requirements],
        format_func=lambda key: next(f"{r.key} — {r.title}" for r in requirements if r.key == key),
    )
    for requirement in requirements:
        with st.expander(f"{requirement.key} · {requirement.title}"):
            st.write(requirement.description or "No description supplied.")
            st.markdown("**Acceptance criteria**")
            if requirement.acceptance_criteria:
                for criterion in requirement.acceptance_criteria:
                    st.markdown(f"- {criterion}")
            else:
                st.warning("No acceptance criteria found. Generated output will require manual review.")
            if requirement.url:
                st.link_button("Open source item", requirement.url)

st.header("3. Generate tests")
kinds = st.multiselect("Automation types", ["API", "Web UI"], default=["API", "Web UI"])
selected = [item for item in requirements if item.key in selected_keys] if requirements else []
if st.button("Generate automation project", type="primary", disabled=not selected or not kinds):
    st.session_state.generated = generate_project(selected, kinds)
    st.rerun()

files = st.session_state.generated
if files:
    st.info("Generated tests are starting points. Review routes, selectors, test data, and expected results before CI use.")
    test_names = [name for name in files if name.endswith(".py") and name.startswith("tests/")]
    chosen = st.selectbox("Edit generated test", test_names)
    editor_key = f"editor_{chosen}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = files[chosen]
    edited = st.text_area("Test code", key=editor_key, height=420)
    if st.button("Apply edit"):
        files[chosen] = edited
        st.success("Edit applied to the downloadable project.")

    issues = validate_test_code(edited)
    if issues:
        st.error("Validation found: " + "; ".join(issues))
    else:
        st.success("Syntax and safety validation passed for the selected file.")

    st.download_button(
        f"Download this script ({chosen.split('/')[-1]})",
        edited,
        file_name=chosen.split("/")[-1],
        mime="text/x-python",
        use_container_width=True,
    )

    api_files = {name: content for name, content in files.items() if name.startswith("tests/test_api_")}
    ui_files = {name: content for name, content in files.items() if name.startswith("tests/test_ui_")}

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.download_button(
            "Download API scripts (.zip)",
            project_zip(api_files),
            file_name="api-automation-tests.zip",
            mime="application/zip",
            use_container_width=True,
            disabled=not api_files,
        )
    with col_b:
        st.download_button(
            "Download Playwright UI scripts (.zip)",
            project_zip(ui_files),
            file_name="playwright-ui-automation-tests.zip",
            mime="application/zip",
            use_container_width=True,
            disabled=not ui_files,
        )
    with col_c:
        st.download_button(
            "Download full pytest project (.zip)",
            project_zip(files),
            file_name="requirement-automation.zip",
            mime="application/zip",
            use_container_width=True,
        )

    run_confirmed = st.checkbox("I understand this sends demo API requests to dummyjson.com")
    if st.button("Run generated API tests in demo mode", disabled=not run_confirmed, use_container_width=True):
        with st.spinner("Running tests in an isolated temporary folder..."):
            code, output = run_demo_api_tests(files)
        if code == 0:
            st.success("API test run passed")
        else:
            st.error(f"API test run exited with code {code}")
        st.code(output or "No output", language="text")

st.header("4. AI Agent (LangChain + OpenAI)")
st.caption("Give a plain-language instruction. The agent picks which tools to call: load requirements, generate tests, validate, and run them.")
with st.expander("Run the LangChain agent", expanded=False):
    openai_key = st.text_input("OpenAI API key", type="password", key="agent_openai_key")
    agent_model = st.text_input("Model", value="gpt-4o-mini", key="agent_model")
    agent_instruction = st.text_area(
        "Instruction",
        value="Load the demo requirements, generate API and Playwright UI tests for all of them, then run the API tests and summarize results.",
        key="agent_instruction",
    )
    if st.button("Run agent", type="primary", disabled=not openai_key, use_container_width=True):
        try:
            from reqauto.agent import RequirementAutomationAgent
        except ImportError:
            st.error("Install the agent dependencies first: pip install langchain langchain-openai openai")
        else:
            with st.spinner("Agent is working..."):
                try:
                    agent = RequirementAutomationAgent(openai_api_key=openai_key, model=agent_model)
                    summary = agent.run(agent_instruction)
                except Exception as exc:
                    st.error(f"Agent run failed: {exc}")
                else:
                    st.success("Agent finished")
                    st.write(summary)
                    if agent.requirements:
                        st.session_state.requirements = agent.requirements
                    if agent.generated_files:
                        st.session_state.generated = agent.generated_files
                    st.rerun()

st.divider()
st.markdown('<div class="small-note">Credentials stay in this browser session and are only sent to the selected service. They are not written to project files.</div>', unsafe_allow_html=True)

