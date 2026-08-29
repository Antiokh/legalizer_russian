from legalizer.linters.legislation import lint_legislation_hierarchy, lint_legislation_preamble


def test_legislation_preamble_with_goal_passes():
    text = (
        "# Проект федерального закона\n\n"
        "Преамбула: Настоящий Федеральный закон направлен на создание единых условий регулирования.\n\n"
        "Статья 1. Предмет регулирования\n"
    )
    assert lint_legislation_preamble(text) == []


def test_legislation_preamble_with_obligation_is_reviewed():
    text = (
        "Преамбула: Организации обязаны представить сведения не позднее 1 марта.\n\n"
        "Статья 1. Общие положения\n"
    )
    findings = lint_legislation_preamble(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "DOC-N01"
    assert findings[0].meta["signal"] == "directive"


def test_legislation_preamble_with_definition_is_reviewed():
    text = (
        "Преамбула\n"
        "Для целей настоящего Федерального закона под оператором понимается юридическое лицо.\n\n"
        "Статья 1. Общие положения\n"
    )
    findings = lint_legislation_preamble(text)
    assert len(findings) == 1
    assert findings[0].meta["signal"] == "definition"


def test_section_without_chapter_is_reviewed():
    text = "Раздел I. Общие положения\n\nСтатья 1. Предмет регулирования\n"
    findings = lint_legislation_hierarchy(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "DOC-N02"


def test_section_with_chapter_passes_basic_hierarchy_check():
    text = "Раздел I. Общие положения\n\nГлава 1. Основы\n\nСтатья 1. Предмет регулирования\n"
    assert lint_legislation_hierarchy(text) == []
