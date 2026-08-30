from __future__ import annotations

from dataclasses import asdict, dataclass

from .linters.admin_orders import directive_infinitive_occurrences
from .linters.contract_parties import party_alias_occurrences
from .linters.defined_terms import defined_term_occurrences
from .linters.modality import modality_occurrences
from .linters.scope import scope_marker_occurrences
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

    if "party_names" in resolved.protected_classes:
        resolved_classes.add("party_names")
        for party, match in party_alias_occurrences(text):
            line, column = line_column(text, match.start())
            spans.append(
                ProtectedSpan(
                    kind="party_name",
                    text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    line=line,
                    column=column,
                    meta={
                        "canonical": party.alias,
                        "definition_line": party.line,
                    },
                )
            )

    modality_classes = {"obligation_modality", "legal_modality"} & resolved.protected_classes
    if modality_classes:
        resolved_classes.update(modality_classes)
        for occurrence in modality_occurrences(text):
            line, column = line_column(text, occurrence.start)
            spans.append(
                ProtectedSpan(
                    kind="legal_modality",
                    text=occurrence.text,
                    start=occurrence.start,
                    end=occurrence.end,
                    line=line,
                    column=column,
                    meta={"modality": occurrence.kind},
                )
            )

    scope_markers = scope_marker_occurrences(text)
    if "condition_scope_marker" in resolved.protected_classes:
        resolved_classes.add("condition_scope_marker")
        for marker in scope_markers:
            if marker.kind != "condition":
                continue
            line, column = line_column(text, marker.start)
            spans.append(
                ProtectedSpan(
                    kind="condition_scope_marker",
                    text=marker.text,
                    start=marker.start,
                    end=marker.end,
                    line=line,
                    column=column,
                    meta={"form": marker.form},
                )
            )

    if "exception_scope_marker" in resolved.protected_classes:
        resolved_classes.add("exception_scope_marker")
        for marker in scope_markers:
            if marker.kind != "exception":
                continue
            line, column = line_column(text, marker.start)
            spans.append(
                ProtectedSpan(
                    kind="exception_scope_marker",
                    text=marker.text,
                    start=marker.start,
                    end=marker.end,
                    line=line,
                    column=column,
                    meta={"form": marker.form},
                )
            )

    if "directive_infinitive" in resolved.protected_classes:
        resolved_classes.add("directive_infinitive")
        for directive, match in directive_infinitive_occurrences(text):
            line, column = line_column(text, match.start())
            spans.append(
                ProtectedSpan(
                    kind="directive_infinitive",
                    text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    line=line,
                    column=column,
                    meta={"directive": directive.number},
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
