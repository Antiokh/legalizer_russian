from __future__ import annotations

import re
from dataclasses import dataclass

from ..model import Finding
from ..text import line_column, line_excerpt


_AMOUNT = (
    r"(?:\d+|одн(?:ого|ой)|двух|тр[её]х|четыр[её]х|пяти|шести|семи|"
    r"восьми|девяти|десяти|одиннадцати|двенадцати|тринадцати|"
    r"четырнадцати|пятнадцати|шестнадцати|семнадцати|восемнадцати|"
    r"девятнадцати|двадцати|тридцати)"
)
_DURATION_UNIT = r"(?:дн(?:я|ей)|сут(?:ок|ки)?|час(?:а|ов)|недел(?:и|ь)|месяц(?:а|ев))"

RELATIVE_DEADLINE_RE = re.compile(
    rf"\b(?:"
    rf"в\s+течение\s+{_AMOUNT}"
    rf"|не\s+позднее(?:\s+чем)?\s+(?:через\s+|за\s+)?{_AMOUNT}"
    rf")"
    rf"(?:\s*\([^()\n]{{1,30}}\))?"
    rf"\s+(?:(?:рабочих|календарных|банковских)\s+)?{_DURATION_UNIT}\b",
    re.IGNORECASE,
)

ANCHOR_RE = re.compile(
    r"\b(?:"
    r"с\s+даты|со\s+дня|с\s+момента|"
    r"после\s+[А-Яа-яЁё0-9«\"(]|"
    r"до\s+[А-Яа-яЁё0-9«\"(]|"
    r"по\s+(?:получении|подписании|истечении|наступлении|завершении|оплате|передаче)\b|"
    r"с\s+\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|"
    r"с\s+\d{1,2}\s+[а-яё]+(?:\s+\d{4})?"
    r")",
    re.IGNORECASE,
)


@dataclass(slots=True)
class RelativeDeadline:
    text: str
    start: int
    end: int
    anchor_text: str | None
    anchor_start: int | None
    anchor_end: int | None


def _sentence_bounds(text: str, offset: int) -> tuple[int, int]:
    left_candidates = [text.rfind(mark, 0, offset) for mark in (".", "!", "?", ";", "\n")]
    left = max(left_candidates)
    start = 0 if left < 0 else left + 1

    right_candidates = [
        pos
        for mark in (".", "!", "?", ";", "\n")
        if (pos := text.find(mark, offset)) >= 0
    ]
    end = min(right_candidates) if right_candidates else len(text)
    return start, end


def relative_deadline_occurrences(text: str) -> list[RelativeDeadline]:
    deadlines: list[RelativeDeadline] = []
    for match in RELATIVE_DEADLINE_RE.finditer(text):
        sentence_start, sentence_end = _sentence_bounds(text, match.start())
        sentence = text[sentence_start:sentence_end]
        anchor = ANCHOR_RE.search(sentence)
        if anchor is None:
            deadlines.append(
                RelativeDeadline(match.group(0), match.start(), match.end(), None, None, None)
            )
            continue

        anchor_start = sentence_start + anchor.start()
        anchor_end = sentence_start + anchor.end()
        deadlines.append(
            RelativeDeadline(
                text=match.group(0),
                start=match.start(),
                end=match.end(),
                anchor_text=anchor.group(0),
                anchor_start=anchor_start,
                anchor_end=anchor_end,
            )
        )
    return deadlines


def lint_relative_deadline_anchors(text: str, severity: str = "REVIEW") -> list[Finding]:
    """Review relative duration deadlines whose local anchor is not explicit.

    An absent local anchor is not proof of a legal defect: the triggering event
    can be supplied by a heading, previous sentence, referenced clause or law.
    The linter therefore never autofixes and always reports a review candidate.
    """

    findings: list[Finding] = []
    for deadline in relative_deadline_occurrences(text):
        if deadline.anchor_text is not None:
            continue
        line, column = line_column(text, deadline.start)
        findings.append(
            Finding(
                rule_id="LDB-016",
                severity=severity,
                message=(
                    "Относительный срок указан без явной точки отсчёта в той же фразе/предложении; "
                    "проверьте, однозначно ли определяется событие, от которого начинается течение срока."
                ),
                line=line,
                column=column,
                evidence=line_excerpt(text, deadline.start),
                meta={
                    "deadline": deadline.text,
                    "parser_confidence": "local-anchor-review-candidate",
                },
            )
        )
    return findings
