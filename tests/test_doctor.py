from legalizer.config import load_profiles, load_rules, load_sources
from legalizer.doctor import run_doctor


def test_repository_configuration_has_no_doctor_errors():
    report = run_doctor(load_rules(), load_profiles(), load_sources())
    assert report.errors == []
    assert "DOC-M05" in report.implemented_rules
    assert "LDB-001" in report.manual_rules


def test_doctor_rejects_unknown_enabled_rule():
    report = run_doctor(
        {"KNOWN": {"source_ids": []}},
        {"x": {"enable": ["MISSING"]}},
        {},
    )
    assert any(issue.code == "PROFILE_UNKNOWN_RULE" for issue in report.errors)


def test_doctor_rejects_unknown_source_status():
    report = run_doctor({}, {}, {"X": {"status": "MAYBE"}})
    assert any(issue.code == "SOURCE_STATUS" for issue in report.errors)
