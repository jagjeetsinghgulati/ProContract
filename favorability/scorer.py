from __future__ import annotations

from collections import defaultdict

from ai_providers.base_provider import BaseAIProvider
from data_model.enums import FavorabilityTarget, RiskLevel
from data_model.schema import FavorabilityModel, PartyModel


def score_clause_favorability(
    clause_text: str,
    parties: list[PartyModel],
    provider: BaseAIProvider | None = None,
) -> FavorabilityModel:
    if provider:
        ai_model = _score_with_ai(clause_text, parties, provider)
        if ai_model:
            return ai_model

    scores = defaultdict(lambda: 3)
    lowered = clause_text.lower()
    party_names = [p.display_name for p in parties] or ["Party1", "Party2"]
    if len(party_names) == 1:
        party_names.append("Party2")

    left = party_names[0]
    right = party_names[1]
    third = party_names[2] if len(party_names) > 2 else "Party3"

    if any(tok in lowered for tok in ["shall pay", "must pay", "penalty", "liability", "indemnify"]):
        scores[left] = 2
        scores[right] = 4
    if any(tok in lowered for tok in ["exclusive right", "sole discretion", "unilateral"]):
        scores[left] = 1
        scores[right] = 5
    if any(tok in lowered for tok in ["mutual", "both parties", "reciprocal"]):
        scores[left] = 3
        scores[right] = 3

    scores[third] = scores.get(third, 3)

    beneficiary = _determine_beneficiary(scores)
    risk_reasons = []
    if max(scores.values()) - min(scores.values()) >= 3:
        risk_level = RiskLevel.HIGH
        risk_reasons.append("Strong one-sided clause detected.")
    else:
        risk_level = RiskLevel.MEDIUM

    return FavorabilityModel(
        scores_by_party=dict(scores),
        beneficiary=beneficiary,
        risk_level=risk_level,
        risk_reasons=risk_reasons,
    )


def _determine_beneficiary(scores: dict[str, int]) -> FavorabilityTarget:
    if not scores:
        return FavorabilityTarget.NEUTRAL
    top_party = max(scores, key=lambda p: scores[p])
    ordered = sorted(scores.values(), reverse=True)
    if len(ordered) > 1 and ordered[0] == ordered[1]:
        return FavorabilityTarget.NEUTRAL
    normalized = top_party.lower()
    if normalized.endswith("1") or normalized == "party 1":
        return FavorabilityTarget.PARTY_1
    if normalized.endswith("2") or normalized == "party 2":
        return FavorabilityTarget.PARTY_2
    if normalized.endswith("3") or normalized == "party 3":
        return FavorabilityTarget.PARTY_3
    return FavorabilityTarget.NEUTRAL


def _score_with_ai(
    clause_text: str, parties: list[PartyModel], provider: BaseAIProvider
) -> FavorabilityModel | None:
    party_names = [p.display_name for p in parties]
    prompt = (
        "Score favorability per party on a 1-5 scale and return JSON with keys: "
        "scores_by_party (object), beneficiary (Party1/Party2/Party3/Neutral), risk_level, risk_reasons (list).\n"
        f"Parties: {party_names}\nClause:\n{clause_text[:4000]}"
    )
    result = provider.extract_json(prompt)
    if not result.success or not result.data:
        return None
    data = result.data
    try:
        return FavorabilityModel(
            scores_by_party={k: int(v) for k, v in dict(data.get("scores_by_party", {})).items()},
            beneficiary=FavorabilityTarget(str(data.get("beneficiary", "Neutral"))),
            risk_level=RiskLevel(str(data.get("risk_level", "Medium"))),
            risk_reasons=[str(x) for x in data.get("risk_reasons", [])],
        )
    except Exception:
        return None
