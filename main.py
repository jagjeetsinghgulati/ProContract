from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import setup_logging
from data_model.enums import FavorabilityTarget, ModificationMode
from data_model.persistence import init_db, load_contract
from data_model.schema import ContractModel
from pipeline import (
    run_classification,
    run_favorability,
    run_modification,
    run_phase1_pipeline,
    run_reporting,
)


def _write_json(path: str, payload: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, default=str)


def _load_contract_json(path: str) -> ContractModel:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and "contract" in payload:
        payload = payload["contract"]
    return ContractModel.model_validate(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ProContracts CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_phase1 = sub.add_parser("phase1", help="Run ingestion + segmentation + party detection")
    p_phase1.add_argument("--file", required=True, help="Path to PDF/DOCX/TXT")
    p_phase1.add_argument("--provider", default="none", choices=["none", "ollama", "lmstudio", "gemini"])
    p_phase1.add_argument("--allow-cloud", action="store_true", help="Allow Gemini usage")
    p_phase1.add_argument("--output", default="output/phase1_contract.json")

    p_classify = sub.add_parser("classify", help="Run clause classification")
    p_classify.add_argument("--contract-json", required=True)
    p_classify.add_argument("--provider", default="none", choices=["none", "ollama", "lmstudio", "gemini"])
    p_classify.add_argument("--allow-cloud", action="store_true")
    p_classify.add_argument("--output", default="output/classified_contract.json")

    p_favor = sub.add_parser("favorability", help="Run favorability + risk analysis")
    p_favor.add_argument("--contract-json", required=True)
    p_favor.add_argument("--provider", default="none", choices=["none", "ollama", "lmstudio", "gemini"])
    p_favor.add_argument("--allow-cloud", action="store_true")
    p_favor.add_argument("--output", default="output/favorability_contract.json")

    p_modify = sub.add_parser("modify", help="Generate clause modification proposals")
    p_modify.add_argument("--contract-json", required=True)
    p_modify.add_argument("--mode", default="Balanced", choices=["Balanced", "FavorParty", "Aggressive"])
    p_modify.add_argument("--target-party", default="Party1", choices=["Party1", "Party2", "Party3", "Neutral"])
    p_modify.add_argument("--provider", default="none", choices=["none", "ollama", "lmstudio", "gemini"])
    p_modify.add_argument("--allow-cloud", action="store_true")
    p_modify.add_argument("--output", default="output/modified_contract_state.json")

    p_report = sub.add_parser("report", help="Generate export artifacts")
    p_report.add_argument("--contract-json", required=False)
    p_report.add_argument("--contract-id", required=False)
    p_report.add_argument("--output-dir", default="output")

    return parser


def main() -> None:
    setup_logging()
    init_db()

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "phase1":
        contract, run = run_phase1_pipeline(
            file_path=args.file, provider_name=args.provider, allow_cloud=args.allow_cloud
        )
        payload = {"contract": contract.model_dump(mode="json"), "run": run.model_dump(mode="json")}
        _write_json(args.output, payload)
        print(f"Phase 1 completed. JSON saved at: {args.output}")
        return

    if args.command == "classify":
        contract = _load_contract_json(args.contract_json)
        contract = run_classification(contract, provider_name=args.provider, allow_cloud=args.allow_cloud)
        _write_json(args.output, contract.model_dump(mode="json"))
        print(f"Classification completed. JSON saved at: {args.output}")
        return

    if args.command == "favorability":
        contract = _load_contract_json(args.contract_json)
        balance = run_favorability(contract, provider_name=args.provider, allow_cloud=args.allow_cloud)
        payload = {"contract": contract.model_dump(mode="json"), "balance": balance}
        _write_json(args.output, payload)
        print(f"Favorability completed. JSON saved at: {args.output}")
        return

    if args.command == "modify":
        contract = _load_contract_json(args.contract_json)
        mode = ModificationMode(args.mode)
        target_party = FavorabilityTarget(args.target_party)
        contract = run_modification(
            contract=contract,
            mode=mode,
            target_party=target_party,
            provider_name=args.provider,
            allow_cloud=args.allow_cloud,
        )
        _write_json(args.output, contract.model_dump(mode="json"))
        print(f"Modification completed. JSON saved at: {args.output}")
        return

    if args.command == "report":
        if args.contract_json:
            contract = _load_contract_json(args.contract_json)
        elif args.contract_id:
            contract = load_contract(args.contract_id)
            if not contract:
                raise ValueError("Contract ID not found in SQLite database.")
        else:
            raise ValueError("Provide either --contract-json or --contract-id.")
        artifacts = run_reporting(contract, output_dir=args.output_dir)
        print(json.dumps(artifacts, indent=2))
        return


if __name__ == "__main__":
    main()
