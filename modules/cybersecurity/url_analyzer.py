"""Defensive URL risk analysis for the SIH 26152 prototype.

This module performs local, rule-based inspection only. It does not visit URLs,
download content, or make external API calls.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

URL_PATTERN = re.compile(
    r"(?i)\b(?:https?://|www\.)[^\s<>\"]+"
)

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "cutt.ly", "rb.gy", "shorturl.at",
}

SUSPICIOUS_TLDS = {
    ".zip", ".mov", ".click", ".top", ".xyz", ".tk", ".ml", ".ga", ".cf",
}

SUSPICIOUS_TERMS = {
    "login", "verify", "verification", "account", "password", "secure",
    "update", "wallet", "payment", "claim", "urgent", "free", "gift",
}


def extract_urls(text: str) -> list[str]:
    """Extract HTTP(S) or www URLs from text."""
    if not isinstance(text, str):
        return []
    urls = [match.rstrip(".,!?;:)]}") for match in URL_PATTERN.findall(text)]
    return list(dict.fromkeys(urls))


def analyze_url(url: str) -> dict:
    """Return an explainable local risk assessment for one URL."""
    result = {
        "url": url,
        "risk_score": 0,
        "status": "LOW_RISK",
        "reasons": [],
    }

    candidate = url if re.match(r"(?i)^https?://", url) else f"https://{url}"

    try:
        parsed = urlparse(candidate)
        hostname = (parsed.hostname or "").lower()
        path_query = f"{parsed.path} {parsed.query}".lower()

        if not hostname:
            result["risk_score"] += 30
            result["reasons"].append("Invalid or missing hostname")

        if parsed.scheme != "https":
            result["risk_score"] += 10
            result["reasons"].append("Not using HTTPS")

        if re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", hostname):
            result["risk_score"] += 25
            result["reasons"].append("URL uses a raw IP address")

        if "xn--" in hostname:
            result["risk_score"] += 25
            result["reasons"].append("Punycode domain detected")

        if hostname in SHORTENERS:
            result["risk_score"] += 20
            result["reasons"].append("URL shortener detected")

        if any(hostname.endswith(tld) for tld in SUSPICIOUS_TLDS):
            result["risk_score"] += 15
            result["reasons"].append("Higher-risk TLD pattern")

        if hostname.count(".") >= 4:
            result["risk_score"] += 10
            result["reasons"].append("Unusually deep subdomain structure")

        matched_terms = sorted(
            term for term in SUSPICIOUS_TERMS if term in path_query
        )
        if matched_terms:
            result["risk_score"] += min(30, 8 * len(matched_terms))
            result["reasons"].append(
                "Sensitive action terms: " + ", ".join(matched_terms[:4])
            )

        if len(url) > 180:
            result["risk_score"] += 10
            result["reasons"].append("Unusually long URL")

    except ValueError:
        result["risk_score"] += 30
        result["reasons"].append("Malformed URL")

    result["risk_score"] = min(100, result["risk_score"])

    if result["risk_score"] >= 60:
        result["status"] = "HIGH_RISK"
    elif result["risk_score"] >= 30:
        result["status"] = "MEDIUM_RISK"

    return result


def analyze_text_urls(text: str) -> dict:
    """Analyze all URLs in a message and return an aggregate result."""
    urls = extract_urls(text)
    assessments = [analyze_url(url) for url in urls]

    if assessments:
        max_risk = max(item["risk_score"] for item in assessments)
        suspicious = [item["url"] for item in assessments if item["risk_score"] >= 30]
        reasons = list(
            dict.fromkeys(
                reason
                for item in assessments
                for reason in item["reasons"]
            )
        )
    else:
        max_risk = 0
        suspicious = []
        reasons = []

    return {
        "urls": urls,
        "url_count": len(urls),
        "suspicious_urls": suspicious,
        "url_risk_score": max_risk,
        "url_reasons": reasons,
        "url_assessments": assessments,
    }
