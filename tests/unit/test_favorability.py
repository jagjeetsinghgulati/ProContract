from __future__ import annotations

from data_model.schema import PartyModel
from favorability.scorer import score_clause_favorability


def test_favorability_scores_generated():
    text = "Supplier shall pay penalty and indemnify Buyer for all losses."
    parties = [PartyModel(display_name="Party1"), PartyModel(display_name="Party2")]
    result = score_clause_favorability(text, parties)
    assert len(result.scores_by_party) >= 2
    assert result.risk_level.value in {"Low", "Medium", "High", "Severe"}
