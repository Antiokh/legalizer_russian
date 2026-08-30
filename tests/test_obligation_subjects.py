from legalizer.linters.obligations import (
    implicit_obligation_subject_occurrences,
    lint_obligation_subjects,
)


_PARTIES = (
    'ООО «Альфа», именуемое в дальнейшем «Заказчик», и '
    'ООО «Бета», именуемое в дальнейшем «Исполнитель», заключили договор.\n'
)


def test_explicit_party_subject_passes():
    text = _PARTIES + "Заказчик обязан оплатить услуги.\n"
    assert lint_obligation_subjects(text) == []


def test_collective_parties_subject_passes():
    text = _PARTIES + "Стороны обязаны уведомлять друг друга об изменении реквизитов.\n"
    assert lint_obligation_subjects(text) == []


def test_obvious_missing_local_subject_is_reviewed():
    text = _PARTIES + "Обязан оплатить услуги в течение пяти дней.\n"
    findings = lint_obligation_subjects(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "CTR-002"
    assert findings[0].severity == "REVIEW"
    assert findings[0].meta["modality"].casefold() == "обязан"


def test_condition_prefix_without_visible_party_is_reviewed():
    text = _PARTIES + "В случае просрочки, обязан уплатить неустойку.\n"
    occurrences = implicit_obligation_subject_occurrences(text)
    assert len(occurrences) == 1
    assert occurrences[0].text.casefold() == "обязан"


def test_dolzhen_family_is_not_used_for_subject_inference():
    text = _PARTIES + "Документы должны быть переданы в электронной форме.\n"
    assert lint_obligation_subjects(text) == []


def test_no_explicit_party_aliases_means_no_subject_inference():
    text = "Покупатель обязан оплатить товар. Обязан также принять товар.\n"
    assert lint_obligation_subjects(text) == []
