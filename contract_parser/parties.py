from __future__ import annotations

import re

from data_model.schema import ClauseModel, PartyModel


_ALIASED_PARTY_PATTERN = re.compile(
    r"(?i)\b([A-Z][A-Za-z0-9&.,\-\s]{2,}?)\s*\((?:\"|')?([A-Za-z0-9\s]+?)(?:\"|')?\)"
)

_BETWEEN_PATTERN = re.compile(r"(?is)\bbetween\b(.*?)(?:\bwhereas\b|$)")
_SIGNATURE_PATTERN = re.compile(r"(?im)^\s*for and on behalf of\s+(.+)$")


def detect_parties(text: str, clauses: list[ClauseModel] | None = None) -> list[PartyModel]:
    parties = _extract_from_preamble(text)
    if not parties:
        parties = _extract_from_signature(text)

    if not parties:
        parties = [PartyModel(display_name="Party 1"), PartyModel(display_name="Party 2")]

    # Normalize duplicates by display name.
    deduped: dict[str, PartyModel] = {}
    for party in parties:
        key = party.display_name.strip().lower()
        if key not in deduped:
            deduped[key] = party
    return list(deduped.values())


def _extract_from_preamble(text: str) -> list[PartyModel]:
    preamble = text[:2500]
    between_match = _BETWEEN_PATTERN.search(preamble)
    target = between_match.group(1) if between_match else preamble

    parties: list[PartyModel] = []
    alias_hits = list(_ALIASED_PARTY_PATTERN.finditer(target))
    for hit in alias_hits[:3]:
        legal_name = _clean_name(hit.group(1))
        alias = _clean_name(hit.group(2))
        if legal_name:
            parties.append(PartyModel(display_name=legal_name, aliases=[alias] if alias else []))

    if parties:
        return parties

    # Fallback patterns: "between X and Y" or "X and Y" if "between" already stripped.
    simple = re.search(r"(?is)\bbetween\b\s+(.+?)\s+\band\b\s+(.+?)(?:\.|\n|$)", preamble)
    if not simple:
        simple = re.search(r"(?is)^\s*(.+?)\s+\band\b\s+(.+?)(?:\.|\n|$)", target)
    if simple:
        left = _clean_name(simple.group(1))
        right = _clean_name(simple.group(2))
        if left:
            parties.append(PartyModel(display_name=left))
        if right:
            parties.append(PartyModel(display_name=right))
    return parties


def _extract_from_signature(text: str) -> list[PartyModel]:
    parties: list[PartyModel] = []
    for match in _SIGNATURE_PATTERN.finditer(text):
        name = _clean_name(match.group(1))
        if name:
            parties.append(PartyModel(display_name=name))
    return parties[:3]


def _clean_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip(" ,.;:\n\t")
    value = re.sub(r"(?i)hereinafter.*$", "", value).strip(" ,.;:\n\t")
    return value
