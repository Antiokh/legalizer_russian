from legalizer.config import load_profiles, load_rules, load_sources
from legalizer.resolver import resolve_profile


def _resolve(name: str):
    return resolve_profile(name, load_rules(), load_profiles(), load_sources())


def test_contractual_profile_enables_party_modality_and_scope_rules():
    resolved = _resolve("contractual")
    assert "CTR-001" in resolved.active_rules
    assert "LDB-008" in resolved.active_rules
    assert "LDB-015" in resolved.active_rules
    assert "party_names" in resolved.protected_classes
    assert "obligation_modality" in resolved.protected_classes
    assert "condition_scope_marker" in resolved.protected_classes
    assert "exception_scope_marker" in resolved.protected_classes


def test_normative_profile_gets_scope_review_but_not_contract_party_rule():
    resolved = _resolve("normative")
    assert "LDB-015" in resolved.active_rules
    assert "CTR-001" not in resolved.active_rules
    assert "legal_modality" in resolved.protected_classes
    assert "condition_scope_marker" in resolved.protected_classes
    assert "exception_scope_marker" in resolved.protected_classes


def test_plain_official_admin_does_not_get_contract_scope_rule():
    resolved = _resolve("official-admin")
    assert "CTR-001" not in resolved.active_rules
    assert "LDB-015" not in resolved.active_rules
    assert "legal_modality" in resolved.protected_classes
