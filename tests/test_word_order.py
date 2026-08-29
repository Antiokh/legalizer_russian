from legalizer.linters.word_order import lint_instrumental_attachment


def test_stacked_instrumentals_after_nominalization_are_reviewed():
    text = "Признание юридического лица банкротом судом влечёт его ликвидацию.\n"
    findings = lint_instrumental_attachment(text)
    assert len(findings) == 1
    assert findings[0].rule_id == "LDB-012"
    assert findings[0].severity == "REVIEW"
    assert findings[0].meta["first"] == "банкротом"
    assert findings[0].meta["second"] == "судом"


def test_reordered_clear_example_does_not_match_narrow_heuristic():
    text = "Признание судом юридического лица банкротом влечёт его ликвидацию.\n"
    assert lint_instrumental_attachment(text) == []


def test_common_adverb_pair_is_not_reported():
    text = "Решение было принято совсем потом и отражено в протоколе.\n"
    assert lint_instrumental_attachment(text) == []
