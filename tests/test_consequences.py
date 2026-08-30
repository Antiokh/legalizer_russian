from legalizer.linters.consequences import (
    breach_trigger_occurrences,
    legal_consequence_occurrences,
    lint_breach_consequence_links,
)


def test_breach_and_penalty_in_responsibility_section_pass():
    text = (
        "5. Ответственность сторон\n"
        "5.1. В случае просрочки Заказчик уплачивает неустойку 0,1 процента.\n"
    )
    assert lint_breach_consequence_links(text) == []
    assert [item.text.casefold() for item in breach_trigger_occurrences(text)] == [
        "в случае просрочки"
    ]
    consequences = legal_consequence_occurrences(text)
    assert any(item.kind == "penalty" and item.text.casefold() == "неустойку" for item in consequences)


def test_generic_liability_formula_before_breach_passes():
    text = (
        "# Ответственность сторон\n"
        "Стороны несут ответственность за неисполнение обязательств по договору.\n"
    )
    assert lint_breach_consequence_links(text) == []


def test_breach_without_local_consequence_in_responsibility_section_is_reviewed():
    text = (
        "5. Ответственность сторон\n"
        "5.1. За нарушение срока передачи результата работ.\n"
    )
    findings = lint_breach_consequence_links(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "CTR-004"
    assert findings[0].severity == "REVIEW"
    assert findings[0].meta["breach"].casefold() == "за нарушение"


def test_adjacent_numbered_clauses_do_not_share_consequences():
    text = (
        "5. Ответственность сторон\n"
        "5.1. В случае просрочки оплаты Заказчик уплачивает неустойку.\n"
        "5.2. За нарушение срока передачи результата работ Исполнителем.\n"
    )
    findings = lint_breach_consequence_links(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "CTR-004"
    assert findings[0].meta["breach"].casefold() == "за нарушение"


def test_nested_clause_without_terminal_punctuation_stays_in_numbered_section():
    text = (
        "5. Ответственность сторон\n"
        "5.1 В случае просрочки оплаты Заказчик уплачивает штраф\n"
        "5.2 За нарушение срока передачи результата работ Исполнителем\n"
        "6. Срок действия договора\n"
    )
    findings = lint_breach_consequence_links(text)
    assert len(findings) == 1
    assert findings[0].meta["breach"].casefold() == "за нарушение"


def test_markdown_subheading_does_not_end_responsibility_section():
    text = (
        "## Ответственность сторон\n"
        "### Просрочка\n"
        "В случае просрочки Заказчик уплачивает пеню.\n"
        "## Срок действия\n"
        "В случае просрочки продления Стороны направляют уведомление.\n"
    )
    assert lint_breach_consequence_links(text) == []


def test_breach_outside_responsibility_section_is_not_forced_into_sanction():
    text = "В случае просрочки Заказчик обязан уведомить Исполнителя.\n"
    assert lint_breach_consequence_links(text) == []


def test_damages_and_remedy_are_recognized_as_consequences():
    text = (
        "Ответственность\n"
        "При нарушении обязательства Исполнитель обязан возместить убытки.\n\n"
        "В случае неисполнения Заказчик вправе расторгнуть договор.\n"
    )
    consequences = legal_consequence_occurrences(text)
    kinds = {item.kind for item in consequences}
    assert "damages" in kinds
    assert "remedy" in kinds
    assert lint_breach_consequence_links(text) == []


def test_next_numbered_section_ends_responsibility_scope():
    text = (
        "5. Ответственность сторон\n"
        "5.1. В случае просрочки Заказчик уплачивает штраф.\n"
        "6. Срок действия договора\n"
        "В случае просрочки продления Стороны направляют уведомление.\n"
    )
    assert lint_breach_consequence_links(text) == []
