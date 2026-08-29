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
    for rule_id, rule in resolved.active_rules.items():
        for source_id in rule.get("source_ids") or []:
            source = sources.get(source_id)
            if source is None:
                findings.append(
                    Finding(
                        rule_id="DOC-P01",
                        severity=severity,
                        message=f"Для источника {source_id}, используемого правилом {rule_id}, нет метаданных применимости.",
                        meta={"affected_rule": rule_id, "source_id": source_id},
                    )
                )
                continue
            ok, reason = source_applicability(
                source,
                document_date=document_date,
                jurisdiction=jurisdiction,
            )
            if not ok:
                findings.append(
                    Finding(
                        rule_id="DOC-P01",
                        severity=severity,
                        message=f"Правило {rule_id} опирается на неприменимый источник {source_id}: {reason}.",
                        meta={"affected_rule": rule_id, "source_id": source_id},
                    )
                )
    return findings
