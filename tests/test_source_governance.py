from datetime import date

from legalizer.linters.source_governance import lint_source_governance
from legalizer.model import ResolvedProfile


def test_one_inactive_supporting_source_does_not_invalidate_rule():
    resolved = ResolvedProfile(
        name="contractual",
        active_rules={"X": {"source_ids": ["OLD", "CURRENT"]}},
    )
    sources = {
        "OLD": {"status": "HISTORICAL", "jurisdiction": "RU"},
        "CURRENT": {"status": "CURRENT_NORM", "jurisdiction": "RU"},
    }
    assert lint_source_governance(resolved, sources, document_date=date(2026, 8, 29)) == []


def test_source_inactive_enabled_rule_is_reported():
    rule = {"source_ids": ["FUTURE"]}
    resolved = ResolvedProfile(
        name="contractual",
        active_rules={},
        inactive_rules={"X": "FUTURE: source effective only from 2027-01-01"},
        source_inactive_rules={"X": rule},
    )
    findings = lint_source_governance(resolved, {"FUTURE": {"status": "CURRENT_NORM", "jurisdiction": "RU", "effective_from": "2027-01-01"}})
    assert len(findings) == 1
    assert findings[0].meta["problem"] == "enabled_rule_source_inapplicable"


def test_profile_disabled_rule_is_not_reported_as_source_gap():
    resolved = ResolvedProfile(
        name="contractual",
        active_rules={},
        inactive_rules={"X": "disabled by profile"},
    )
    assert lint_source_governance(resolved, {}) == []


def test_missing_source_metadata_is_hard_gate():
    resolved = ResolvedProfile(name="contractual", active_rules={"X": {"source_ids": ["MISSING"]}})
    findings = lint_source_governance(resolved, {})
    assert len(findings) == 1
    assert findings[0].meta["problem"] == "missing_source_metadata"


def test_no_applicable_registered_source_is_hard_gate():
    resolved = ResolvedProfile(name="contractual", active_rules={"X": {"source_ids": ["PENDING"]}})
    sources = {"PENDING": {"status": "PENDING_CHANGE", "jurisdiction": "RU"}}
    findings = lint_source_governance(resolved, sources, document_date=date(2026, 8, 29))
    assert len(findings) == 1
    assert findings[0].meta["problem"] == "no_applicable_source"
