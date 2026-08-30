from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(slots=True)
class ModalityOccurrence:
    kind: str
    text: str
    start: int
    end: int


_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "prohibition",
        re.compile(
            r"\b(?:не\s+вправе|не\s+(?:имеет|имеют)\s+права|"
            r"не\s+(?:должен|должна|должно|должны)|"
            r"не\s+допускается|запрещается|запрещено)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "right",
        re.compile(r"\b(?:вправе|(?:имеет|имеют)\s+право)\b", re.IGNORECASE),
    ),
    (
        "permission",
        re.compile(r"\b(?:разрешается|разрешено)\b", re.IGNORECASE),
    ),
    (
        "obligation",
        re.compile(
            r"\b(?:обязан|обязана|обязано|обязаны|обязуется|обязуются|"
            r"должен|должна|должно|должны)\b",
            re.IGNORECASE,
        ),
    ),
]


def modality_occurrences(text: str) -> list[ModalityOccurrence]:
    """Locate strong lexical signals without inferring legal force from context.

    Deliberately excludes «может»: in legal prose it can express permission,
    possibility, competence, or a factual capability, so token-level
    classification would overclaim.
    """

    occurrences: list[ModalityOccurrence] = []
    occupied: list[tuple[int, int]] = []

    for kind, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            if any(not (match.end() <= start or match.start() >= end) for start, end in occupied):
                continue
            occupied.append((match.start(), match.end()))
            occurrences.append(
                ModalityOccurrence(
                    kind=kind,
                    text=match.group(0),
                    start=match.start(),
                    end=match.end(),
                )
            )

    occurrences.sort(key=lambda item: (item.start, item.end, item.kind))
    return occurrences
