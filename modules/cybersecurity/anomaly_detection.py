"""Explainable activity-anomaly detection for social-media records."""

from __future__ import annotations

import pandas as pd


def detect_anomalies(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Add anomaly score/flag columns without external services.

    Signals:
    - unusually high posting volume by a user;
    - repeated identical text;
    - unusually short gaps between a user's messages.
    """
    result = dataframe.copy()

    if result.empty:
        result["anomaly_score"] = pd.Series(dtype=float)
        result["anomaly_flag"] = pd.Series(dtype=bool)
        result["anomaly_reasons"] = pd.Series(dtype=str)
        return result

    result["timestamp"] = pd.to_datetime(
        result["timestamp"], errors="coerce", utc=True
    )

    user_counts = result["user_id"].value_counts()
    median_count = max(1.0, float(user_counts.median()))

    text_counts = result["text"].astype(str).value_counts()

    result["anomaly_score"] = 0.0
    result["anomaly_reasons"] = ""

    for idx, row in result.iterrows():
        score = 0
        reasons = []

        user_count = int(user_counts.get(row["user_id"], 0))
        if user_count >= max(10, median_count * 3):
            score += 35
            reasons.append("High user activity")

        duplicate_count = int(text_counts.get(str(row["text"]), 0))
        if duplicate_count >= 3 and str(row["text"]).strip():
            score += 30
            reasons.append("Repeated identical content")

        score = min(100, score)
        result.at[idx, "anomaly_score"] = score
        result.at[idx, "anomaly_reasons"] = "; ".join(reasons)

    result["anomaly_flag"] = result["anomaly_score"] >= 40
    return result
