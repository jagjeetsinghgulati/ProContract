from __future__ import annotations

import re
from typing import Iterable

from ai_providers.base_provider import BaseAIProvider
from data_model.schema import ClauseModel


_NUMBERED_HEADING_PATTERN = re.compile(r"(?m)^\s*(\d+(?:\.\d+)*[\)\.]?)\s+(.+)$")


def segment_clauses(
    text: str,
    strategy: str = "auto",
    provider: BaseAIProvider | None = None,
) -> list[ClauseModel]:
    text = text.strip()
    if not text:
        return []

    if strategy in ("auto", "regex"):
        clauses = _segment_with_regex(text)
        if clauses and (strategy == "regex" or len(clauses) >= 3):
            return clauses

    if strategy in ("auto", "ai") and provider is not None:
        ai_clauses = _segment_with_ai(text, provider)
        if ai_clauses:
            return ai_clauses

    return _segment_with_paragraphs(text)


def _segment_with_regex(text: str) -> list[ClauseModel]:
    matches = list(_NUMBERED_HEADING_PATTERN.finditer(text))
    if not matches:
        return []

    clauses: list[ClauseModel] = []
    for idx, match in enumerate(matches, start=1):
        number = match.group(1).strip()
        start = match.start()
        end = matches[idx].start() if idx < len(matches) else len(text)
        block = text[start:end].strip()
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        heading_line = lines[0]
        clause_body = "\n".join(lines[1:]).strip()
        if not clause_body:
            heading, clause_text = _split_heading_body(heading_line)
            clause_text = clause_text or heading_line
        else:
            heading = heading_line
            clause_text = clause_body
        clauses.append(
            ClauseModel(
                heading=heading,
                text=clause_text,
                source_section=number,
            )
        )
    return clauses


def _segment_with_ai(text: str, provider: BaseAIProvider) -> list[ClauseModel]:
    prompt = (
        "Segment the contract text into clauses and return JSON in this format: "
        '{"clauses":[{"heading":"...", "text":"..."}]}.\n\n'
        f"Contract text:\n{text[:12000]}"
    )
    result = provider.extract_json(prompt)
    if not result.success or not result.data:
        return []
    rows: Iterable[dict] = result.data.get("clauses", [])
    clauses: list[ClauseModel] = []
    for row in rows:
        clause_text = str(row.get("text", "")).strip()
        if not clause_text:
            continue
        clauses.append(
            ClauseModel(
                heading=str(row.get("heading", "")).strip(),
                text=clause_text,
                source_section=str(row.get("heading", "")).strip(),
            )
        )
    return clauses


def _segment_with_paragraphs(text: str) -> list[ClauseModel]:
    blocks = [b.strip() for b in re.split(r"\n{2,}", text) if b.strip()]
    clauses: list[ClauseModel] = []
    for idx, block in enumerate(blocks, start=1):
        heading, body = _split_heading_body(block)
        clauses.append(
            ClauseModel(
                heading=heading or f"Clause {idx}",
                text=body,
                source_section=f"Clause {idx}",
            )
        )
    return clauses


def _split_heading_body(raw_text: str) -> tuple[str, str]:
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    if len(lines[0]) <= 90 and len(lines) > 1:
        return lines[0], "\n".join(lines[1:])
    sentence_split = re.split(r"(?<=[.!?])\s+", raw_text, maxsplit=1)
    if len(sentence_split) == 2 and len(sentence_split[0]) < 100:
        return sentence_split[0], sentence_split[1]
    return "", raw_text
