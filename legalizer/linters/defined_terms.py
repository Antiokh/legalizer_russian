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
    alias_start: int
    alias_end: int
    line: int
    column: int


def normalize_alias(value: str) -> str:
    value = value.strip()
    if value.startswith("«") and value.endswith("»"):
        value = value[1:-1].strip()
    return re.sub(r"\s+", " ", value)


def alias_pattern(alias: str) -> re.Pattern[str]:
    escaped = re.escape(alias).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![{WORD_CHAR}]){escaped}(?![{WORD_CHAR}])")


def extract_defined_terms(text: str) -> list[DefinedTerm]:
    terms: list[DefinedTerm] = []
    for match in INTRO_RE.finditer(text):
        alias = normalize_alias(match.group("alias"))
        if not alias:
            continue
        raw_start = match.start("alias")
        raw_end = match.end("alias")
        raw = match.group("alias")
        left_trim = len(raw) - len(raw.lstrip())
        right_trim = len(raw) - len(raw.rstrip())
        alias_start = raw_start + left_trim
        alias_end = raw_end - right_trim
        if raw.strip().startswith("«") and raw.strip().endswith("»"):
            stripped_start = raw_start + left_trim
            alias_start = stripped_start + 1
            alias_end -= 1
        line, column = line_column(text, alias_start)
        terms.append(
            DefinedTerm(
                alias=alias,
                offset=match.start(),
                alias_start=alias_start,
                alias_end=alias_end,
                line=line,
                column=column,
            )
        )
    return terms


def defined_term_occurrences(text: str) -> list[tuple[DefinedTerm, re.Match[str]]]:
    occurrences: list[tuple[DefinedTerm, re.Match[str]]] = []
    seen: set[tuple[str, int, int]] = set()
    for term in extract_defined_terms(text):
        pattern = alias_pattern(term.alias)
        for match in pattern.finditer(text):
            key = (term.alias.casefold(), match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            occurrences.append((term, match))
    occurrences.sort(key=lambda item: (item[1].start(), item[1].end(), item[0].alias.casefold()))
    return occurrences


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
        prior = list(alias_pattern(term.alias).finditer(prefix))
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
