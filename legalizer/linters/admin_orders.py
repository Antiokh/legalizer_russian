from __future__ import annotations

import re
from dataclasses import dataclass

from ..model import Finding
from ..text import line_column, line_excerpt


ORDER_MARKER_RE = re.compile(r"(?im)^\s*ПРИКАЗЫВАЮ\s*:?[ \t]*$")
ORDER_STOP_RE = re.compile(
    r"(?im)^\s*(?:ПРИЛОЖЕНИЕ(?:\s+№?\s*\d+)?|УТВЕРЖДЕНО|УТВЕРЖДАЮ)\b.*$"
)
# Restrict runtime checking to top-level numbered directives. Nested numbering
# often belongs to an attached regulation rather than to the order itself.
NUMBERED_DIRECTIVE_RE = re.compile(
    r"(?m)^\s*(?P<num>\d+)[.)]\s+(?P<body>\S.*)$"
)
INFINITIVE_CANDIDATE_RE = re.compile(
    r"\b(?:"
    r"[А-Яа-яЁё-]{2,}(?:ать|ять|еть|ить|уть|ыть|оть)(?:ся)?"
    r"|внести|ввести|провести|довести|привести|перевести|вывести|отвести"
    r"|принести|донести|занести|нести|вести|идти|прийти|найти|войти|выйти"
    r"|перейти|подойти|уйти|пройти|сойти|дойти"
    r")\b",
    re.IGNORECASE,
)
_NON_VERB_CANDIDATES = {"печать", "память", "кровать", "благодать"}


@dataclass(slots=True)
class DirectiveParagraph:
    number: str
    start: int
    end: int
    text: str


def _is_infinitive_candidate(match: re.Match[str]) -> bool:
    return match.group(0).casefold() not in _NON_VERB_CANDIDATES


def extract_order_directives(text: str) -> list[DirectiveParagraph]:
    """Extract top-level numbered directive paragraphs after an explicit ПРИКАЗЫВАЮ marker."""

    marker = ORDER_MARKER_RE.search(text)
    if marker is None:
        return []

    stop = ORDER_STOP_RE.search(text, marker.end())
    scan_end = stop.start() if stop else len(text)
    matches = list(NUMBERED_DIRECTIVE_RE.finditer(text, marker.end(), scan_end))
    directives: list[DirectiveParagraph] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else scan_end
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
    """Return conservative infinitive-like action tokens inside parsed order directives."""

    occurrences: list[tuple[DirectiveParagraph, re.Match[str]]] = []
    for directive in extract_order_directives(text):
        for match in INFINITIVE_CANDIDATE_RE.finditer(text, directive.start, directive.end):
            if _is_infinitive_candidate(match):
                occurrences.append((directive, match))
    return occurrences


def lint_order_directive_infinitives(text: str, severity: str = "REVIEW") -> list[Finding]:
    """Review parsed order directives that contain no conservative infinitive-like action."""

    by_directive = {
        directive.number
        for directive, _ in directive_infinitive_occurrences(text)
    }
    findings: list[Finding] = []
    for directive in extract_order_directives(text):
        if directive.number in by_directive:
            continue
        line, column = line_column(text, directive.start)
        findings.append(
            Finding(
                rule_id="ADM-ORDER-001",
                severity=severity,
                message=(
                    f"В распорядительном пункте {directive.number} после «ПРИКАЗЫВАЮ» "
                    "не найдено надёжно распознаваемое действие в инфинитиве; проверьте формулировку поручения."
                ),
                line=line,
                column=column,
                evidence=line_excerpt(text, directive.start),
                meta={
                    "directive": directive.number,
                    "parser_confidence": "conservative-top-level-order-parser",
                },
            )
        )
    return findings
