from __future__ import annotations

import re


RED_FLAG_PATTERNS: dict[str, str] = {
    "unlimited_liability": r"(?i)\bunlimited liability\b",
    "sole_discretion": r"(?i)\bsole discretion\b",
    "no_termination_right": r"(?i)\bno right to terminate\b",
    "indemnify_without_limit": r"(?i)\bindemnif(?:y|ication).{0,40}without limit\b",
    "automatic_renewal_hidden": r"(?i)\bautomatically renew(?:s|ed)?\b",
}


def detect_red_flags(text: str) -> tuple[bool, list[str]]:
    findings: list[str] = []
    for name, pattern in RED_FLAG_PATTERNS.items():
        if re.search(pattern, text):
            findings.append(name)
    return (len(findings) > 0, findings)
