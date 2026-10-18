from unittest.mock import patch

from reqauto.connectors import fetch_azure_requirements, fetch_jira_requirements


@patch("reqauto.connectors._request")
def test_azure_mapping(request):
    request.side_effect = [
        {"workItems": [{"id": 12}]},
        {"value": [{"id": 12, "fields": {"System.Title": "Save order", "System.Description": "Details", "Microsoft.VSTS.Common.AcceptanceCriteria": "<p>Returns 201</p>"}}]},
    ]
    result = fetch_azure_requirements("org", "project", "pat", "query")
    assert result[0].key == "12"
    assert result[0].title == "Save order"
    assert result[0].description == "Details"
    assert result[0].acceptance_criteria == ["Returns 201"]
    assert result[0].url == "https://dev.azure.com/org/project/_workitems/edit/12"
    assert result[0].metadata == {"work_item_type": ""}


@patch("reqauto.connectors._request")
def test_jira_mapping(request):
    request.return_value = {"issues": [{"key": "APP-1", "fields": {"summary": "Login", "description": {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Shows account page"}]}]}, "issuetype": {"name": "Story"}}}]}
    result = fetch_jira_requirements("https://test.atlassian.net", "me@test.com", "token", "project=APP")
    assert result[0].title == "Login"
    assert result[0].description == "Shows account page"
    assert result[0].acceptance_criteria == ["Shows account page"]
    assert result[0].url == "https://test.atlassian.net/browse/APP-1"
    assert result[0].metadata == {"issue_type": "Story"}
