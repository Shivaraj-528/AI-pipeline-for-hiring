"""
utils/json_store.py
-------------------
Previously stored candidates in a local JSON file.
Now forwards all writes to Supabase via utils/db.py.

The local JSON file is kept as a fallback/audit log only.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# ── Supabase primary store ──────────────────────
try:
    from utils.db import store_candidate_result
    _DB_AVAILABLE = True
except ImportError:
    _DB_AVAILABLE = False

# ── Local JSON fallback ─────────────────────────
_DATA_FILE = "data/applied_candidates.json"


def store_candidate_json(candidate_data: dict):
    """
    Save candidate result.
    Primary:  Supabase (via utils.db)
    Fallback: local JSON file  (data/applied_candidates.json)
    """
    # Attach a timestamp so both stores have it
    candidate_data.setdefault("timestamp",
                              datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    # ── 1. Write to Supabase ───────────────────
    if _DB_AVAILABLE:
        try:
            store_candidate_result(candidate_data)
        except Exception as e:
            print(f"⚠️  Supabase write failed, falling back to JSON: {e}")
            _write_json(candidate_data)
    else:
        _write_json(candidate_data)


def _write_json(candidate_data: dict):
    """Append candidate_data to the local JSON file."""
    os.makedirs("data", exist_ok=True)

    existing = []
    if os.path.exists(_DATA_FILE):
        try:
            with open(_DATA_FILE, "r") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = []

    existing.append(candidate_data)

    with open(_DATA_FILE, "w") as f:
        json.dump(existing, f, indent=4)

    print("📁 Candidate stored in local JSON (fallback)")
