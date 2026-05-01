from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from data_model.enums import (
    ClauseCategory,
    CriticalityLevel,
    DocumentType,
    FavorabilityTarget,
    ModificationMode,
    Negotiability,
    RiskLevel,
)


def _utc_now() -> datetime:
    return datetime.now(UTC)


class PartyModel(BaseModel):
    party_id: str = Field(default_factory=lambda: str(uuid4()))
    display_name: str
    aliases: list[str] = Field(default_factory=list)
    role_hint: str | None = None


class ClassificationModel(BaseModel):
    primary_category: ClauseCategory = ClauseCategory.OTHER
    secondary_categories: list[ClauseCategory] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    rationale: str = ""
    criticality: CriticalityLevel = CriticalityLevel.LEVEL_3
    negotiability: Negotiability = Negotiability.MEDIUM
    red_flag: bool = False


class FavorabilityModel(BaseModel):
    scores_by_party: dict[str, int] = Field(default_factory=dict)
    beneficiary: FavorabilityTarget = FavorabilityTarget.NEUTRAL
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_reasons: list[str] = Field(default_factory=list)


class ClauseDiffModel(BaseModel):
    added_lines: list[str] = Field(default_factory=list)
    removed_lines: list[str] = Field(default_factory=list)
    changed: bool = False
    summary: str = ""


class ModificationProposalModel(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid4()))
    mode: ModificationMode
    target_party: FavorabilityTarget
    original_text: str
    proposed_text: str
    change_summary: str = ""
    accept_status: str = "Pending"
    diff: ClauseDiffModel | None = None


class ClauseModel(BaseModel):
    clause_id: str = Field(default_factory=lambda: str(uuid4()))
    heading: str = ""
    text: str
    source_page: int | None = None
    source_section: str = ""
    defined_terms: list[str] = Field(default_factory=list)
    classification: ClassificationModel | None = None
    favorability: FavorabilityModel | None = None
    modifications: list[ModificationProposalModel] = Field(default_factory=list)


class ContractModel(BaseModel):
    contract_id: str = Field(default_factory=lambda: str(uuid4()))
    file_name: str
    document_type: DocumentType
    raw_text: str
    clauses: list[ClauseModel] = Field(default_factory=list)
    parties: list[PartyModel] = Field(default_factory=list)
    governing_law: str | None = None
    effective_date: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utc_now)


class StageStatusModel(BaseModel):
    completed: bool = False
    duration_ms: float | None = None
    error: str | None = None


class PipelineRunModel(BaseModel):
    run_id: str = Field(default_factory=lambda: str(uuid4()))
    contract_id: str
    provider_used: str = "none"
    stages: dict[str, StageStatusModel] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=_utc_now)
    finished_at: datetime | None = None


class UserModel(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=_utc_now)
    is_active: bool = True
