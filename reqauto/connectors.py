from typing import Any
import requests

from .models import Requirement
from .parser import adf_to_text, extract_acceptance_criteria, plain_text


class ConnectorError(RuntimeError):
    pass


def _map_azure_work_item(
    item: dict[str, Any],
    organization: str,
    project: str,
) -> Requirement:
    values = item.get("fields", {})
    item_id = item.get("id")
    criteria = values.get("Microsoft.VSTS.Common.AcceptanceCriteria", "")
    return Requirement(
        source="Azure Boards",
        key=str(item.get("id", "")),
        title=values.get("System.Title", "Untitled requirement"),
        description=plain_text(values.get("System.Description", "")),
        acceptance_criteria=extract_acceptance_criteria(criteria),
        url=f"https://dev.azure.com/{organization}/{project}/_workitems/edit/{item_id}",
        metadata={"work_item_type": values.get("System.WorkItemType", "")},
    )


def _map_jira_issue(
    issue: dict[str, Any],
    site_url: str,
    acceptance_field: str,
) -> Requirement:
    values = issue.get("fields", {})
    description = adf_to_text(values.get("description")).strip()
    criteria_value = values.get(acceptance_field) if acceptance_field else description
    criteria_text = (
        adf_to_text(criteria_value)
        if isinstance(criteria_value, (dict, list))
        else str(criteria_value or "")
    )
    key = issue.get("key", "")
    issue_type = values.get("issuetype") or {}
    return Requirement(
        source="Jira",
        key=key,
        title=values.get("summary", "Untitled requirement"),
        description=description,
        acceptance_criteria=extract_acceptance_criteria(criteria_text),
        url=f"{site_url}/browse/{key}",
        metadata={"issue_type": issue_type.get("name", "")},
    )


def _request(method: str, url: str, **kwargs) -> Any:
    try:
        response = requests.request(method, url, timeout=25, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        detail = ""
        if getattr(exc, "response", None) is not None:
            detail = f" ({exc.response.status_code}: {exc.response.text[:250]})"
        raise ConnectorError(f"Connection failed: {exc}{detail}") from exc


def fetch_azure_requirements(organization: str, project: str, pat: str, wiql: str, limit: int = 25) -> list[Requirement]:
    organization = organization.strip().rstrip("/")
    project = project.strip()
    if not all((organization, project, pat, wiql)):
        raise ConnectorError("Organization, project, PAT, and WIQL are required.")
    base = f"https://dev.azure.com/{organization}/{project}/_apis"
    query = _request("POST", f"{base}/wit/wiql?api-version=7.1", auth=("", pat), json={"query": wiql})
    ids = [str(item["id"]) for item in query.get("workItems", [])[:limit]]
    if not ids:
        return []
    fields = ",".join([
        "System.Id", "System.Title", "System.Description", "System.WorkItemType",
        "Microsoft.VSTS.Common.AcceptanceCriteria",
    ])
    data = _request(
        "GET",
        f"{base}/wit/workitems?ids={','.join(ids)}&fields={fields}&api-version=7.1",
        auth=("", pat),
    )
    return [
        _map_azure_work_item(item, organization, project)
        for item in data.get("value", [])
    ]


def fetch_jira_requirements(site_url: str, email: str, token: str, jql: str, acceptance_field: str = "", limit: int = 25) -> list[Requirement]:
    site_url = site_url.strip().rstrip("/")
    if not all((site_url, email, token, jql)):
        raise ConnectorError("Jira URL, email, API token, and JQL are required.")
    acceptance_field = acceptance_field.strip()
    fields = ["summary", "description", "issuetype"]
    if acceptance_field:
        fields.append(acceptance_field)
    payload = _request(
        "GET",
        f"{site_url}/rest/api/3/search",
        auth=(email, token),
        headers={"Accept": "application/json"},
        params={"jql": jql, "maxResults": limit, "fields": ",".join(fields)},
    )
    return [
        _map_jira_issue(issue, site_url, acceptance_field)
        for issue in payload.get("issues", [])
    ]
