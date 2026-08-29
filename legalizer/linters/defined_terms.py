from __future__ import annotations

import re
from dataclasses import dataclass

from ..model import Finding
from ..text import line_column, line_excerpt


INTRO_RE = re.compile(
    r"\(\s*далее\s*[—–-]\s*(?P<alias>«[^»\n]{1,80}»|[^)\n]{1,80}?)\s*\)",
    re.IGNORECASE,
)
WORD_CHAR = r"A-Za-zА-Яа-яЁё0-9_"


@dataclass(slots=True)
class DefinedTerm:
    alias: str
    offset: int
    line: int
    column: int


def _normalize_alias(value: str) -> str:
    value = value.strip()
    if value.startswith("«") and value.endswith("»"):
        value = value[1:-1].strip()
    return re.sub(r"\s+", " ", value)


def extract_defined_terms(text: str) -> list[DefinedTerm]:
    terms: list[DefinedTerm] = []
    for match in INTRO_RE.finditer(text):
        alias = _normalize_alias(match.group("alias"))
        if not alias:
            continue
        line, column = line_column(text, match.start("alias"))
        terms.append(DefinedTerm(alias=alias, offset=match.start(), line=line, column=column))
    return terms


def _alias_pattern(alias: str) -> re.Pattern[str]:
    escaped = re.escape(alias).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![{WORD_CHAR}]){escaped}(?![{WORD_CHAR}])")


def lint_defined_terms(text: str, severity: str = "REVIEW") -> list[Finding]:
    findings: list[Finding] = []
    terms = extract_defined_terms(text)
    first_definition: dict[str, DefinedTerm] = {}

    for term in terms:
        key = term.alias.casefold()
        previous = first_definition.get(key)
        if previous is not None:
            findings.append(
                Finding(
                    rule_id="DOC-M05",
                    severity=severity,
                    message=(
                        f"Термин «{term.alias}» вводится повторно; проверьте, что обозначение "
                        "не присвоено двум разным объектам."
                    ),
                    line=term.line,
                    column=term.column,
                    evidence=line_excerpt(text, term.offset),
                    meta={"first_definition_line": previous.line, "alias": term.alias},
                )
            )
            continue
        first_definition[key] = term

        prefix = text[: term.offset]
        prior = list(_alias_pattern(term.alias).finditer(prefix))
        if prior:
            occurrence = prior[-1]
            line, column = line_column(text, occurrence.start())
            findings.append(
                Finding(
                    rule_id="DOC-M05",
                    severity=severity,
                    message=f"Термин «{term.alias}» используется до явного введения через «далее — …».",
                    line=line,
                    column=column,
                    evidence=line_excerpt(text, occurrence.start()),
                    meta={"definition_line": term.line, "alias": term.alias},
                )
            )

    return findings
