"""Local append-only, blockchain-style evidence ledger.

This is intentionally a prototype ledger, not a public blockchain. Each
record references the previous block hash, creating a verifiable hash chain.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .hasher import generate_hash

LEDGER_PATH = Path("data/evidence/evidence_ledger.jsonl")


def _read_entries() -> list[dict]:
    if not LEDGER_PATH.exists():
        return []

    entries = []
    with LEDGER_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def add_evidence(
    evidence_id: str,
    evidence_hash: str,
    metadata: dict | None = None,
) -> dict:
    """Append evidence once and return its ledger record."""
    entries = _read_entries()

    for entry in entries:
        if entry.get("evidence_hash") == evidence_hash:
            return entry

    previous_block_hash = (
        entries[-1]["block_hash"] if entries else "GENESIS"
    )

    record = {
        "block_index": len(entries) + 1,
        "evidence_id": evidence_id,
        "evidence_hash": evidence_hash,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "previous_block_hash": previous_block_hash,
        "metadata": metadata or {},
    }

    record["block_hash"] = generate_hash(record)

    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return record


def get_ledger() -> list[dict]:
    """Return all ledger entries."""
    return _read_entries()
