from __future__ import annotations


def line_column(text: str, offset: int) -> tuple[int, int]:
    offset = max(0, min(offset, len(text)))
    line = text.count("\n", 0, offset) + 1
    last_newline = text.rfind("\n", 0, offset)
    column = offset + 1 if last_newline < 0 else offset - last_newline
    return line, column


def line_excerpt(text: str, offset: int, limit: int = 220) -> str:
    start = text.rfind("\n", 0, offset) + 1
    end = text.find("\n", offset)
    if end < 0:
        end = len(text)
    value = text[start:end].strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"
