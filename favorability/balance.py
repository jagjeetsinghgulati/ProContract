from __future__ import annotations

from collections import defaultdict

from data_model.schema import ClauseModel


def calculate_contract_balance(clauses: list[ClauseModel]) -> dict:
    aggregate = defaultdict(int)
    counts = defaultdict(int)

    for clause in clauses:
        if not clause.favorability:
            continue
        for party, score in clause.favorability.scores_by_party.items():
            aggregate[party] += score
            counts[party] += 1

    averages = {party: (aggregate[party] / counts[party]) for party in aggregate if counts[party] > 0}
    if not averages:
        return {
            "tilt_party": "Neutral",
            "balance_score": 0.0,
            "averages": {},
            "top_imbalanced_clauses": [],
        }

    sorted_parties = sorted(averages.items(), key=lambda item: item[1], reverse=True)
    tilt_party = sorted_parties[0][0]
    spread = sorted_parties[0][1] - sorted_parties[-1][1] if len(sorted_parties) > 1 else 0.0

    imbalanced = []
    for clause in clauses:
        if not clause.favorability:
            continue
        scores = list(clause.favorability.scores_by_party.values())
        if scores:
            imbalanced.append((max(scores) - min(scores), clause))
    imbalanced.sort(key=lambda item: item[0], reverse=True)

    return {
        "tilt_party": tilt_party if spread > 0.2 else "Neutral",
        "balance_score": round(spread, 2),
        "averages": {k: round(v, 2) for k, v in averages.items()},
        "top_imbalanced_clauses": [c.clause_id for _, c in imbalanced[:5]],
    }
