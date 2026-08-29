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
        "4. Секретарю внести изменения в реестр.\n"
    )
    assert lint_order_directive_infinitives(text) == []
    verbs = [match.group(0) for _, match in directive_infinitive_occurrences(text)]
    assert verbs == ["подготовить", "открыть", "возложить", "внести"]


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


def test_nouns_ending_like_infinitives_do_not_fake_an_action():
    text = (
        "ПРИКАЗЫВАЮ:\n"
        "1. Отделу печать организации и пути передачи документов.\n"
    )
    findings = lint_order_directive_infinitives(text)
    assert len(findings) == 1
    assert findings[0].meta["directive"] == "1"


def test_attached_document_numbering_is_outside_order_directives():
    text = (
        "ПРИКАЗЫВАЮ:\n"
        "1. Утвердить Положение согласно приложению.\n\n"
        "Приложение № 1\n"
        "1. Общие положения.\n"
        "2. Термины и определения.\n"
    )
    assert lint_order_directive_infinitives(text) == []


def test_numbered_text_without_order_marker_is_not_treated_as_order():
    text = "1. Общие положения.\n2. Область применения.\n"
    assert lint_order_directive_infinitives(text) == []
