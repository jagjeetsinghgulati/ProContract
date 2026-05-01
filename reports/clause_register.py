from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_model.schema import ContractModel


def export_clause_register(contract: ContractModel, output_path: str | Path) -> Path:
    rows = []
    for clause in contract.clauses:
        rows.append(
            {
                "Clause ID": clause.clause_id,
                "Heading": clause.heading,
                "Text": clause.text,
                "Primary Category": (
                    clause.classification.primary_category.value
                    if clause.classification
                    else ""
                ),
                "Criticality": (
                    clause.classification.criticality.value if clause.classification else ""
                ),
                "Red Flag": clause.classification.red_flag if clause.classification else False,
                "Beneficiary": (
                    clause.favorability.beneficiary.value if clause.favorability else ""
                ),
                "Risk": clause.favorability.risk_level.value if clause.favorability else "",
            }
        )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_excel(output, index=False)
    return output
