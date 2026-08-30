from __future__ import annotations

import re
from dataclasses import dataclass

from ..model import Finding
from ..text import line_column, line_excerpt
from .contract_parties import extract_party_aliases
from .defined_terms import alias_pattern
from .verb_forms import infinitive_occurrences


PERSONAL_OBLIGATION_RE = re.compile(
    r"\b(?:обязан|обязана|обязаны|обязуется|обязуются)\b",
    re.IGNORECASE,
)
COLLECTIVE_SUBJECT_RE = re.compile(
    r"\b(?:Сторона|Стороны|каждая\s+Сторона|обе\s+Стороны)\b",
    re.IGNORECASE,
)
LEADING_CONTEXT_RE = re.compile(
    r"^(?:"
    r"при\s+этом|"
    r"если\b[^,;:.!?\n]{0,160},?|"
    r"в\s+случае(?:\s+если)?\b[^,;:.!?\n]{0,160},?|"
    r"при\s+условии\b[^,;:.!?\n]{0,160},?|"
    r"после\b[^,;:.!?\n]{0,160},?|"
    r"до\b[^,;:.!?\n]{0,160},?|"
    r"с\s+(?:момента|даты)\b[^,;:.!?\n]{0,160},?|"
    r"со\s+дня\b[^,;:.!?\n]{0,160},?|"
    r"по\s+(?:истечении|получении|подписании|наступлении)\b[^,;:.!?\n]{0,160},?|"
    r"в\s+течение\b[^,;:.!?\n]{0,160},?"
    r")\s*$",
    re.IGNORECASE,
)
STRUCTURAL_PREFIX_RE = re.compile(r"^\s*(?:[-*•]|\d+(?:\.\d+)*[.)]?)?\s*")
CAPITALIZED_TOKEN_RE = re.compile(r"\b[А-ЯЁ][а-яё-]{2,}\b")


@dataclass(slots=True)
class ImplicitObligationSubject:
    text: str
    start: int
    end: int
    clause_start: int
    clause_end: int


@dataclass(slots=True)
class ObligationAction:
    modality: str
    action: str
    start: int
    end: int
    modality_start: int
    clause_start: int
    clause_end: int


@dataclass(slots=True)
class IncompleteObligationContent:
    modality: str
    start: int
    end: int
    clause_start: int
    clause_end: int


def _clause_bounds(text: str, offset: int) -> tuple[int, int]:
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


def _explicit_party_in_clause(clause: str, aliases: list[str]) -> bool:
    if COLLECTIVE_SUBJECT_RE.search(clause):
        return True
    return any(alias_pattern(alias).search(clause) for alias in aliases)


def _looks_like_subjectless_prefix(prefix: str) -> bool:
    cleaned = STRUCTURAL_PREFIX_RE.sub("", prefix).strip()
    if not cleaned:
        return True

    # Avoid calling a clause subjectless when a role-like capitalized noun is
    # visible even if it was introduced by a contractual formula we do not yet
    # parse. This intentionally trades recall for fewer false positives.
    caps = CAPITALIZED_TOKEN_RE.findall(cleaned)
    if caps:
        first_word = cleaned.split(maxsplit=1)[0].casefold()
        ignored_sentence_starters = {"если", "после", "до", "при"}
        visible_caps = [
            token
            for token in caps
            if token.casefold() != first_word or first_word not in ignored_sentence_starters
        ]
        if visible_caps:
            return False

    return bool(LEADING_CONTEXT_RE.fullmatch(cleaned))


def _party_aliases(text: str) -> list[str]:
    return sorted({party.alias for party in extract_party_aliases(text)}, key=str.casefold)


def implicit_obligation_subject_occurrences(text: str) -> list[ImplicitObligationSubject]:
    """Locate only obvious personal obligation formulas with an implicit local subject.

    The check activates only when the document explicitly introduces at least
    one contractual party alias. It does not attempt full syntactic parsing and
    deliberately ignores the broader `должен/должны` family because those forms
    often describe requirements for documents, objects or states rather than a
    party's personal obligation.
    """

    aliases = _party_aliases(text)
    if not aliases:
        return []

    occurrences: list[ImplicitObligationSubject] = []
    for match in PERSONAL_OBLIGATION_RE.finditer(text):
        clause_start, clause_end = _clause_bounds(text, match.start())
        clause = text[clause_start:clause_end]
        if _explicit_party_in_clause(clause, aliases):
            continue

        prefix = text[clause_start:match.start()]
        if not _looks_like_subjectless_prefix(prefix):
            continue

        occurrences.append(
            ImplicitObligationSubject(
                text=match.group(0),
                start=match.start(),
                end=match.end(),
                clause_start=clause_start,
                clause_end=clause_end,
            )
        )
    return occurrences


def obligation_action_occurrences(text: str) -> list[ObligationAction]:
    """Locate the first conservative infinitive-like action after a strong personal obligation."""

    aliases = _party_aliases(text)
    if not aliases:
        return []

    occurrences: list[ObligationAction] = []
    for modality in PERSONAL_OBLIGATION_RE.finditer(text):
        clause_start, clause_end = _clause_bounds(text, modality.start())
        actions = infinitive_occurrences(text, modality.end(), clause_end)
        if not actions:
            continue
        action = actions[0]
        occurrences.append(
            ObligationAction(
                modality=modality.group(0),
                action=action.group(0),
                start=action.start(),
                end=action.end(),
                modality_start=modality.start(),
                clause_start=clause_start,
                clause_end=clause_end,
            )
        )
    return occurrences


def incomplete_obligation_content_occurrences(text: str) -> list[IncompleteObligationContent]:
    """Review only explicit-party obligations that have no local action after the modality.

    This is intentionally narrower than semantic completeness. It does not try
    to infer whether the action has a sufficient object, quantity, quality,
    recipient or other legal qualifiers. Those remain a model/lawyer review.
    """

    aliases = _party_aliases(text)
    if not aliases:
        return []

    action_by_modality = {item.modality_start for item in obligation_action_occurrences(text)}
    occurrences: list[IncompleteObligationContent] = []
    for modality in PERSONAL_OBLIGATION_RE.finditer(text):
        if modality.start() in action_by_modality:
            continue
        clause_start, clause_end = _clause_bounds(text, modality.start())
        clause = text[clause_start:clause_end]
        # Subjectless formulas are already handled by CTR-002. Avoid duplicate
        # diagnostics until a full dependency parser can distinguish both defects.
        if not _explicit_party_in_clause(clause, aliases):
            continue
        occurrences.append(
            IncompleteObligationContent(
                modality=modality.group(0),
                start=modality.start(),
                end=modality.end(),
                clause_start=clause_start,
                clause_end=clause_end,
            )
        )
    return occurrences


def lint_obligation_subjects(text: str, severity: str = "REVIEW") -> list[Finding]:
    findings: list[Finding] = []
    for occurrence in implicit_obligation_subject_occurrences(text):
        line, column = line_column(text, occurrence.start)
        findings.append(
            Finding(
                rule_id="CTR-002",
                severity=severity,
                message=(
                    "Формула обязанности употреблена без локально выраженного субъекта; "
                    "проверьте, однозначно ли определяется обязанная сторона из структуры договора."
                ),
                line=line,
                column=column,
                evidence=line_excerpt(text, occurrence.start),
                meta={
                    "modality": occurrence.text,
                    "parser_confidence": "conservative-implicit-subject-candidate",
                },
            )
        )
    return findings


def lint_obligation_content(text: str, severity: str = "REVIEW") -> list[Finding]:
    findings: list[Finding] = []
    for occurrence in incomplete_obligation_content_occurrences(text):
        line, column = line_column(text, occurrence.start)
        findings.append(
            Finding(
                rule_id="CTR-003",
                severity=severity,
                message=(
                    "У явно названной стороны найдена сильная формула обязанности, "
                    "но после неё не найдено локально выраженное действие; проверьте, "
                    "полно ли сформулировано содержание обязательства."
                ),
                line=line,
                column=column,
                evidence=line_excerpt(text, occurrence.start),
                meta={
                    "modality": occurrence.modality,
                    "parser_confidence": "missing-local-action-review-candidate",
                },
            )
        )
    return findings
