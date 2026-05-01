from __future__ import annotations

from data_model.enums import ClauseCategory, CriticalityLevel, Negotiability


def score_criticality(
    category: ClauseCategory,
    red_flag: bool,
    text: str,
) -> tuple[CriticalityLevel, Negotiability]:
    lowered = text.lower()

    if red_flag:
        return CriticalityLevel.LEVEL_5, Negotiability.LOW

    if category in (ClauseCategory.CRITICAL, ClauseCategory.MALICIOUS):
        return CriticalityLevel.LEVEL_5, Negotiability.LOW

    if category in (ClauseCategory.LEGAL, ClauseCategory.OBLIGATORY):
        if any(token in lowered for token in ["termination", "liability", "indemnity", "breach"]):
            return CriticalityLevel.LEVEL_4, Negotiability.MEDIUM
        return CriticalityLevel.LEVEL_3, Negotiability.MEDIUM

    if category == ClauseCategory.COMMERCIAL:
        if any(token in lowered for token in ["penalty", "damages", "payment", "delay"]):
            return CriticalityLevel.LEVEL_4, Negotiability.MEDIUM
        return CriticalityLevel.LEVEL_3, Negotiability.HIGH

    if category == ClauseCategory.INCONSEQUENTIAL:
        return CriticalityLevel.LEVEL_1, Negotiability.HIGH
    if category == ClauseCategory.UNNECESSARY:
        return CriticalityLevel.LEVEL_2, Negotiability.HIGH

    return CriticalityLevel.LEVEL_2, Negotiability.MEDIUM
