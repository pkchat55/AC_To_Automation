from dataclasses import dataclass, field
from typing import Any


@dataclass
class Requirement:
    source: str
    key: str
    title: str
    description: str = ""
    acceptance_criteria: list[str] = field(default_factory=list)
    url: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "key": self.key,
            "title": self.title,
            "description": self.description,
            "acceptance_criteria": self.acceptance_criteria,
            "url": self.url,
            "metadata": self.metadata,
        }
