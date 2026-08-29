from datetime import date

from legalizer.config import load_rules, load_sources
from legalizer.source_policy import source_applicability, validate_source_registry


def test_pending_source_is_never_active():
    source = load_sources()["DOC-ROSARCHIVE-91-2026"]
    ok, reason = source_applicability(source, document_date=date(2026, 8, 29), jurisdiction="RU")
    assert ok is False
    assert "not active" in reason


def test_gost_is_not_active_before_effective_date():
    source = load_sources()["DOC-GOST-2025"]
    ok, reason = source_applicability(source, document_date=date(2025, 8, 17), jurisdiction="RU")
    assert ok is False
    assert "2025-08-18" in reason


def test_registry_covers_current_rules():
    assert validate_source_registry(load_rules(), load_sources()) == []
