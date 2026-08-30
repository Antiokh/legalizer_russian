from legalizer.linters.deadlines import (
    lint_relative_deadline_anchors,
    relative_deadline_occurrences,
)


def test_relative_deadline_without_local_anchor_is_reviewed():
    text = "Заказчик обязан оплатить услуги в течение 5 рабочих дней.\n"
    findings = lint_relative_deadline_anchors(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "LDB-016"
    assert findings[0].severity == "REVIEW"
    assert findings[0].meta["deadline"].casefold() == "в течение 5 рабочих дней"


def test_deadline_with_date_anchor_passes():
    text = "Заказчик обязан оплатить услуги в течение 5 рабочих дней с даты получения счёта.\n"
    deadlines = relative_deadline_occurrences(text)
    assert len(deadlines) == 1
    assert deadlines[0].anchor_text is not None
    assert deadlines[0].anchor_text.casefold() == "с даты"
    assert lint_relative_deadline_anchors(text) == []


def test_deadline_with_after_anchor_passes():
    text = "Исполнитель направляет акт в течение 3 дней после завершения работ.\n"
    assert lint_relative_deadline_anchors(text) == []


def test_deadline_with_anchor_before_duration_passes():
    text = "Со дня получения акта Заказчик вправе направить замечания в течение 5 дней.\n"
    deadlines = relative_deadline_occurrences(text)
    assert deadlines[0].anchor_text is not None
    assert deadlines[0].anchor_text.casefold() == "со дня"
    assert lint_relative_deadline_anchors(text) == []


def test_not_later_than_duration_without_anchor_is_reviewed():
    text = "Уведомление направляется не позднее чем за 10 календарных дней.\n"
    findings = lint_relative_deadline_anchors(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "LDB-016"


def test_not_later_than_duration_with_before_anchor_passes():
    text = "Уведомление направляется не позднее чем за 10 календарных дней до проведения собрания.\n"
    assert lint_relative_deadline_anchors(text) == []


def test_parenthesized_spelled_out_amount_is_supported():
    text = (
        "Отгрузка осуществляется в течение 5 (Пяти) банковских дней "
        "с даты зачисления оплаты.\n"
    )
    deadlines = relative_deadline_occurrences(text)
    assert len(deadlines) == 1
    assert deadlines[0].anchor_text is not None
    assert lint_relative_deadline_anchors(text) == []


def test_absolute_date_is_not_treated_as_relative_duration():
    text = "Оплата производится не позднее 15 сентября 2026 года.\n"
    assert relative_deadline_occurrences(text) == []
