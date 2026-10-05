"""Evidence and ledger verification utilities."""

from __future__ import annotations

from .hasher import generate_hash
from .ledger import get_ledger


def verify_evidence(evidence_hash: str) -> dict:
    """Verify whether an evidence hash exists in the local ledger."""
    entries = get_ledger()

    matching = [
        entry for entry in entries
        if entry.get("evidence_hash") == evidence_hash
    ]

    if not matching:
        return {
            "verified": False,
            "message": "Evidence hash not found in ledger.",
        }

    entry = matching[0]

    block_copy = dict(entry)
    stored_block_hash = block_copy.pop("block_hash", None)
    recalculated_block_hash = generate_hash(block_copy)

    valid_block = stored_block_hash == recalculated_block_hash

    return {
        "verified": valid_block,
        "message": (
            "Evidence and ledger block verified."
            if valid_block
            else "Ledger block integrity check failed."
        ),
        "entry": entry,
    }


def verify_chain() -> dict:
    """Verify every previous-block link and block hash."""
    entries = get_ledger()
    previous = "GENESIS"

    for entry in entries:
        if entry.get("previous_block_hash") != previous:
            return {
                "verified": False,
                "message": f"Broken chain at block {entry.get('block_index')}.",
            }

        block_copy = dict(entry)
        stored_hash = block_copy.pop("block_hash", None)
        if generate_hash(block_copy) != stored_hash:
            return {
                "verified": False,
                "message": f"Invalid block hash at block {entry.get('block_index')}.",
            }

        previous = stored_hash

    return {
        "verified": True,
        "message": f"{len(entries)} ledger blocks verified.",
    }
