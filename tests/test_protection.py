from legalizer.config import load_profiles, load_rules, load_sources
from legalizer.protection import collect_protected_spans
from legalizer.resolver import resolve_profile


def _resolved(profile: str):
    return resolve_profile(profile, load_rules(), load_profiles(), load_sources())


def test_contractual_defined_terms_are_located_and_protected():
    text = (
        "ООО «Альфа» (далее — Заказчик) заключает договор.\n"
        "Заказчик передаёт материалы Исполнителю.\n"
    )
    result = collect_protected_spans(text, _resolved("contractual"))
    protected = [span for span in result.spans if span.kind == "defined_term"]
    assert [span.text for span in protected] == ["Заказчик", "Заказчик"]
    assert all(span.meta["canonical"] == "Заказчик" for span in protected)
    assert "generic_synonymize_repetition" in result.disabled_rules_on_spans


def test_unimplemented_protection_classes_stay_visible():
    result = collect_protected_spans("Текст договора.", _resolved("contractual"))
    assert "party_names" in result.unresolved_classes
    assert "obligation_modality" in result.unresolved_classes


def test_profile_without_defined_term_protection_does_not_create_spans():
    profiles = {"plain": {"enable": []}}
    resolved = resolve_profile("plain", load_rules(), profiles, load_sources())
    result = collect_protected_spans("ООО «Альфа» (далее — Заказчик). Заказчик платит.", resolved)
    assert result.spans == []
