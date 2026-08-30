from __future__ import annotations

import re
from dataclasses import dataclass

from ..model import Finding
from ..text import line_column, line_excerpt
from .defined_terms import alias_pattern


PARTY_INTRO_RE = re.compile(
    r"\bименуем(?:ый|ая|ое|ые)\s+в\s+дальнейшем\s+"
    r"(?P<alias>«[^»\n]{1,80}»|\"[^\"\n]{1,80}\"|[А-ЯЁ][А-Яа-яЁё-]{1,60}(?:\s+\d+)?)",
    re.IGNORECASE,
)


@dataclass(slots=True)
class PartyAlias:
    alias: str
    offset: int
    alias_start: int
    alias_end: int
    line: int
    column: int


def _normalize_party_alias(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and ((value[0], value[-1]) in {("«", "»"), ('"', '"')}):
        value = value[1:-1].strip()
    return re.sub(r"\s+", " ", value)


def extract_party_aliases(text: str) -> list[PartyAlias]:
    aliases: list[PartyAlias] = []
    for match in PARTY_INTRO_RE.finditer(text):
        raw = match.group("alias")
        alias = _normalize_party_alias(raw)
        if not alias:
            continue

        raw_start = match.start("alias")
        raw_end = match.end("alias")
        left_trim = len(raw) - len(raw.lstrip())
        right_trim = len(raw) - len(raw.rstrip())
        alias_start = raw_start + left_trim
        alias_end = raw_end - right_trim
        stripped = raw.strip()
        if len(stripped) >= 2 and ((stripped[0], stripped[-1]) in {("«", "»"), ('"', '"')}):
            alias_start += 1
            alias_end -= 1

        line, column = line_column(text, alias_start)
        aliases.append(
            PartyAlias(
                alias=alias,
                offset=match.start(),
                alias_start=alias_start,
                alias_end=alias_end,
                line=line,
                column=column,
            )
        )
    return aliases


def party_alias_occurrences(text: str) -> list[tuple[PartyAlias, re.Match[str]]]:
    occurrences: list[tuple[PartyAlias, re.Match[str]]] = []
    seen: set[tuple[str, int, int]] = set()
    for party in extract_party_aliases(text):
        for match in alias_pattern(party.alias).finditer(text):
            key = (party.alias.casefold(), match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            occurrences.append((party, match))
    occurrences.sort(key=lambda item: (item[1].start(), item[1].end(), item[0].alias.casefold()))
    return occurrences


def lint_party_aliases(text: str, severity: str = "REVIEW") -> list[Finding]:
    """Check only explicit contractual role introductions: «именуем… в дальнейшем X»."""

    findings: list[Finding] = []
    first_definition: dict[str, PartyAlias] = {}

    for party in extract_party_aliases(text):
        key = party.alias.casefold()
        previous = first_definition.get(key)
        if previous is not None:
            findings.append(
                Finding(
                    rule_id="CTR-001",
                    severity=severity,
                    message=(
                        f"Обозначение стороны «{party.alias}» вводится повторно; "
                        "проверьте, не присвоено ли оно разным участникам договора."
                    ),
                    line=party.line,
                    column=party.column,
                    evidence=line_excerpt(text, party.offset),
                    meta={"first_definition_line": previous.line, "alias": party.alias},
                )
            )
            continue
        first_definition[key] = party

        prior = list(alias_pattern(party.alias).finditer(text[: party.offset]))
        if prior:
            occurrence = prior[-1]
            line, column = line_column(text, occurrence.start())
            findings.append(
                Finding(
                    rule_id="CTR-001",
                    severity=severity,
                    message=(
                        f"Обозначение стороны «{party.alias}» используется до явного "
                        "введения через «именуем… в дальнейшем …»."
                    ),
                    line=line,
                    column=column,
                    evidence=line_excerpt(text, occurrence.start()),
                    meta={"definition_line": party.line, "alias": party.alias},
                )
            )

    return findings
