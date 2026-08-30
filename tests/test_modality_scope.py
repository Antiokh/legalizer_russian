from legalizer.linters.modality import modality_occurrences
from legalizer.linters.scope import lint_condition_exception_scope, scope_marker_occurrences


def test_strong_legal_modality_is_classified_without_mozhet():
    text = (
        "Заказчик обязан оплатить услуги. "
        "Исполнитель вправе приостановить работы. "
        "Передача пароля запрещается. "
        "Сторона может направить уведомление."
    )
    occurrences = modality_occurrences(text)
    assert [(item.text, item.kind) for item in occurrences] == [
        ("обязан", "obligation"),
        ("вправе", "right"),
        ("запрещается", "prohibition"),
    ]


def test_negative_right_is_not_double_counted():
    text = "Исполнитель не вправе передавать доступ третьим лицам."
    occurrences = modality_occurrences(text)
    assert len(occurrences) == 1
    assert occurrences[0].text == "не вправе"
    assert occurrences[0].kind == "prohibition"


def test_unless_otherwise_is_exception_not_nested_condition():
    text = "Если иное не предусмотрено договором, Заказчик обязан уведомить Исполнителя."
    markers = scope_marker_occurrences(text)
    assert [(item.kind, item.form) for item in markers] == [
        ("exception", "unless_otherwise")
    ]


def test_condition_modality_exception_cluster_is_reviewed():
    text = (
        "В случае просрочки Заказчик обязан уплатить неустойку, "
        "за исключением случаев, когда просрочка вызвана действиями Исполнителя."
    )
    findings = lint_condition_exception_scope(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "LDB-015"
    assert findings[0].severity == "REVIEW"
    assert findings[0].meta["condition"] == "В случае"
    assert findings[0].meta["exceptions"] == ["за исключением"]


def test_simple_condition_with_one_obligation_does_not_trigger_scope_review():
    text = "Если Заказчик получил акт, он обязан подписать его в течение пяти дней."
    assert lint_condition_exception_scope(text) == []
