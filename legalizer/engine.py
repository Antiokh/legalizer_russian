from __future__ import annotations

from datetime import date

from .model import Finding, ResolvedProfile
from .registry import LintContext, run_registered_linters
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

    findings = run_registered_linters(
        LintContext(
            text=text,
            resolved=resolved,
            sources=sources,
            document_date=document_date,
            jurisdiction=jurisdiction,
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
