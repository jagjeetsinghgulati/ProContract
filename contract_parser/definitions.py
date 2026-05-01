from __future__ import annotations

import re

from data_model.schema import ClauseModel


_DEF_PATTERN = re.compile(r'(?:"([^"]+)"|\'([^\']+)\')\s+(?:means|shall mean)\s+(.+?)(?:\.|$)', re.IGNORECASE)


def build_definitions_map(clauses: list[ClauseModel]) -> dict[str, str]:
    definitions: dict[str, str] = {}
    for clause in clauses:
        heading = clause.heading.lower()
        if "definition" in heading or "definitions" in heading:
            for match in _DEF_PATTERN.finditer(clause.text):
                term = (match.group(1) or match.group(2) or "").strip()
                meaning = match.group(3).strip()
                if term and meaning:
                    definitions[term] = meaning
    return definitions


def extract_defined_terms_from_text(text: str, definitions: dict[str, str]) -> list[str]:
    hits: list[str] = []
    lowered = text.lower()
    for term in definitions:
        if term.lower() in lowered:
            hits.append(term)
    return sorted(set(hits))
