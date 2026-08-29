from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any

from .model import ResolvedProfile
from .source_policy import parse_iso_date, rule_source_applicability


class ResolverError(RuntimeError):
    pass


_LIST_KEYS = {"enable", "disable", "protect", "disable_for_protected_spans", "notes"}
_MAP_KEYS = {"downgrade", "upgrade", "override"}


def _merge_profile(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for key in _LIST_KEYS:
        values: list[Any] = []
        for source in (parent, child):
            for value in source.get(key, []) or []:
                if value not in values:
                    values.append(value)
        if values:
            merged[key] = values

    for key in _MAP_KEYS:
        value: dict[str, Any] = {}
        value.update(parent.get(key, {}) or {})
        if key == "override":
            for rule_id, patch in (child.get(key, {}) or {}).items():
                prior = deepcopy(value.get(rule_id, {}))
                prior.update(patch or {})
                value[rule_id] = prior
        else:
            value.update(child.get(key, {}) or {})
        if value:
            merged[key] = value

    if "description" in child:
        merged["description"] = child["description"]
    elif "description" in parent:
        merged["description"] = parent["description"]
    return merged


def flatten_profile(name: str, profiles: dict[str, dict[str, Any]]) -> dict[str, Any]:
    visiting: set[str] = set()

    def visit(current: str) -> dict[str, Any]:
        if current in visiting:
            raise ResolverError(f"Profile inheritance cycle at {current}")
        profile = profiles.get(current)
        if profile is None:
            raise ResolverError(f"Unknown profile: {current}")
        visiting.add(current)
        parent_name = profile.get("extends")
        parent = visit(parent_name) if parent_name else {}
        visiting.remove(current)
        return _merge_profile(parent, profile)

    return visit(name)


def _rule_applicability(
    rule: dict[str, Any],
    sources: dict[str, dict[str, Any]],
    *,
    document_date: date | None,
    jurisdiction: str | None,
) -> tuple[bool, str | None]:
    rule_jurisdiction = rule.get("jurisdiction")
    if jurisdiction and rule_jurisdiction and rule_jurisdiction != jurisdiction:
        return False, f"rule jurisdiction mismatch: {rule_jurisdiction} != {jurisdiction}"

    if rule.get("source_status") == "PENDING_CHANGE":
        return False, "rule is based on a pending change"

    if document_date:
        effective_from = parse_iso_date(rule.get("effective_from"))
        effective_to = parse_iso_date(rule.get("effective_to"))
        if effective_from and document_date < effective_from:
            return False, f"rule effective only from {effective_from.isoformat()}"
        if effective_to and document_date > effective_to:
            return False, f"rule expired on {effective_to.isoformat()}"

    return rule_source_applicability(
        rule,
        sources,
        document_date=document_date,
        jurisdiction=jurisdiction,
    )


def resolve_profile(
    name: str,
    rules: dict[str, dict[str, Any]],
    profiles: dict[str, dict[str, Any]],
    sources: dict[str, dict[str, Any]],
    *,
    document_date: date | None = None,
    jurisdiction: str | None = "RU",
) -> ResolvedProfile:
    profile = flatten_profile(name, profiles)
    enabled = list(profile.get("enable", []) or [])
    disabled = set(profile.get("disable", []) or [])
    overrides = profile.get("override", {}) or {}

    active: dict[str, dict[str, Any]] = {}
    inactive: dict[str, str] = {}
    source_inactive: dict[str, dict[str, Any]] = {}
    disabled_external: set[str] = set()

    for item in disabled:
        if item not in rules:
            disabled_external.add(item)

    for rule_id in enabled:
        rule = rules.get(rule_id)
        if rule is None:
            raise ResolverError(f"Profile {name} enables unknown rule {rule_id}")
        if rule_id in disabled:
            inactive[rule_id] = "disabled by profile"
            continue

        resolved_rule = deepcopy(rule)
        resolved_rule.update(overrides.get(rule_id, {}) or {})
        ok, reason = _rule_applicability(
            resolved_rule,
            sources,
            document_date=document_date,
            jurisdiction=jurisdiction,
        )
        if not ok:
            inactive[rule_id] = reason or "not applicable"
            source_inactive[rule_id] = resolved_rule
            continue
        active[rule_id] = resolved_rule

    external_severity: dict[str, str] = {}
    external_severity.update(profile.get("downgrade", {}) or {})
    external_severity.update(profile.get("upgrade", {}) or {})

    return ResolvedProfile(
        name=name,
        active_rules=active,
        protected_classes=set(profile.get("protect", []) or []),
        disabled_external_rules=disabled_external,
        disabled_for_protected_spans=set(profile.get("disable_for_protected_spans", []) or []),
        external_severity=external_severity,
        notes=list(profile.get("notes", []) or []),
        inactive_rules=inactive,
        source_inactive_rules=source_inactive,
    )
