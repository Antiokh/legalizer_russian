from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    line: int | None = None
    column: int | None = None
    evidence: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v not in (None, {}, [])}


@dataclass(slots=True)
class ResolvedProfile:
    name: str
    active_rules: dict[str, dict[str, Any]]
    protected_classes: set[str] = field(default_factory=set)
    disabled_external_rules: set[str] = field(default_factory=set)
    external_severity: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    inactive_rules: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "active_rules": self.active_rules,
            "protected_classes": sorted(self.protected_classes),
            "disabled_external_rules": sorted(self.disabled_external_rules),
            "external_severity": dict(sorted(self.external_severity.items())),
            "notes": self.notes,
            "inactive_rules": self.inactive_rules,
        }
