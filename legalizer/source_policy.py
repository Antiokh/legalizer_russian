from __future__ import annotations

from datetime import date
from typing import Any


INACTIVE_STATUSES = {"PENDING_CHANGE", "HISTORICAL"}


def parse_iso_date(value: str | date | None) -> date | None:
    if value is None or isinstance(value, date):
        return value
    return date.fromisoformat(value)


def source_applicability(
    source: dict[str, Any],
    *,
    document_date: date | None = None,
    jurisdiction: str | None = None,
    include_historical: bool = False,
) -> tuple[bool, str | None]:
    status = source.get("status")
    if status == "PENDING_CHANGE":
        return False, "source is published/known but not active"
    if status == "HISTORICAL" and not include_historical:
        return False, "source is historical"

    source_jurisdiction = source.get("jurisdiction")
    if jurisdiction and source_jurisdiction and source_jurisdiction != jurisdiction:
        return False, f"jurisdiction mismatch: {source_jurisdiction} != {jurisdiction}"

    if document_date:
        effective_from = parse_iso_date(source.get("effective_from"))
        effective_to = parse_iso_date(source.get("effective_to"))
        if effective_from and document_date < effective_from:
            return False, f"source effective only from {effective_from.isoformat()}"
        if effective_to and document_date > effective_to:
            return False, f"source expired on {effective_to.isoformat()}"

    return True, None


def rule_source_applicability(
    rule: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    *,
    document_date: date | None = None,
    jurisdiction: str | None = None,
) -> tuple[bool, str | None]:
    source_ids = rule.get("source_ids") or []
    if not source_ids:
        return True, None

    known = []
    applicable = []
    reasons = []
    for source_id in source_ids:
        source = sources.get(source_id)
        if source is None:
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
            reasons.append(f"{source_id}: {reason}")

    # Unknown source metadata must not silently disable a rule. It is a registry
    # completeness problem, not evidence that the rule is inapplicable.
    if not known:
        return True, None
    if applicable:
        return True, None
    return False, "; ".join(reasons) or "no applicable registered source"


def validate_source_registry(
    rules: dict[str, dict[str, Any]], sources: dict[str, dict[str, Any]]
) -> list[str]:
    problems: list[str] = []
    for rule_id, rule in rules.items():
        for source_id in rule.get("source_ids") or []:
            if source_id not in sources:
                problems.append(f"{rule_id}: missing source metadata for {source_id}")
    return problems
