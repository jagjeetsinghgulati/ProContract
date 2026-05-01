from __future__ import annotations

from pathlib import Path

from data_model.enums import FavorabilityTarget, ModificationMode
from pipeline import (
    run_classification,
    run_favorability,
    run_modification,
    run_phase1_pipeline,
    run_reporting,
)


def test_full_pipeline_with_exports(tmp_path: Path):
    contract_file = tmp_path / "contract.txt"
    contract_file.write_text(
        """
This Agreement is made between Party 1 and Party 2.

1. Liability
Supplier shall indemnify Buyer for all losses and pay penalties.

2. Governing Law
This agreement is governed by the laws of India.
        """.strip(),
        encoding="utf-8",
    )

    contract, _ = run_phase1_pipeline(str(contract_file), provider_name="none")
    contract = run_classification(contract, provider_name="none")
    balance = run_favorability(contract, provider_name="none")
    assert "tilt_party" in balance

    contract = run_modification(
        contract,
        mode=ModificationMode.BALANCED,
        target_party=FavorabilityTarget.PARTY_1,
        provider_name="none",
    )
    artifacts = run_reporting(contract, output_dir=str(tmp_path / "output"))
    for path in artifacts.values():
        assert Path(path).exists()
