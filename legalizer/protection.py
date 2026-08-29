from __future__ import annotations

from dataclasses import asdict, dataclass

from .linters.defined_terms import defined_term_occurrences
from .model import ResolvedProfile
from .text import line_column


@dataclass(slots=True)
class ProtectedSpan:
    kind: str
    text: str
    start: int
    end: int
    line: int
    column: int
    meta: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ProtectionResult:
    spans: list[ProtectedSpan]
    protected_classes: set[str]
    unresolved_classes: set[str]
    disabled_rules_on_spans: set[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "spans": [span.to_dict() for span in self.spans],
            "protected_classes": sorted(self.protected_classes),
            "unresolved_classes": sorted(self.unresolved_classes),
            "disabled_rules_on_spans": sorted(self.disabled_rules_on_spans),
        }


def collect_protected_spans(text: str, resolved: ResolvedProfile) -> ProtectionResult:
    spans: list[ProtectedSpan] = []
    resolved_classes: set[str] = set()

    if "defined_terms" in resolved.protected_classes:
        resolved_classes.add("defined_terms")
        for term, match in defined_term_occurrences(text):
            line, column = line_column(text, match.start())
            spans.append(
                ProtectedSpan(
                    kind="defined_term",
                    text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    line=line,
                    column=column,
                    meta={
                        "canonical": term.alias,
                        "definition_line": term.line,
                    },
                )
            )

    spans.sort(key=lambda span: (span.start, span.end, span.kind))
    unresolved = set(resolved.protected_classes) - resolved_classes
    return ProtectionResult(
        spans=spans,
        protected_classes=set(resolved.protected_classes),
        unresolved_classes=unresolved,
        disabled_rules_on_spans=set(resolved.disabled_for_protected_spans),
    )
