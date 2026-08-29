from __future__ import annotations

from datetime import date

from ..model import Finding, ResolvedProfile
from ..source_policy import source_applicability


def lint_source_governance(
    resolved: ResolvedProfile,
    sources: dict[str, dict],
    *,
    document_date: date | None = None,
    jurisdiction: str | None = "RU",
    severity: str = "HARD_GATE",
) -> list[Finding]:
    findings: list[Finding] = []

    # An enabled rule may be intentionally withheld because none of its sources
    # applies to this document date/jurisdiction. That is safer than applying an
    # inapplicable rule, but it must not become a silent clean result.
    for rule_id in resolved.source_inactive_rules:
        reason = resolved.inactive_rules.get(rule_id, "source not applicable")
        findings.append(
            Finding(
                rule_id="DOC-P01",
                severity=severity,
                message=(
                    f"Правило {rule_id} включено профилем, но отключено по применимости источника: {reason}. "
                    "Проверка по этому правилу не выполнена."
                ),
                meta={
                    "affected_rule": rule_id,
                    "problem": "enabled_rule_source_inapplicable",
                    "reason": reason,
                },
            )
        )

    for rule_id, rule in resolved.active_rules.items():
        source_ids = rule.get("source_ids") or []
        if not source_ids:
            continue

        applicable: list[str] = []
        known: list[str] = []
        inactive_reasons: list[str] = []

        for source_id in source_ids:
            source = sources.get(source_id)
            if source is None:
                findings.append(
                    Finding(
                        rule_id="DOC-P01",
                        severity=severity,
                        message=f"Для источника {source_id}, используемого правилом {rule_id}, нет метаданных применимости.",
                        meta={"affected_rule": rule_id, "source_id": source_id, "problem": "missing_source_metadata"},
                    )
                )
                continue

            known.append(source_id)
            ok, reason = source_applicability(
                source,
                document_date=document_date,
                jurisdiction=jurisdiction,
            )
            if ok:
                applicable.append(source_id)
            elif reason:
                inactive_reasons.append(f"{source_id}: {reason}")

        # A rule may cite several editions or supporting sources. One inactive
        # source does not invalidate the rule if another registered source is
        # applicable for the document date/jurisdiction.
        if known and not applicable:
            findings.append(
                Finding(
                    rule_id="DOC-P01",
                    severity=severity,
                    message=(
                        f"У активного правила {rule_id} не осталось применимых зарегистрированных источников: "
                        + "; ".join(inactive_reasons)
                    ),
                    meta={"affected_rule": rule_id, "problem": "no_applicable_source"},
                )
            )

    return findings
