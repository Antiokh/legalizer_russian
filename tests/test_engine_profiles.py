from datetime import date

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


def test_source_inapplicable_enabled_rule_is_not_silent_pass():
    rules = {
        "DOC-P01": {
            "title": "source governance",
            "scope": ["contractual"],
            "level": "source-governance",
            "basis": "PROJECT_DERIVED",
            "confidence": "high",
            "severity": "HARD_GATE",
            "source_status": "PROJECT_DERIVED",
        },
        "X": {
            "title": "future rule",
            "scope": ["contractual"],
            "level": "document",
            "basis": "SOURCE_DIRECT",
            "confidence": "high",
            "severity": "REVIEW",
            "source_ids": ["FUTURE"],
        },
    }
    profiles = {"contractual": {"enable": ["DOC-P01", "X"]}}
    sources = {
        "FUTURE": {
            "status": "CURRENT_NORM",
            "jurisdiction": "RU",
            "effective_from": "2027-01-01",
        }
    }
    resolved, findings = check_text(
        "Текст документа.\n",
        profile_name="contractual",
        rules=rules,
        profiles=profiles,
        sources=sources,
        document_date=date(2026, 8, 29),
    )
    assert "X" not in resolved.active_rules
    assert "X" in resolved.source_inactive_rules
    assert any(
        f.rule_id == "DOC-P01" and f.meta.get("affected_rule") == "X" and f.severity == "HARD_GATE"
        for f in findings
    )
