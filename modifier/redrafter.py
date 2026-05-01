from __future__ import annotations

from ai_providers.base_provider import BaseAIProvider
from data_model.enums import FavorabilityTarget, ModificationMode
from data_model.schema import ModificationProposalModel
from modifier.diff import build_clause_diff


def rewrite_clause(
    clause_text: str,
    mode: ModificationMode,
    target_party: FavorabilityTarget,
    provider: BaseAIProvider | None = None,
) -> ModificationProposalModel:
    if provider:
        ai_rewrite = _rewrite_with_ai(clause_text, mode, target_party, provider)
        if ai_rewrite:
            return ai_rewrite

    proposed = _rule_based_rewrite(clause_text, mode, target_party)
    diff = build_clause_diff(clause_text, proposed)
    return ModificationProposalModel(
        mode=mode,
        target_party=target_party,
        original_text=clause_text,
        proposed_text=proposed,
        change_summary=diff.summary,
        diff=diff,
    )


def _rule_based_rewrite(
    clause_text: str, mode: ModificationMode, target_party: FavorabilityTarget
) -> str:
    text = clause_text.strip()
    if mode == ModificationMode.BALANCED:
        return (
            text
            + " The parties agree that obligations, remedies, and liability limits under this clause are mutual and proportionate."
        )
    if mode == ModificationMode.FAVOR_PARTY:
        return (
            text
            + f" Notwithstanding anything to the contrary, interpretation and remedies under this clause shall reasonably favor {target_party.value}."
        )
    return (
        text
        + f" {target_party.value} retains sole protective rights under this clause, including expanded termination and indemnity safeguards to the maximum extent permitted by law."
    )


def _rewrite_with_ai(
    clause_text: str,
    mode: ModificationMode,
    target_party: FavorabilityTarget,
    provider: BaseAIProvider,
) -> ModificationProposalModel | None:
    prompt = (
        "Rewrite this clause and return JSON with keys proposed_text and change_summary.\n"
        f"Mode: {mode.value}\nTarget party: {target_party.value}\nClause:\n{clause_text[:5000]}"
    )
    result = provider.extract_json(prompt)
    if not result.success or not result.data:
        return None

    proposed = str(result.data.get("proposed_text", "")).strip()
    if not proposed:
        return None
    summary = str(result.data.get("change_summary", "")).strip()
    diff = build_clause_diff(clause_text, proposed)
    return ModificationProposalModel(
        mode=mode,
        target_party=target_party,
        original_text=clause_text,
        proposed_text=proposed,
        change_summary=summary or diff.summary,
        diff=diff,
    )
