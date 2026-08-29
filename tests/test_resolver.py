from datetime import date

from legalizer.config import load_profiles, load_rules, load_sources
from legalizer.resolver import resolve_profile


def test_legislation_inherits_normative_rules():
    rules = load_rules()
    profiles = load_profiles()
    sources = load_sources()
    resolved = resolve_profile("normative/legislation", rules, profiles, sources)

    assert "DOC-M03" in resolved.active_rules
    assert "DOC-N01" in resolved.active_rules
    assert resolved.active_rules["DOC-N01"]["severity"] == "REVIEW"
    assert "legal_modality" in resolved.protected_classes


def test_contractual_exposes_external_conflict_policy():
    resolved = resolve_profile(
        "contractual",
        load_rules(),
        load_profiles(),
        load_sources(),
    )
    assert "generic_synonymize_repetition" in resolved.disabled_for_protected_spans
    assert resolved.external_severity["generic_nominalization"] == "INFO"


def test_rule_with_future_source_is_inactive_for_old_document():
    rules = {
        "X": {
            "title": "future",
            "scope": ["contractual"],
            "level": "document",
            "basis": "SOURCE_DIRECT",
            "confidence": "high",
            "severity": "REVIEW",
            "source_ids": ["DOC-GOST-2025"],
        }
    }
    profiles = {"contractual": {"enable": ["X"]}}
    resolved = resolve_profile(
        "contractual",
        rules,
        profiles,
        load_sources(),
        document_date=date(2024, 1, 1),
    )
    assert "X" not in resolved.active_rules
    assert "effective only from 2025-08-18" in resolved.inactive_rules["X"]
