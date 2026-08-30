from __future__ import annotations

import re
from dataclasses import dataclass

from ..model import Finding
from ..text import line_column, line_excerpt
from .modality import modality_occurrences


@dataclass(slots=True)
class ScopeMarker:
    kind: str
    form: str
    text: str
    start: int
    end: int


_EXCEPTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "unless_otherwise",
        re.compile(
            r"\bесли\s+иное\s+не\s+(?:предусмотрено|установлено|определено)\b",
            re.IGNORECASE,
        ),
    ),
    ("except", re.compile(r"\bза\s+исключением\b", re.IGNORECASE)),
    ("except_cases", re.compile(r"\bкроме\s+случа(?:я|ев)\b", re.IGNORECASE)),
]

_CONDITION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("in_case_if", re.compile(r"\bв\s+случае\s+если\b", re.IGNORECASE)),
    ("in_case", re.compile(r"\bв\s+случае\b", re.IGNORECASE)),
    ("provided_that", re.compile(r"\bпри\s+условии(?:\s*,?\s*что)?\b", re.IGNORECASE)),
    ("if", re.compile(r"\bесли\b", re.IGNORECASE)),
]


def scope_marker_occurrences(text: str) -> list[ScopeMarker]:
    markers: list[ScopeMarker] = []
    occupied: list[tuple[int, int]] = []

    # Exception phrases go first so their internal «если» is not separately
    # misclassified as a condition marker.
    for form, pattern in _EXCEPTION_PATTERNS:
        for match in pattern.finditer(text):
            occupied.append((match.start(), match.end()))
            markers.append(
                ScopeMarker("exception", form, match.group(0), match.start(), match.end())
            )

    for form, pattern in _CONDITION_PATTERNS:
        for match in pattern.finditer(text):
            if any(not (match.end() <= start or match.start() >= end) for start, end in occupied):
                continue
            # Prefer the longer «в случае если» over its nested parts.
            if any(
                marker.kind == "condition"
                and not (match.end() <= marker.start or match.start() >= marker.end)
                for marker in markers
            ):
                continue
            markers.append(
                ScopeMarker("condition", form, match.group(0), match.start(), match.end())
            )

    # Remove shorter condition markers that were added before a later, longer
    # overlapping form. This keeps protection output deterministic.
    conditions = [marker for marker in markers if marker.kind == "condition"]
    filtered: list[ScopeMarker] = [marker for marker in markers if marker.kind == "exception"]
    for marker in conditions:
        if any(
            other is not marker
            and other.start <= marker.start
            and other.end >= marker.end
            and (other.end - other.start) > (marker.end - marker.start)
            for other in conditions
        ):
            continue
        filtered.append(marker)

    filtered.sort(key=lambda item: (item.start, item.end, item.kind, item.form))
    return filtered


def _paragraph_bounds(text: str, offset: int) -> tuple[int, int]:
    before = text.rfind("\n\n", 0, offset)
    start = 0 if before < 0 else before + 2
    after = text.find("\n\n", offset)
    end = len(text) if after < 0 else after
    return start, end


def lint_condition_exception_scope(text: str, severity: str = "REVIEW") -> list[Finding]:
    """Raise review candidates; never infer or rewrite the legal scope itself."""

    markers = scope_marker_occurrences(text)
    conditions = [marker for marker in markers if marker.kind == "condition"]
    exceptions = [marker for marker in markers if marker.kind == "exception"]
    modalities = modality_occurrences(text)
    findings: list[Finding] = []
    seen_windows: set[tuple[int, int]] = set()

    for condition in conditions:
        paragraph_start, paragraph_end = _paragraph_bounds(text, condition.start)
        window_start = max(paragraph_start, condition.start - 180)
        window_end = min(paragraph_end, condition.end + 420)

        nearby_exceptions = [
            marker for marker in exceptions if window_start <= marker.start < window_end
        ]
        nearby_modalities = [
            marker for marker in modalities if window_start <= marker.start < window_end
        ]
        if not nearby_exceptions or not nearby_modalities:
            continue

        key = (window_start, window_end)
        if key in seen_windows:
            continue
        seen_windows.add(key)

        line, column = line_column(text, condition.start)
        findings.append(
            Finding(
                rule_id="LDB-015",
                severity=severity,
                message=(
                    "В одном близком фрагменте совмещены условие, юридическая модальность "
                    "и исключение; проверьте, однозначно ли видно область действия условия "
                    "и к какому предписанию относится исключение."
                ),
                line=line,
                column=column,
                evidence=line_excerpt(text, condition.start),
                meta={
                    "condition": condition.text,
                    "exceptions": [marker.text for marker in nearby_exceptions],
                    "modalities": [
                        {"text": marker.text, "kind": marker.kind}
                        for marker in nearby_modalities
                    ],
                    "parser_confidence": "review-candidate-only",
                },
            )
        )

    return findings
