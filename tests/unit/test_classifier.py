from __future__ import annotations

from classifier.categorize import classify_clause
from data_model.enums import ClauseCategory


def test_classify_commercial_clause():
    text = "Client shall pay the invoice within 30 days as per payment terms."
    result = classify_clause(text)
    assert result.primary_category in (ClauseCategory.COMMERCIAL, ClauseCategory.OBLIGATORY)
    assert result.confidence >= 0.4


def test_detect_red_flag_clause():
    text = "Vendor accepts unlimited liability at the sole discretion of Client."
    result = classify_clause(text)
    assert result.red_flag is True
