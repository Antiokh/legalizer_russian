from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from .linters import (
    lint_condition_exception_scope,
    lint_defined_terms,
    lint_instrumental_attachment,
    lint_internal_references,
    lint_legislation_hierarchy,
    lint_legislation_preamble,
    lint_order_directive_infinitives,
    lint_party_aliases,
    lint_source_governance,
    lint_vague_time_references,
)
from .model import Finding, ResolvedProfile


@dataclass(slots=True)
class LintContext:
    text: str
    resolved: ResolvedProfile
    sources: dict[str, dict]
    document_date: date | None
    jurisdiction: str | None


LinterAdapter = Callable[[LintContext, dict], list[Finding]]


def _text_adapter(fn: Callable[[str, str], list[Finding]]) -> LinterAdapter:
    def run(context: LintContext, rule: dict) -> list[Finding]:
        return fn(context.text, severity=rule.get("severity", "REVIEW"))

    return run


def _source_governance(context: LintContext, rule: dict) -> list[Finding]:
    return lint_source_governance(
        context.resolved,
        context.sources,
        document_date=context.document_date,
        jurisdiction=context.jurisdiction,
        severity=rule.get("severity", "HARD_GATE"),
    )


IMPLEMENTATIONS: dict[str, LinterAdapter] = {
    "DOC-M05": _text_adapter(lint_defined_terms),
    "DOC-N01": _text_adapter(lint_legislation_preamble),
    "DOC-N02": _text_adapter(lint_legislation_hierarchy),
    "DOC-N04": _text_adapter(lint_internal_references),
    "DOC-P01": _source_governance,
    "LDB-009": _text_adapter(lint_vague_time_references),
    "LDB-012": _text_adapter(lint_instrumental_attachment),
    "LDB-015": _text_adapter(lint_condition_exception_scope),
    "ADM-ORDER-001": _text_adapter(lint_order_directive_infinitives),
    "CTR-001": _text_adapter(lint_party_aliases),
}


def implemented_rule_ids() -> set[str]:
    return set(IMPLEMENTATIONS)


def run_registered_linters(context: LintContext) -> list[Finding]:
    findings: list[Finding] = []
    for rule_id, rule in context.resolved.active_rules.items():
        implementation = IMPLEMENTATIONS.get(rule_id)
        if implementation is None:
            continue
        findings.extend(implementation(context, rule))
    return findings
