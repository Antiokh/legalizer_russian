from __future__ import annotations

import re
from dataclasses import dataclass

from ..model import Finding
from ..text import line_column, line_excerpt


RESPONSIBILITY_HEADING_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s*)?(?:\d+(?:\.\d+)*[.)]?\s*)?"
    r"Ответственность(?:\s+сторон)?\s*:?[ \t]*$"
)
NEXT_SECTION_RE = re.compile(
    r"(?im)^\s*(?:#{1,6}\s+\S.*|\d+(?:\.\d+)*[.)]?\s+[А-ЯЁ][^\n.!?]{2,100})\s*$"
)
NUMBERED_CLAUSE_RE = re.compile(
    r"(?m)^\s*(?:(?:\d+(?:\.\d+)+)[.)]?|\d+[.)])\s+"
)

_BREACH_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "in_case",
        re.compile(
            r"\b(?:в\s+случае|при)\s+(?:нарушения|неисполнения|невыполнения|"
            r"ненадлежащего\s+исполнения|просрочки)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "for_breach",
        re.compile(
            r"\bза\s+(?:нарушение|неисполнение|невыполнение|"
            r"ненадлежащее\s+исполнение|просрочку)\b",
            re.IGNORECASE,
        ),
    ),
]

_CONSEQUENCE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "liability",
        re.compile(r"\b(?:нес[её]т|несут)\s+ответственность\b", re.IGNORECASE),
    ),
    (
        "penalty",
        re.compile(
            r"\b(?:неустойк(?:а|и|у|ой|е)?|штраф(?:а|у|ом|е)?|пен(?:я|и|ю|ей))\b",
            re.IGNORECASE,
        ),
    ),
    (
        "damages",
        re.compile(
            r"\b(?:возмещает|возмещают|возместить|возмещение|взыскать|взыскивается|взыскиваются)"
            r"\b[^.;\n]{0,60}\b(?:убытк[а-яё]*|ущерб[а-яё]*)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "remedy",
        re.compile(
            r"\bвправе\s+(?:расторгнуть|отказаться|приостановить|потребовать)\b",
            re.IGNORECASE,
        ),
    ),
]


@dataclass(slots=True)
class BreachTrigger:
    kind: str
    text: str
    start: int
    end: int


@dataclass(slots=True)
class LegalConsequence:
    kind: str
    text: str
    start: int
    end: int


def _responsibility_sections(text: str) -> list[tuple[int, int]]:
    sections: list[tuple[int, int]] = []
    for heading in RESPONSIBILITY_HEADING_RE.finditer(text):
        next_heading = NEXT_SECTION_RE.search(text, heading.end())
        end = next_heading.start() if next_heading else len(text)
        sections.append((heading.end(), end))
    return sections


def breach_trigger_occurrences(text: str) -> list[BreachTrigger]:
    occurrences: list[BreachTrigger] = []
    occupied: list[tuple[int, int]] = []
    for kind, pattern in _BREACH_PATTERNS:
        for match in pattern.finditer(text):
            if any(not (match.end() <= start or match.start() >= end) for start, end in occupied):
                continue
            occupied.append((match.start(), match.end()))
            occurrences.append(BreachTrigger(kind, match.group(0), match.start(), match.end()))
    occurrences.sort(key=lambda item: (item.start, item.end, item.kind))
    return occurrences


def legal_consequence_occurrences(text: str) -> list[LegalConsequence]:
    occurrences: list[LegalConsequence] = []
    occupied: list[tuple[int, int]] = []
    for kind, pattern in _CONSEQUENCE_PATTERNS:
        for match in pattern.finditer(text):
            if any(not (match.end() <= start or match.start() >= end) for start, end in occupied):
                continue
            occupied.append((match.start(), match.end()))
            occurrences.append(LegalConsequence(kind, match.group(0), match.start(), match.end()))
    occurrences.sort(key=lambda item: (item.start, item.end, item.kind))
    return occurrences


def _paragraph_bounds(text: str, offset: int, section_start: int, section_end: int) -> tuple[int, int]:
    before = text.rfind("\n\n", section_start, offset)
    start = section_start if before < 0 else before + 2
    after = text.find("\n\n", offset, section_end)
    end = section_end if after < 0 else after
    return start, end


def _local_fragment_bounds(
    text: str,
    offset: int,
    section_start: int,
    section_end: int,
) -> tuple[int, int]:
    """Prefer a numbered contractual clause; otherwise fall back to paragraph bounds.

    Contract sections often contain `5.1`, `5.2`, `5.3` on adjacent lines with no
    blank line. Treating the whole block as one paragraph would let a sanction in
    one clause incorrectly satisfy a breach in a different clause.
    """

    numbered = list(NUMBERED_CLAUSE_RE.finditer(text, section_start, section_end))
    containing_index: int | None = None
    for index, match in enumerate(numbered):
        if match.start() <= offset:
            containing_index = index
        else:
            break

    if containing_index is not None:
        start = numbered[containing_index].start()
        end = (
            numbered[containing_index + 1].start()
            if containing_index + 1 < len(numbered)
            else section_end
        )
        if start <= offset < end:
            return start, end

    return _paragraph_bounds(text, offset, section_start, section_end)


def lint_breach_consequence_links(text: str, severity: str = "REVIEW") -> list[Finding]:
    """Review breach phrases in an explicit responsibility section with no local consequence.

    A contract can distribute remedies across clauses or rely on applicable law.
    The runtime therefore does not require a particular sanction and never
    autofixes. The explicit section restriction keeps the signal conservative.
    """

    triggers = breach_trigger_occurrences(text)
    consequences = legal_consequence_occurrences(text)
    findings: list[Finding] = []

    for section_start, section_end in _responsibility_sections(text):
        section_triggers = [item for item in triggers if section_start <= item.start < section_end]
        for trigger in section_triggers:
            fragment_start, fragment_end = _local_fragment_bounds(
                text, trigger.start, section_start, section_end
            )
            if any(fragment_start <= item.start < fragment_end for item in consequences):
                continue

            line, column = line_column(text, trigger.start)
            findings.append(
                Finding(
                    rule_id="CTR-004",
                    severity=severity,
                    message=(
                        "В разделе ответственности явно названо нарушение/неисполнение, "
                        "но в том же локальном фрагменте не найдена формула ответственности "
                        "или последствия; проверьте, однозначно ли связаны нарушение и его правовой эффект."
                    ),
                    line=line,
                    column=column,
                    evidence=line_excerpt(text, trigger.start),
                    meta={
                        "breach": trigger.text,
                        "parser_confidence": "explicit-responsibility-section-review-candidate",
                    },
                )
            )

    return findings
