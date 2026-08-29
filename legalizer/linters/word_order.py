from __future__ import annotations

import re

from ..model import Finding
from ..text import line_column, line_excerpt


# Conservative heuristic for the pattern discussed in the source as
# "нанизывание творительного падежа": an abstract/nominalized head followed
# within one clause by two adjacent masculine/neuter forms that plausibly end
# in instrumental -ом/-ем. It is only a REVIEW candidate, never a grammar fact.
NOMINALIZATION_WITH_INSTRUMENTAL_CHAIN_RE = re.compile(
    r"\b(?P<head>[А-Яа-яЁё-]{3,}(?:ние|ция|тие|ство))\b"
    r"(?P<middle>[^.!?\n]{0,140}?)"
    r"\b(?P<first>[А-Яа-яЁё-]{3,}(?:ом|ем))\s+"
    r"(?P<second>[А-Яа-яЁё-]{3,}(?:ом|ем))\b",
    re.IGNORECASE,
)

_FALSE_PAIR_FIRST = {
    "затем",
    "совсем",
    "потом",
    "рядом",
    "кругом",
    "целиком",
    "бегом",
    "верхом",
    "даром",
}


def lint_instrumental_attachment(text: str, severity: str = "REVIEW") -> list[Finding]:
    """Flag narrow candidates where stacked instrumental-looking forms may attach ambiguously."""

    findings: list[Finding] = []
    for match in NOMINALIZATION_WITH_INSTRUMENTAL_CHAIN_RE.finditer(text):
        first = match.group("first")
        second = match.group("second")
        if first.casefold() in _FALSE_PAIR_FIRST:
            continue

        line, column = line_column(text, match.start("first"))
        findings.append(
            Finding(
                rule_id="LDB-012",
                severity=severity,
                message=(
                    f"Цепочка «{first} {second}» после номинализации может иметь "
                    "неясное синтаксическое прикрепление; проверьте порядок слов."
                ),
                line=line,
                column=column,
                evidence=line_excerpt(text, match.start()),
                meta={
                    "head": match.group("head"),
                    "first": first,
                    "second": second,
                    "parser_confidence": "conservative-heuristic",
                },
            )
        )
    return findings
