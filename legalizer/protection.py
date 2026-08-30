from __future__ import annotations

from dataclasses import asdict, dataclass

from .linters.admin_orders import directive_infinitive_occurrences
from .linters.consequences import breach_trigger_occurrences, legal_consequence_occurrences
from .linters.contract_parties import party_alias_occurrences
from .linters.deadlines import relative_deadline_occurrences
from .linters.defined_terms import defined_term_occurrences
from .linters.modality import modality_occurrences
from .linters.obligations import obligation_action_occurrences
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

    if "obligation_action" in resolved.protected_classes:
        resolved_classes.add("obligation_action")
        for occurrence in obligation_action_occurrences(text):
            line, column = line_column(text, occurrence.start)
            spans.append(
                ProtectedSpan(
                    kind="obligation_action",
                    text=occurrence.action,
                    start=occurrence.start,
                    end=occurrence.end,
                    line=line,
                    column=column,
                    meta={"modality": occurrence.modality},
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

    deadline_classes = {"relative_deadline", "deadline_anchor"} & resolved.protected_classes
    if deadline_classes:
        resolved_classes.update(deadline_classes)
        for deadline in relative_deadline_occurrences(text):
            if "relative_deadline" in deadline_classes:
                line, column = line_column(text, deadline.start)
                spans.append(
                    ProtectedSpan(
                        kind="relative_deadline",
                        text=deadline.text,
                        start=deadline.start,
                        end=deadline.end,
                        line=line,
                        column=column,
                        meta={"has_local_anchor": deadline.anchor_text is not None},
                    )
                )
            if (
                "deadline_anchor" in deadline_classes
                and deadline.anchor_text is not None
                and deadline.anchor_start is not None
                and deadline.anchor_end is not None
            ):
                line, column = line_column(text, deadline.anchor_start)
                spans.append(
                    ProtectedSpan(
                        kind="deadline_anchor",
                        text=deadline.anchor_text,
                        start=deadline.anchor_start,
                        end=deadline.anchor_end,
                        line=line,
                        column=column,
                        meta={"deadline": deadline.text},
                    )
                )

    if "breach_trigger" in resolved.protected_classes:
        resolved_classes.add("breach_trigger")
        for trigger in breach_trigger_occurrences(text):
            line, column = line_column(text, trigger.start)
            spans.append(
                ProtectedSpan(
                    kind="breach_trigger",
                    text=trigger.text,
                    start=trigger.start,
                    end=trigger.end,
                    line=line,
                    column=column,
                    meta={"form": trigger.kind},
                )
            )

    if "legal_consequence" in resolved.protected_classes:
        resolved_classes.add("legal_consequence")
        for consequence in legal_consequence_occurrences(text):
            line, column = line_column(text, consequence.start)
            spans.append(
                ProtectedSpan(
                    kind="legal_consequence",
                    text=consequence.text,
                    start=consequence.start,
                    end=consequence.end,
                    line=line,
                    column=column,
                    meta={"consequence": consequence.kind},
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
