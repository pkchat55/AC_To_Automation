from reqauto.parser import adf_to_text, extract_acceptance_criteria, plain_text


def test_extracts_html_list():
    value = "<ul><li>Returns 200</li><li>Contains a title</li></ul>"
    assert extract_acceptance_criteria(value) == ["Returns 200", "Contains a title"]


def test_plain_text_removes_markup():
    assert plain_text("<p>Hello &amp; welcome</p>") == "Hello & welcome"


def test_converts_jira_adf():
    document = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Given a user"}]}]}
    assert adf_to_text(document).strip() == "Given a user"
