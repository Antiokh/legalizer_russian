from legalizer.linters.admin_orders import (
    directive_infinitive_occurrences,
    lint_order_directive_infinitives,
)


def test_numbered_order_directives_with_infinitives_pass():
    text = (
        "ПРИКАЗЫВАЮ:\n"
        "1. Директору управления подготовить предложения по составу группы.\n"
        "2. Бухгалтерии открыть отдельный расчётный счёт.\n"
        "3. Контроль за исполнением приказа возложить на заместителя директора.\n"
    )
    assert lint_order_directive_infinitives(text) == []
    verbs = [match.group(0) for _, match in directive_infinitive_occurrences(text)]
    assert verbs == ["подготовить", "открыть", "возложить"]


def test_numbered_order_directive_without_action_is_reviewed():
    text = (
        "ПРИКАЗЫВАЮ:\n"
        "1. Директору управления предложения по составу рабочей группы.\n"
        "2. Бухгалтерии открыть отдельный расчётный счёт.\n"
    )
    findings = lint_order_directive_infinitives(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "ADM-ORDER-001"
    assert findings[0].meta["directive"] == "1"


def test_numbered_text_without_order_marker_is_not_treated_as_order():
    text = "1. Общие положения.\n2. Область применения.\n"
    assert lint_order_directive_infinitives(text) == []
