from __future__ import annotations

from collections import Counter

from ai_providers.base_provider import BaseAIProvider
from classifier.criticality import score_criticality
from classifier.red_flags import detect_red_flags
from data_model.enums import ClauseCategory
from data_model.schema import ClassificationModel


CATEGORY_KEYWORDS: dict[ClauseCategory, tuple[str, ...]] = {
    ClauseCategory.COMMERCIAL: (
        "payment",
        "price",
        "invoice",
        "fees",
        "commercial",
        "discount",
    ),
    ClauseCategory.LEGAL: ("law", "jurisdiction", "liability", "indemnity", "dispute", "arbitration"),
    ClauseCategory.OBLIGATORY: ("shall", "must", "obligation", "required", "compliance"),
    ClauseCategory.CRITICAL: ("termination", "breach", "default", "penalty", "damages"),
    ClauseCategory.INCONSEQUENTIAL: ("notice", "headings", "formatting", "typographical"),
    ClauseCategory.MALICIOUS: ("unlimited liability", "sole discretion", "irrevocable"),
    ClauseCategory.UNNECESSARY: ("redundant", "duplicate", "superfluous", "restate"),
}


def classify_clause(clause_text: str, provider: BaseAIProvider | None = None) -> ClassificationModel:
    text_lower = clause_text.lower()
    scores = Counter()
    matched_keywords: dict[ClauseCategory, list[str]] = {}

    for category, words in CATEGORY_KEYWORDS.items():
        hits = [word for word in words if word in text_lower]
        if hits:
            scores[category] += len(hits)
            matched_keywords[category] = hits

    red_flag, flag_reasons = detect_red_flags(clause_text)

    if scores:
        primary = scores.most_common(1)[0][0]
        secondary = [cat for cat, _ in scores.most_common(3)[1:]]
        confidence = min(0.95, 0.45 + (scores[primary] * 0.1))
    else:
        primary = ClauseCategory.OTHER
        secondary = []
        confidence = 0.4

    rationale_bits = []
    if primary in matched_keywords:
        rationale_bits.append(f"Matched keywords: {', '.join(matched_keywords[primary])}")
    if red_flag:
        rationale_bits.append(f"Red flags: {', '.join(flag_reasons)}")

    if provider:
        ai = _refine_classification_with_ai(clause_text, provider)
        if ai:
            primary = ai.primary_category
            secondary = ai.secondary_categories or secondary
            confidence = max(confidence, ai.confidence)
            if ai.rationale:
                rationale_bits.append(ai.rationale)

    criticality, negotiability = score_criticality(primary, red_flag, clause_text)
    return ClassificationModel(
        primary_category=primary,
        secondary_categories=secondary,
        confidence=confidence,
        rationale=" | ".join(rationale_bits) if rationale_bits else "Rule-based classification.",
        criticality=criticality,
        negotiability=negotiability,
        red_flag=red_flag,
    )


def _refine_classification_with_ai(
    clause_text: str, provider: BaseAIProvider
) -> ClassificationModel | None:
    prompt = (
        "Classify this clause. Return JSON with keys: "
        "primary_category, secondary_categories (list), confidence (0..1), rationale.\n\n"
        f"Clause:\n{clause_text[:5000]}"
    )
    result = provider.extract_json(prompt)
    if not result.success or not result.data:
        return None
    data = result.data
    try:
        primary = ClauseCategory(str(data.get("primary_category", "Other")).title())
    except ValueError:
        primary = ClauseCategory.OTHER

    secondaries = []
    for item in data.get("secondary_categories", []):
        try:
            secondaries.append(ClauseCategory(str(item).title()))
        except ValueError:
            continue

    return ClassificationModel(
        primary_category=primary,
        secondary_categories=secondaries,
        confidence=float(data.get("confidence", 0.5)),
        rationale=str(data.get("rationale", "AI refinement.")),
    )
