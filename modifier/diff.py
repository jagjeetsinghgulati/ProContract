from __future__ import annotations

import difflib

from data_model.schema import ClauseDiffModel


def build_clause_diff(original: str, proposed: str) -> ClauseDiffModel:
    original_lines = original.splitlines()
    proposed_lines = proposed.splitlines()
    diff = list(difflib.ndiff(original_lines, proposed_lines))
    added = [line[2:] for line in diff if line.startswith("+ ")]
    removed = [line[2:] for line in diff if line.startswith("- ")]
    changed = bool(added or removed)
    summary = f"{len(added)} line(s) added, {len(removed)} line(s) removed."
    return ClauseDiffModel(added_lines=added, removed_lines=removed, changed=changed, summary=summary)
