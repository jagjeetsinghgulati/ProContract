from __future__ import annotations

from data_model.enums import ClauseCategory, RiskLevel
from data_model.schema import ClassificationModel, FavorabilityModel


def assess_clause_risk(
    classification: ClassificationModel,
    favorability: FavorabilityModel,
) -> tuple[RiskLevel, list[str]]:
    reasons: list[str] = []
    level = favorability.risk_level

    if classification.red_flag:
        level = RiskLevel.SEVERE
        reasons.append("Red flag pattern detected.")

    if classification.primary_category in (ClauseCategory.MALICIOUS, ClauseCategory.CRITICAL):
        level = RiskLevel.SEVERE
        reasons.append("Clause category has elevated legal/commercial risk.")

    scores = list(favorability.scores_by_party.values())
    if scores and (max(scores) - min(scores) >= 3):
        if level == RiskLevel.MEDIUM:
            level = RiskLevel.HIGH
        reasons.append("High favorability imbalance between parties.")

    if not reasons:
        reasons.append("No major concerns from rule-based risk engine.")
    return level, reasons
