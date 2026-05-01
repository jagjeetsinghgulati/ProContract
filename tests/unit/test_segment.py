from __future__ import annotations

from contract_parser.segment import segment_clauses


def test_segment_numbered_contract():
    text = """
1. Definitions
"Services" means services under this agreement.
2. Payment Terms
Client shall pay invoice in 30 days.
3. Termination
Either party may terminate with 30 days notice.
"""
    clauses = segment_clauses(text, strategy="regex")
    assert len(clauses) == 3
    assert clauses[0].heading.startswith("1.")


def test_segment_paragraph_fallback():
    text = "First paragraph clause.\n\nSecond paragraph clause."
    clauses = segment_clauses(text, strategy="auto", provider=None)
    assert len(clauses) == 2
