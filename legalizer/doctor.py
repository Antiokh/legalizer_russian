from __future__ import annotations

from dataclasses import asdict, dataclass

from .registry import implemented_rule_ids
from .resolver import ResolverError, flatten_profile
from .source_policy import parse_iso_date, validate_source_registry


ALLOWED_SOURCE_STATUSES = {
    "CURRENT_NORM",
    "PENDING_CHANGE",
    "METHODICAL",
    "DOMAIN_CONVENTION",
    "HISTORICAL",
    "PROJECT_DERIVED",
}


@dataclass(slots=True)
class DoctorIssue:
    level: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class DoctorReport:
    issues: list[DoctorIssue]
    implemented_rules: set[str]
    manual_rules: set[str]

    @property
    def errors(self) -> list[DoctorIssue]:
        return [issue for issue in self.issues if issue.level == "ERROR"]

    @property
    def warnings(self) -> list[DoctorIssue]:
        return [issue for issue in self.issues if issue.level == "WARNING"]

    def to_dict(self) -> dict[str, object]:
        return {
            "issues": [issue.to_dict() for issue in self.issues],
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "implemented_rules": sorted(self.implemented_rules),
            "manual_rules": sorted(self.manual_rules),
        }


def run_doctor(
    rules: dict[str, dict],
    profiles: dict[str, dict],
    sources: dict[str, dict],
) -> DoctorReport:
    issues: list[DoctorIssue] = []

    for problem in validate_source_registry(rules, sources):
        issues.append(DoctorIssue("ERROR", "SOURCE_REGISTRY", problem))

    for source_id, source in sources.items():
        status = source.get("status")
        if status not in ALLOWED_SOURCE_STATUSES:
            issues.append(
                DoctorIssue(
                    "ERROR",
                    "SOURCE_STATUS",
                    f"{source_id}: unknown source status {status!r}",
                )
            )
        try:
            effective_from = parse_iso_date(source.get("effective_from"))
            effective_to = parse_iso_date(source.get("effective_to"))
        except (TypeError, ValueError) as exc:
            issues.append(DoctorIssue("ERROR", "SOURCE_DATE", f"{source_id}: {exc}"))
            continue
        if effective_from and effective_to and effective_from > effective_to:
            issues.append(
                DoctorIssue(
                    "ERROR",
                    "SOURCE_DATE_RANGE",
                    f"{source_id}: effective_from is after effective_to",
                )
            )

    for profile_name in profiles:
        try:
            flattened = flatten_profile(profile_name, profiles)
        except ResolverError as exc:
            issues.append(DoctorIssue("ERROR", "PROFILE_INHERITANCE", str(exc)))
            continue

        for rule_id in flattened.get("enable", []) or []:
            if rule_id not in rules:
                issues.append(
                    DoctorIssue(
                        "ERROR",
                        "PROFILE_UNKNOWN_RULE",
                        f"{profile_name}: enables unknown rule {rule_id}",
                    )
                )
        for rule_id in (flattened.get("override", {}) or {}):
            if rule_id not in rules:
                issues.append(
                    DoctorIssue(
                        "ERROR",
                        "PROFILE_UNKNOWN_OVERRIDE",
                        f"{profile_name}: overrides unknown rule {rule_id}",
                    )
                )

    implemented = implemented_rule_ids()
    for rule_id in implemented - set(rules):
        issues.append(
            DoctorIssue(
                "ERROR",
                "ORPHAN_IMPLEMENTATION",
                f"Runtime implementation exists for missing rule {rule_id}",
            )
        )

    manual = set(rules) - implemented
    return DoctorReport(issues=issues, implemented_rules=implemented, manual_rules=manual)
