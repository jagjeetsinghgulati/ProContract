from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from ai_providers.base_provider import ProviderType
from ai_providers.factory import get_factory
from classifier.categorize import classify_clause
from contract_parser.definitions import build_definitions_map, extract_defined_terms_from_text
from contract_parser.extract import extract_text
from contract_parser.parties import detect_parties
from contract_parser.segment import segment_clauses
from data_model.enums import FavorabilityTarget, ModificationMode
from data_model.persistence import save_contract, save_contract_run
from data_model.schema import ContractModel, PipelineRunModel, StageStatusModel
from favorability.balance import calculate_contract_balance
from favorability.risk import assess_clause_risk
from favorability.scorer import score_clause_favorability
from modifier.negotiation import generate_negotiation_note
from modifier.redrafter import rewrite_clause
from reports.analysis_report import generate_analysis_report
from reports.change_report import generate_change_report
from reports.clause_register import export_clause_register
from reports.modified_contract import export_modified_contract


def _get_provider(provider_name: str, allow_cloud: bool):
    if provider_name in ("", "none", None):
        return None
    try:
        provider_type = ProviderType(provider_name.lower())
    except ValueError:
        return None
    return get_factory().get_provider(provider_type=provider_type, allow_cloud=allow_cloud)


def run_phase1_pipeline(
    file_path: str,
    provider_name: str = "none",
    allow_cloud: bool = False,
) -> tuple[ContractModel, PipelineRunModel]:
    provider = _get_provider(provider_name, allow_cloud=allow_cloud)
    extracted = extract_text(file_path)
    run = PipelineRunModel(contract_id="", provider_used=provider_name or "none")

    started = perf_counter()
    clauses = segment_clauses(extracted.text, strategy="auto", provider=provider)
    run.stages["segment"] = StageStatusModel(
        completed=True, duration_ms=(perf_counter() - started) * 1000
    )

    started = perf_counter()
    parties = detect_parties(extracted.text, clauses)
    run.stages["party_detection"] = StageStatusModel(
        completed=True, duration_ms=(perf_counter() - started) * 1000
    )

    started = perf_counter()
    definitions = build_definitions_map(clauses)
    for clause in clauses:
        clause.defined_terms = extract_defined_terms_from_text(clause.text, definitions)
    run.stages["definitions"] = StageStatusModel(
        completed=True, duration_ms=(perf_counter() - started) * 1000
    )

    contract = ContractModel(
        file_name=Path(file_path).name,
        document_type=extracted.document_type,
        raw_text=extracted.text,
        clauses=clauses,
        parties=parties,
        metadata={"page_count": extracted.page_count, "definitions": definitions},
    )
    run.contract_id = contract.contract_id
    run.finished_at = datetime.now(UTC)

    save_contract(contract)
    save_contract_run(run)
    return contract, run


def run_classification(contract: ContractModel, provider_name: str = "none", allow_cloud: bool = False) -> ContractModel:
    provider = _get_provider(provider_name, allow_cloud=allow_cloud)
    for clause in contract.clauses:
        clause.classification = classify_clause(clause.text, provider=provider)
    save_contract(contract)
    return contract


def run_favorability(contract: ContractModel, provider_name: str = "none", allow_cloud: bool = False) -> dict:
    provider = _get_provider(provider_name, allow_cloud=allow_cloud)
    for clause in contract.clauses:
        clause.favorability = score_clause_favorability(
            clause.text, contract.parties, provider=provider
        )
        if clause.classification:
            risk_level, reasons = assess_clause_risk(clause.classification, clause.favorability)
            clause.favorability.risk_level = risk_level
            clause.favorability.risk_reasons = reasons
    balance = calculate_contract_balance(contract.clauses)
    save_contract(contract)
    return balance


def run_modification(
    contract: ContractModel,
    mode: ModificationMode,
    target_party: FavorabilityTarget,
    provider_name: str = "none",
    allow_cloud: bool = False,
) -> ContractModel:
    provider = _get_provider(provider_name, allow_cloud=allow_cloud)
    for clause in contract.clauses:
        proposal = rewrite_clause(
            clause.text, mode=mode, target_party=target_party, provider=provider
        )
        proposal.change_summary = (
            proposal.change_summary
            + " | "
            + generate_negotiation_note(clause, proposal)
        )
        clause.modifications.append(proposal)
    save_contract(contract)
    return contract


def run_reporting(contract: ContractModel, output_dir: str = "output") -> dict[str, str]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    clause_register = export_clause_register(contract, out / "clause_register.xlsx")
    analysis_report = generate_analysis_report(contract, out / "analysis_report.docx")
    change_report = generate_change_report(contract, out / "change_report.docx")
    modified_contract = export_modified_contract(contract, out / "modified_contract.docx")
    return {
        "clause_register": str(clause_register),
        "analysis_report": str(analysis_report),
        "change_report": str(change_report),
        "modified_contract": str(modified_contract),
    }
