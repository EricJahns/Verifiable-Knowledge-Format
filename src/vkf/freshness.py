"""Freshness reporting: when should an agent stop trusting a fact?"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from .loader import load_objects

STALE_STATUSES = {"deprecated", "superseded", "retracted", "stale", "archived"}


def _parse_date(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()
        except ValueError:
            return None


def freshness_report(root: str | Path) -> list[dict]:
    rows = []
    today = date.today()
    for obj in load_objects(root):
        valid_until = _parse_date(obj.metadata.get("valid_until"))
        last_verified = _parse_date(obj.metadata.get("last_verified"))
        if valid_until and valid_until < today:
            state = "stale"
        elif obj.status in STALE_STATUSES:
            state = obj.status
        elif valid_until:
            state = "fresh"
        else:
            state = "unknown"
        rows.append({
            "id": obj.display_id,
            "concept_id": obj.concept_id,
            "path": str(obj.path),
            "status": obj.status,
            "freshness": state,
            "last_verified": str(last_verified) if last_verified else None,
            "valid_until": str(valid_until) if valid_until else None,
        })
    return rows
