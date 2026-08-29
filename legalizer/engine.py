from __future__ import annotations

from datetime import date

from .linters import lint_defined_terms, lint_internal_references, lint_source_governance
from .model import Finding, ResolvedProfile
from .resolver import resolve_profile


def check_text(
    text: str,
    *,
    profile_name: str,
    rules: dict[str, dict],
    profiles: dict[str, dict],
    sources: dict[str, dict],
    document_date: date | None = None,
    jurisdiction: str | None = "RU",
) -> tuple[ResolvedProfile, list[Finding]]:
    resolved = resolve_profile(
        profile_name,
        rules,
        profiles,
        sources,
        document_date=document_date,
        jurisdiction=jurisdiction,
    )

    findings: list[Finding] = []

    if "DOC-M05" in resolved.active_rules:
        findings.extend(
            lint_defined_terms(
                text,
                severity=resolved.active_rules["DOC-M05"].get("severity", "REVIEW"),
            )
        )

    if "DOC-N04" in resolved.active_rules:
        findings.extend(
            lint_internal_references(
                text,
                severity=resolved.active_rules["DOC-N04"].get("severity", "HARD_GATE"),
            )
        )

    if "DOC-P01" in resolved.active_rules:
        findings.extend(
            lint_source_governance(
                resolved,
                sources,
                document_date=document_date,
                jurisdiction=jurisdiction,
                severity=resolved.active_rules["DOC-P01"].get("severity", "HARD_GATE"),
            )
        )

    severity_rank = {"HARD_GATE": 0, "REVIEW": 1, "STYLE_WARNING": 2, "INFO": 3}
    findings.sort(
        key=lambda item: (
            item.line is None,
            item.line or 0,
            item.column or 0,
            severity_rank.get(item.severity, 99),
            item.rule_id,
        )
    )
    return resolved, findings
