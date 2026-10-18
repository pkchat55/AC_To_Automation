import re
from html import unescape


def plain_text(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", str(value), flags=re.I)
    text = re.sub(r"</(?:p|li|div|h\d)>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).replace("\r", "").strip()


def extract_acceptance_criteria(value: str | None) -> list[str]:
    text = plain_text(value)
    if not text:
        return []
    lines = [re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    if len(lines) > 1:
        return lines
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [item.strip() for item in sentences if item.strip()]


def adf_to_text(node) -> str:
    """Convert Jira Atlassian Document Format into readable text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(adf_to_text(item) for item in node)
    if not isinstance(node, dict):
        return str(node)
    node_type = node.get("type")
    text = node.get("text", "")
    children = "".join(adf_to_text(item) for item in node.get("content", []))
    suffix = "\n" if node_type in {"paragraph", "heading", "listItem", "bulletList", "orderedList"} else ""
    return text + children + suffix
