"""SHA-256 evidence hashing utilities."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonicalize(data: Any) -> str:
    """Convert evidence data into deterministic JSON."""
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def generate_hash(data: Any) -> str:
    """Generate a SHA-256 hash for evidence data."""
    canonical = canonicalize(data)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
