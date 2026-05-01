SYSTEM_PROMPT = "You analyze legal clause favorability and risk. Return valid JSON."

FAVORABILITY_PROMPT = """
Score favorability for each party on a 1-5 scale.
Output JSON:
{
  "scores_by_party": {"Party1": 3, "Party2": 4, "Party3": 3},
  "beneficiary": "Party2",
  "risk_level": "High",
  "risk_reasons": ["..."]
}

Parties: {parties}
Clause:
{text}
"""
