from __future__ import annotations

import re
from collections import defaultdict

from ..model import Finding
from ..text import line_column, line_excerpt


POINT_TARGET_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?P<num>\d+(?:\.\d+)*)\.?\s+\S",
    re.MULTILINE,
)
ARTICLE_TARGET_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?[Сс]татья\s+(?P<num>\d+(?:\.\d+)*)\b",
    re.MULTILINE,
)
APP_TARGET_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?[Пп]риложение\s*(?:№\s*)?(?P<num>\d+)\b",
    re.MULTILINE,
)

POINT_REF_RE = re.compile(
    r"\b(?:пункт(?:е|а|у|ом)?|п\.)\s+(?P<num>\d+(?:\.\d+)*)\b"
    r"(?=\.?[^\n.]{0,90}\bнастоящ(?:его|ей|ем|ему|ую|ий|ая|ее)\b)",
    re.IGNORECASE,
)
ARTICLE_REF_RE = re.compile(
    r"\bстать(?:е|и|ю|ёй|ей)\s+(?P<num>\d+(?:\.\d+)*)\b"
    r"(?=\.?[^\n.]{0,90}\bнастоящ(?:его|ей|ем|ему|ую|ий|ая|ее)\b)",
    re.IGNORECASE,
)
APP_REF_RE = re.compile(
    r"\bприложени(?:е|я|ю|и|ем)\s*(?:№\s*)?(?P<num>\d+)\b"
    r"(?=[^\n.]{0,90}\b(?:к\s+)?настоящ(?:ему|его|ей|ем|ую|ий|ая|ее)\b)",
    re.IGNORECASE,
)


def extract_targets(text: str) -> dict[str, set[str]]:
    targets: dict[str, set[str]] = defaultdict(set)
    for match in POINT_TARGET_RE.finditer(text):
        targets["point"].add(match.group("num"))
    for match in ARTICLE_TARGET_RE.finditer(text):
        targets["article"].add(match.group("num"))
    for match in APP_TARGET_RE.finditer(text):
        targets["appendix"].add(match.group("num"))
    return targets


def lint_internal_references(text: str, severity: str = "HARD_GATE") -> list[Finding]:
    targets = extract_targets(text)
    findings: list[Finding] = []
    specs = [
        ("point", "пункт", POINT_REF_RE),
        ("article", "статью", ARTICLE_REF_RE),
        ("appendix", "приложение", APP_REF_RE),
    ]

    for kind, label, pattern in specs:
        for match in pattern.finditer(text):
            number = match.group("num")
            if number in targets.get(kind, set()):
                continue
            line, column = line_column(text, match.start("num"))
            findings.append(
                Finding(
                    rule_id="DOC-N04",
                    severity=severity,
                    message=f"Внутренняя ссылка указывает на отсутствующий {label} {number}.",
                    line=line,
                    column=column,
                    evidence=line_excerpt(text, match.start()),
                    meta={"reference_kind": kind, "target": number, "parser_confidence": "high"},
                )
            )
    return findings
