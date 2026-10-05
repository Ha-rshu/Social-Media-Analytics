"""Explainable, local threat scoring for the SIH 26152 prototype."""

from __future__ import annotations

import re

THREAT_TERMS = {
    "phishing": 25,
    "malware": 25,
    "ransomware": 30,
    "credential": 20,
    "password": 15,
    "exploit": 25,
    "hack": 15,
    "breach": 20,
    "stolen": 15,
    "otp": 15,
    "verify": 10,
    "urgent": 8,
    "click now": 15,
    "free gift": 12,
}


def analyze_threat(text: str, url_result: dict | None = None) -> dict:
    """Return a transparent 0-100 risk score and reasons.

    This is an analytical heuristic for a prototype, not a claim that a
    message is malicious.
    """
    text = text if isinstance(text, str) else ""
    lowered = text.lower()

    score = 0
    reasons: list[str] = []

    for term, weight in THREAT_TERMS.items():
        if term in lowered:
            score += weight
            reasons.append(f"Keyword indicator: {term}")

    if re.search(r"(.)\1{6,}", lowered):
        score += 10
        reasons.append("Repeated-character pattern")

    if text.count("!") >= 4:
        score += 8
        reasons.append("High punctuation intensity")

    if any(char.isdigit() for char in text) and len(text) > 180:
        score += 5
        reasons.append("Long message with numeric content")

    if url_result:
        url_score = int(url_result.get("url_risk_score", 0))
        score += round(url_score * 0.45)
        if url_score >= 30:
            reasons.append("Suspicious URL indicators")

    score = min(100, score)

    if score >= 70:
        level = "HIGH"
    elif score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "threat_score": score,
        "threat_level": level,
        "threat_reasons": list(dict.fromkeys(reasons)),
    }
