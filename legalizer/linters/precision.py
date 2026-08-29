from __future__ import annotations

import re

from ..model import Finding
from ..text import line_column, line_excerpt


VAGUE_TIME_RE = re.compile(
    r"\b(?:"
    r"в\s+ближайшее\s+время|"
    r"в\s+скором\s+времени|"
    r"через\s+некоторое\s+время|"
    r"в\s+ближайшие\s+(?:дни|недели|месяцы)|"
    r"в\s+течение\s+нескольких\s+(?:дней|недель|месяцев)"
    r")\b",
    re.IGNORECASE,
)


def lint_vague_time_references(text: str, severity: str = "REVIEW") -> list[Finding]:
    findings: list[Finding] = []
    for match in VAGUE_TIME_RE.finditer(text):
        line, column = line_column(text, match.start())
        findings.append(
            Finding(
                rule_id="LDB-009",
                severity=severity,
                message=(
                    "Неопределённое указание времени: проверьте, нужен ли здесь точный срок "
                    "или однозначно вычисляемая точка отсчёта."
                ),
                line=line,
                column=column,
                evidence=line_excerpt(text, match.start()),
                meta={"phrase": match.group(0)},
            )
        )
    return findings
