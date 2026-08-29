from __future__ import annotations

import re
from dataclasses import dataclass

from ..model import Finding
from ..text import line_column, line_excerpt


ORDER_MARKER_RE = re.compile(r"(?im)^\s*ПРИКАЗЫВАЮ\s*:?[ \t]*$")
NUMBERED_DIRECTIVE_RE = re.compile(
    r"(?m)^\s*(?P<num>\d+(?:\.\d+)*)[.)]?\s+(?P<body>\S.*)$"
)
INFINITIVE_RE = re.compile(
    r"\b[А-Яа-яЁё][А-Яа-яЁё-]{2,}(?:ть(?:ся)?|ти(?:сь)?|чь(?:ся)?)\b",
    re.IGNORECASE,
)


@dataclass(slots=True)
class DirectiveParagraph:
    number: str
    start: int
    end: int
    text: str


def extract_order_directives(text: str) -> list[DirectiveParagraph]:
    """Extract numbered directive paragraphs after an explicit ПРИКАЗЫВАЮ marker."""

    marker = ORDER_MARKER_RE.search(text)
    if marker is None:
        return []

    matches = [match for match in NUMBERED_DIRECTIVE_RE.finditer(text, marker.end())]
    directives: list[DirectiveParagraph] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        directives.append(
            DirectiveParagraph(
                number=match.group("num"),
                start=match.start("body"),
                end=end,
                text=text[match.start("body") : end].strip(),
            )
        )
    return directives


def directive_infinitive_occurrences(text: str) -> list[tuple[DirectiveParagraph, re.Match[str]]]:
    """Return infinitive-like action tokens with absolute offsets represented by match wrappers."""

    occurrences: list[tuple[DirectiveParagraph, re.Match[str]]] = []
    for directive in extract_order_directives(text):
        for match in INFINITIVE_RE.finditer(text, directive.start, directive.end):
            occurrences.append((directive, match))
    return occurrences


def lint_order_directive_infinitives(text: str, severity: str = "REVIEW") -> list[Finding]:
    """Review numbered order directives that contain no infinitive-like action."""

    findings: list[Finding] = []
    for directive in extract_order_directives(text):
        if INFINITIVE_RE.search(text, directive.start, directive.end):
            continue
        line, column = line_column(text, directive.start)
        findings.append(
            Finding(
                rule_id="ADM-ORDER-001",
                severity=severity,
                message=(
                    f"В распорядительном пункте {directive.number} после «ПРИКАЗЫВАЮ» "
                    "не найдено действие в инфинитиве; проверьте формулировку поручения."
                ),
                line=line,
                column=column,
                evidence=line_excerpt(text, directive.start),
                meta={
                    "directive": directive.number,
                    "parser_confidence": "high-when-marker-and-numbering-present",
                },
            )
        )
    return findings
