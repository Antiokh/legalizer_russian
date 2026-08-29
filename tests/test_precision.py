from legalizer.linters.precision import lint_vague_time_references


def test_vague_deadline_is_reviewed():
    findings = lint_vague_time_references("Оплата производится в ближайшее время после подписания акта.")
    assert len(findings) == 1
    assert findings[0].rule_id == "LDB-009"


def test_exact_deadline_passes():
    assert lint_vague_time_references("Оплата производится в течение 5 рабочих дней после подписания акта.") == []


def test_several_days_is_reviewed():
    findings = lint_vague_time_references("Ответ будет направлен в течение нескольких дней.")
    assert len(findings) == 1
