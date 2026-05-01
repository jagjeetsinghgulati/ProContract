from __future__ import annotations

from data_model.enums import FavorabilityTarget, ModificationMode
from modifier.redrafter import rewrite_clause


def test_rewrite_clause_balanced():
    original = "Supplier shall be solely responsible for all liabilities."
    result = rewrite_clause(
        clause_text=original,
        mode=ModificationMode.BALANCED,
        target_party=FavorabilityTarget.PARTY_1,
    )
    assert result.proposed_text != original
    assert result.diff is not None
    assert result.diff.changed is True
