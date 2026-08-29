from legalizer.linters.defined_terms import lint_defined_terms


def test_defined_term_after_first_use_is_reviewed():
    text = (
        "ДРР рассматривает обращения.\n"
        "Департамент регионального развития (далее — ДРР) направляет ответы.\n"
    )
    findings = lint_defined_terms(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "DOC-M05"
    assert findings[0].line == 1


def test_defined_term_introduced_before_use_passes():
    text = (
        "Департамент регионального развития (далее — ДРР) рассматривает обращения.\n"
        "ДРР направляет ответы.\n"
    )
    assert lint_defined_terms(text) == []


def test_reintroduced_alias_is_reviewed():
    text = (
        "ООО «Альфа» (далее — Заказчик) заключает договор.\n"
        "ООО «Бета» (далее — Заказчик) получает документы.\n"
    )
    findings = lint_defined_terms(text)
    assert len(findings) == 1
    assert "вводится повторно" in findings[0].message
