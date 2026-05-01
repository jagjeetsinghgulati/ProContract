SYSTEM_PROMPT = "You are a legal contract parsing assistant. Return valid JSON only."

CLAUSE_SEGMENT_PROMPT = """
Segment the contract into clauses.
Output JSON:
{
  "clauses": [
    {"heading": "...", "text": "..."}
  ]
}

Contract:
{text}
"""
