from __future__ import annotations

from contract_parser.parties import detect_parties


def test_detect_parties_from_between_clause():
    text = """
This Agreement is made between Alpha Technologies Private Limited and Beta Manufacturing Limited.
"""
    parties = detect_parties(text)
    assert len(parties) >= 2
    names = [p.display_name for p in parties]
    assert any("Alpha" in n for n in names)
    assert any("Beta" in n for n in names)


def test_detect_parties_fallback_defaults():
    text = "Simple terms and conditions without clear party names."
    parties = detect_parties(text)
    assert len(parties) == 2
