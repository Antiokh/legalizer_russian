from legalizer.linters.contract_parties import (
    extract_party_aliases,
    lint_party_aliases,
    party_alias_occurrences,
)


def test_explicit_contract_party_aliases_are_extracted_and_reused():
    text = (
        'ООО «Альфа», именуемое в дальнейшем «Заказчик», с одной стороны, '
        'и ООО «Бета», именуемое в дальнейшем «Исполнитель», с другой стороны, '
        'заключили договор.\n'
        'Заказчик передаёт данные, Исполнитель оказывает услуги.\n'
    )
    assert [party.alias for party in extract_party_aliases(text)] == ["Заказчик", "Исполнитель"]
    assert lint_party_aliases(text) == []
    occurrences = [(party.alias, match.group(0)) for party, match in party_alias_occurrences(text)]
    assert occurrences == [
        ("Заказчик", "Заказчик"),
        ("Исполнитель", "Исполнитель"),
        ("Заказчик", "Заказчик"),
        ("Исполнитель", "Исполнитель"),
    ]


def test_party_alias_used_before_intro_is_reviewed():
    text = (
        'Заказчик передаёт материалы. '
        'ООО «Альфа», именуемое в дальнейшем «Заказчик», подписывает договор.\n'
    )
    findings = lint_party_aliases(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "CTR-001"
    assert findings[0].meta["alias"] == "Заказчик"


def test_same_party_alias_introduced_twice_is_reviewed():
    text = (
        'ООО «Альфа», именуемое в дальнейшем «Заказчик», и '
        'ООО «Бета», именуемое в дальнейшем «Заказчик», заключили договор.\n'
    )
    findings = lint_party_aliases(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "CTR-001"
    assert findings[0].meta["first_definition_line"] == 1


def test_non_contractual_dalee_phrase_is_not_party_intro():
    text = 'ООО «Альфа» (далее — Компания) действует на основании устава.\n'
    assert extract_party_aliases(text) == []
