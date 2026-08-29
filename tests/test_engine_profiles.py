from legalizer.config import load_profiles, load_rules, load_sources
from legalizer.engine import check_text


def _check(text: str, profile: str):
    return check_text(
        text,
        profile_name=profile,
        rules=load_rules(),
        profiles=load_profiles(),
        sources=load_sources(),
    )[1]


def test_contract_preamble_does_not_use_legislation_rule():
    text = "Преамбула: Заказчик обязан передать материалы Исполнителю.\n"
    findings = _check(text, "contractual")
    assert all(f.rule_id != "DOC-N01" for f in findings)


def test_legislation_preamble_uses_legislation_rule():
    text = "Преамбула: Организации обязаны представить сведения.\n\nСтатья 1. Общие положения\n"
    findings = _check(text, "normative/legislation")
    assert any(f.rule_id == "DOC-N01" for f in findings)


def test_vague_time_rule_runs_in_contractual_profile():
    findings = _check("Оплата производится в ближайшее время после подписания акта.\n", "contractual")
    assert any(f.rule_id == "LDB-009" for f in findings)


def test_broken_internal_reference_is_hard_gate_in_contract():
    text = "## 4. Ответственность\n\nПорядок указан в пункте 4.7 настоящего Договора.\n"
    findings = _check(text, "contractual")
    assert any(f.rule_id == "DOC-N04" and f.severity == "HARD_GATE" for f in findings)
