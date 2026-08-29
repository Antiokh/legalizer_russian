from legalizer.linters.cross_references import lint_internal_references


def test_existing_internal_point_reference_passes():
    text = (
        "## 4. Ответственность\n\n"
        "### 4.1. Неустойка\n\n"
        "Порядок расчёта установлен в пункте 4.1 настоящего Договора.\n"
    )
    assert lint_internal_references(text) == []


def test_missing_internal_point_reference_is_hard_gate():
    text = (
        "## 4. Ответственность\n\n"
        "### 4.1. Неустойка\n\n"
        "Порядок расчёта установлен в пункте 4.7 настоящего Договора.\n"
    )
    findings = lint_internal_references(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "DOC-N04"
    assert findings[0].severity == "HARD_GATE"
    assert findings[0].meta["target"] == "4.7"


def test_external_reference_is_not_treated_as_internal():
    text = "Требование предусмотрено пунктом 4 соглашения от 10 августа 2026 года.\n"
    assert lint_internal_references(text) == []


def test_missing_appendix_reference_is_detected():
    text = "Условия указаны в приложении 3 к настоящему Договору.\n"
    findings = lint_internal_references(text)
    assert len(findings) == 1
    assert findings[0].meta["reference_kind"] == "appendix"
