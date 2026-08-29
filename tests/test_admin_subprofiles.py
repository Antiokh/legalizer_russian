from legalizer.config import load_profiles, load_rules, load_sources
from legalizer.resolver import resolve_profile


def _resolve(name: str):
    return resolve_profile(name, load_rules(), load_profiles(), load_sources())


def test_letter_profile_gets_letter_rule_not_order_rule():
    resolved = _resolve("official-admin/letter")
    assert "ADM-LETTER-001" in resolved.active_rules
    assert "ADM-ORDER-001" not in resolved.active_rules
    assert "ADM-ACT-001" not in resolved.active_rules


def test_order_profile_gets_order_rule_and_directive_protection():
    resolved = _resolve("official-admin/order")
    assert "ADM-ORDER-001" in resolved.active_rules
    assert "LDB-014" in resolved.active_rules
    assert "ADM-LETTER-001" not in resolved.active_rules
    assert "directive_infinitive" in resolved.protected_classes
    assert "generic_imperative_rewrite" in resolved.disabled_for_protected_spans


def test_act_profile_gets_act_rule_only():
    resolved = _resolve("official-admin/act")
    assert "ADM-ACT-001" in resolved.active_rules
    assert "ADM-ORDER-001" not in resolved.active_rules
    assert "ADM-LETTER-001" not in resolved.active_rules


def test_contractual_profile_uses_refined_word_order_rules_without_admin_rules():
    resolved = _resolve("contractual")
    assert "LDB-010" in resolved.active_rules
    assert "LDB-012" in resolved.active_rules
    assert "LDB-013" in resolved.active_rules
    assert "ADM-ORDER-001" not in resolved.active_rules
