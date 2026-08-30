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


def test_contract_party_names_and_modality_are_located_and_protected():
    text = (
        'ООО «Альфа», именуемое в дальнейшем «Заказчик», заключает договор.\n'
        'Заказчик обязан оплатить услуги и вправе запросить отчёт.\n'
    )
    result = collect_protected_spans(text, _resolved("contractual"))
    party_spans = [span for span in result.spans if span.kind == "party_name"]
    modality_spans = [span for span in result.spans if span.kind == "legal_modality"]
    assert [span.text for span in party_spans] == ["Заказчик", "Заказчик"]
    assert [(span.text, span.meta["modality"]) for span in modality_spans] == [
        ("обязан", "obligation"),
        ("вправе", "right"),
    ]
    assert "party_names" not in result.unresolved_classes
    assert "obligation_modality" not in result.unresolved_classes
    assert "generic_modality_simplification" in result.disabled_rules_on_spans


def test_contract_condition_and_exception_markers_are_protected():
    text = (
        "В случае просрочки Заказчик обязан уплатить неустойку, "
        "за исключением случаев форс-мажора.\n"
    )
    result = collect_protected_spans(text, _resolved("contractual"))
    spans = [
        (span.kind, span.text)
        for span in result.spans
        if span.kind in {"condition_scope_marker", "exception_scope_marker"}
    ]
    assert spans == [
        ("condition_scope_marker", "В случае"),
        ("exception_scope_marker", "за исключением"),
    ]
    assert "condition_scope_marker" not in result.unresolved_classes
    assert "exception_scope_marker" not in result.unresolved_classes


def test_relative_deadline_and_anchor_are_protected():
    text = (
        "Заказчик обязан оплатить услуги в течение 5 рабочих дней "
        "с даты получения счёта.\n"
    )
    result = collect_protected_spans(text, _resolved("contractual"))
    deadlines = [span for span in result.spans if span.kind == "relative_deadline"]
    anchors = [span for span in result.spans if span.kind == "deadline_anchor"]
    assert [span.text for span in deadlines] == ["в течение 5 рабочих дней"]
    assert [span.text.casefold() for span in anchors] == ["с даты"]
    assert deadlines[0].meta["has_local_anchor"] is True
    assert "relative_deadline" not in result.unresolved_classes
    assert "deadline_anchor" not in result.unresolved_classes
    assert "generic_time_simplification" in result.disabled_rules_on_spans


def test_order_directive_infinitives_are_located_and_protected():
    text = (
        "ПРИКАЗЫВАЮ:\n"
        "1. Директору подготовить предложения.\n"
        "2. Бухгалтерии открыть счёт.\n"
    )
    result = collect_protected_spans(text, _resolved("official-admin/order"))
    protected = [span for span in result.spans if span.kind == "directive_infinitive"]
    assert [span.text for span in protected] == ["подготовить", "открыть"]
    assert [span.meta["directive"] for span in protected] == ["1", "2"]
    assert "generic_imperative_rewrite" in result.disabled_rules_on_spans
    assert "directive_infinitive" not in result.unresolved_classes


def test_still_unimplemented_protection_classes_stay_visible():
    result = collect_protected_spans("Текст договора.", _resolved("contractual"))
    assert "cross_references" in result.unresolved_classes
    assert "functional_long_syntax" in result.unresolved_classes


def test_profile_without_protection_does_not_create_spans():
    profiles = {"plain": {"enable": []}}
    resolved = resolve_profile("plain", load_rules(), profiles, load_sources())
    result = collect_protected_spans(
        "ООО «Альфа» (далее — Заказчик). Заказчик обязан платить.", resolved
    )
    assert result.spans == []
