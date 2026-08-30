from __future__ import annotations

import re


INFINITIVE_CANDIDATE_RE = re.compile(
    r"\b(?:"
    r"[А-Яа-яЁё-]{2,}(?:ать|ять|еть|ить|уть|ыть|оть)(?:ся)?"
    r"|внести|ввести|провести|довести|привести|перевести|вывести|отвести"
    r"|произвести|приобрести|перевезти|привезти|отвезти|ввезти|вывезти"
    r"|принести|донести|занести|нести|вести|идти|прийти|найти|войти|выйти"
    r"|перейти|подойти|уйти|пройти|сойти|дойти"
    r"|учесть|зачесть|прочесть|привлечь|пресечь|достичь|беречь|сберечь"
    r")\b",
    re.IGNORECASE,
)

_NON_VERB_CANDIDATES = {"печать", "память", "кровать", "благодать"}


def is_infinitive_candidate(match: re.Match[str]) -> bool:
    return match.group(0).casefold() not in _NON_VERB_CANDIDATES


def infinitive_occurrences(
    text: str,
    start: int = 0,
    end: int | None = None,
) -> list[re.Match[str]]:
    scan_end = len(text) if end is None else end
    return [
        match
        for match in INFINITIVE_CANDIDATE_RE.finditer(text, start, scan_end)
        if is_infinitive_candidate(match)
    ]
