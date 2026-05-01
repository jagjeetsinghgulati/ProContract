from __future__ import annotations

from data_model.enums import ModificationMode
from data_model.schema import ClauseModel, ModificationProposalModel


def generate_negotiation_note(clause: ClauseModel, proposal: ModificationProposalModel) -> str:
    base = f"Clause {clause.source_section or clause.clause_id}: "
    if proposal.mode == ModificationMode.BALANCED:
        return base + "Proposed language introduces reciprocal obligations and balanced risk allocation."
    if proposal.mode == ModificationMode.FAVOR_PARTY:
        return base + "Proposed language tilts commercial/legal outcomes toward the selected party."
    return base + "Aggressive fallback language provided for opening negotiation position."
