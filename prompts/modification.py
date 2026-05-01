SYSTEM_PROMPT = "You rewrite legal clauses while preserving legal coherence. Return valid JSON."

MODIFICATION_PROMPT = """
Rewrite the clause.
Mode: {mode}
Target Party: {target_party}

Output JSON:
{
  "proposed_text": "...",
  "change_summary": "..."
}

Clause:
{text}
"""
