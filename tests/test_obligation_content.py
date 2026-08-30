from legalizer.linters.obligations import (
    incomplete_obligation_content_occurrences,
    lint_obligation_content,
    obligation_action_occurrences,
)


_PARTIES = (
    'ООО «Альфа», именуемое в дальнейшем «Заказчик», и '
    'ООО «Бета», именуемое в дальнейшем «Исполнитель», заключили договор.\n'
)


def test_explicit_obligation_action_is_detected():
    text = _PARTIES + "Заказчик обязан оплатить услуги.\n"
    actions = obligation_action_occurrences(text)
    assert len(actions) == 1
    assert actions[0].modality.casefold() == "обязан"
    assert actions[0].action.casefold() == "оплатить"
    assert lint_obligation_content(text) == []


def test_nested_infinitive_chain_keeps_first_action():
    text = _PARTIES + "Исполнитель обязуется обеспечить передачу документов.\n"
    actions = obligation_action_occurrences(text)
    assert len(actions) == 1
    assert actions[0].action.casefold() == "обеспечить"


def test_negated_action_is_still_detected():
    text = _PARTIES + "Исполнитель обязан не разглашать конфиденциальную информацию.\n"
    actions = obligation_action_occurrences(text)
    assert len(actions) == 1
    assert actions[0].action.casefold() == "разглашать"
    assert lint_obligation_content(text) == []


def test_explicit_party_obligation_without_action_is_reviewed():
    text = _PARTIES + "Заказчик обязан в течение пяти дней.\n"
    findings = lint_obligation_content(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "CTR-003"
    assert findings[0].severity == "REVIEW"
    assert findings[0].meta["modality"].casefold() == "обязан"


def test_subjectless_obligation_is_left_to_ctr_002_not_duplicated():
    text = _PARTIES + "Обязан оплатить услуги.\n"
    assert incomplete_obligation_content_occurrences(text) == []


def test_no_explicit_party_aliases_means_no_content_inference():
    text = "Покупатель обязан.\n"
    assert lint_obligation_content(text) == []
