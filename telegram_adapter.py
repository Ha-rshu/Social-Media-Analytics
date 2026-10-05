import json
from pathlib import Path

import pandas as pd


TELEGRAM_FILE = (
    Path(__file__).resolve().parent
    / "telegram_messages.jsonl"
)

def load_telegram_data():
    """Load Telegram JSONL messages into a Pandas DataFrame."""

    if not TELEGRAM_FILE.exists():
        print("No Telegram data file found.")
        return pd.DataFrame()

    records = []

    with TELEGRAM_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                print("Skipped invalid JSON line.")

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    # Convert timestamp to datetime
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce",
            utc=True
        )

    # Ensure expected columns exist
    expected_columns = [
        "id",
        "timestamp",
        "platform",
        "user_id",
        "text",
        "target_user",
    ]

    for column in expected_columns:
        if column not in df.columns:
            df[column] = None

    return df[expected_columns]


if __name__ == "__main__":
    df = load_telegram_data()

    print("\nTelegram DataFrame")
    print("-" * 60)

    print(df.to_string(index=False))

    print("\nShape:")
    print(df.shape)

    print("\nColumns:")
    print(list(df.columns))