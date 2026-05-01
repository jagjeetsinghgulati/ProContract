from __future__ import annotations

from pathlib import Path

from pipeline import run_phase1_pipeline


def test_phase1_pipeline_txt(tmp_path: Path):
    contract_file = tmp_path / "contract.txt"
    contract_file.write_text(
        """
This Agreement is made between Alpha Systems Private Limited and Beta Industries Limited.

1. Payment Terms
Client shall pay invoice within 30 days.

2. Termination
Either party may terminate this agreement with 30 days notice.
        """.strip(),
        encoding="utf-8",
    )

    contract, run = run_phase1_pipeline(str(contract_file), provider_name="none")
    assert contract.file_name == "contract.txt"
    assert len(contract.clauses) >= 2
    assert len(contract.parties) >= 2
    assert run.stages["segment"].completed
