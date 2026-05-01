SYSTEM_PROMPT = "You classify contract clauses. Return compact valid JSON."

CLASSIFY_PROMPT = """
Classify the clause into one primary category and optional secondary categories.
Allowed categories: Commercial, Legal, Obligatory, Critical, Inconsequential, Malicious, Unnecessary, Other.
Output JSON:
{
  "primary_category": "Commercial",
  "secondary_categories": ["Legal"],
  "confidence": 0.0,
  "rationale": "..."
}

Clause:
{text}
"""
