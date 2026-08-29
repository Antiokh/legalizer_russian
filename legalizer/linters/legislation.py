from __future__ import annotations

import re

from ..model import Finding
from ..text import line_column, line_excerpt


PREAMBLE_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?[Пп]реамбула\b\s*[:.]?\s*(?P<inline>.*)$",
    re.MULTILINE,
)
ARTICLE_HEADING_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?[Сс]татья\s+\d+(?:\.\d+)*\b",
    re.MULTILINE,
)
DIRECTIVE_RE = re.compile(
    r"\b(?:обязан(?:а|о|ы)?|должен|должна|должно|должны|запрещается|запрещено|"
    r"вправе|подлежит|не\s+допускается)\b",
    re.IGNORECASE,
)
DEFINITION_RE = re.compile(
    r"\b(?:для\s+целей\s+настоящего|в\s+настоящем\s+[^.]{0,80}\bпонимается\b|"
    r"под\s+[^.]{1,80}\bпонимается\b)",
    re.IGNORECASE,
)

SECTION_RE = re.compile(r"^\s*(?:#{1,6}\s*)?[Рр]аздел\b", re.MULTILINE)
SUBSECTION_RE = re.compile(r"^\s*(?:#{1,6}\s*)?[Пп]одраздел\b", re.MULTILINE)
CHAPTER_RE = re.compile(r"^\s*(?:#{1,6}\s*)?[Гг]лава\b", re.MULTILINE)


def _preamble_range(text: str) -> tuple[int, int] | None:
    start_match = PREAMBLE_RE.search(text)
    if not start_match:
        return None
    start = start_match.start("inline") if start_match.group("inline").strip() else start_match.end()
    article = ARTICLE_HEADING_RE.search(text, start_match.end())
    end = article.start() if article else len(text)
    return start, end


def lint_legislation_preamble(text: str, severity: str = "REVIEW") -> list[Finding]:
    span = _preamble_range(text)
    if span is None:
        return []
    start, end = span
    preamble = text[start:end]
    findings: list[Finding] = []

    for kind, pattern, message in (
        (
            "directive",
            DIRECTIVE_RE,
            "В явно размеченной преамбуле обнаружена конструкция, похожая на самостоятельное нормативное предписание.",
        ),
        (
            "definition",
            DEFINITION_RE,
            "В явно размеченной преамбуле обнаружена конструкция, похожая на легальную дефиницию.",
        ),
    ):
        match = pattern.search(preamble)
        if match:
            offset = start + match.start()
            line, column = line_column(text, offset)
            findings.append(
                Finding(
                    rule_id="DOC-N01",
                    severity=severity,
                    message=message,
                    line=line,
                    column=column,
                    evidence=line_excerpt(text, offset),
                    meta={"signal": kind, "parser_confidence": "high"},
                )
            )
    return findings


def lint_legislation_hierarchy(text: str, severity: str = "REVIEW") -> list[Finding]:
    has_section = SECTION_RE.search(text) is not None
    has_subsection = SUBSECTION_RE.search(text) is not None
    has_chapter = CHAPTER_RE.search(text) is not None
    if (has_section or has_subsection) and not has_chapter:
        match = SECTION_RE.search(text) or SUBSECTION_RE.search(text)
        assert match is not None
        line, column = line_column(text, match.start())
        return [
            Finding(
                rule_id="DOC-N02",
                severity=severity,
                message="В законопроектной структуре есть раздел/подраздел, но не обнаружены главы; проверьте допустимость такой рубрикации.",
                line=line,
                column=column,
                evidence=line_excerpt(text, match.start()),
                meta={"parser_confidence": "high"},
            )
        ]
    return []
