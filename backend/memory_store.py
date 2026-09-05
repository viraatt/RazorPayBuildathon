"""Tiny in-memory fallback store so the demo + API work without Postgres.

Used when the Postgres pool cannot be reached: batches/listings, matched
pairs, and exceptions are kept in process memory instead of DB tables."""

from datetime import datetime, timezone

_batches: dict[str, dict] = {}
_matches: dict[str, list] = {}
_exceptions: dict[str, list] = {}
_bank_records: dict[str, list] = {}
_ledger_records: dict[str, list] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def put_batch(data: dict) -> None:
    d = dict(data)
    prev = _batches.get(d.get("id"), {})
    d.setdefault("name", prev.get("name", ""))
    d.setdefault("created_at", prev.get("created_at", _now()))
    d["updated_at"] = _now()
    _batches[d["id"]] = d


def get_batch(batch_id: str) -> dict | None:
    return _batches.get(batch_id)


def list_batches(limit: int = 20) -> list[dict]:
    rows = sorted(_batches.values(), key=lambda r: r.get("created_at", ""), reverse=True)
    return rows[:limit]


def put_batch_matches(batch_id: str, rows: list[dict]) -> None:
    _matches[batch_id] = [dict(r) for r in rows]


def get_batch_matches(batch_id: str) -> list[dict]:
    return _matches.get(batch_id, [])


def put_batch_exceptions(batch_id: str, rows: list[dict]) -> None:
    _exceptions[batch_id] = [dict(r) for r in rows]


def get_batch_exceptions(batch_id: str) -> list[dict]:
    return _exceptions.get(batch_id, [])


def put_batch_records(
    batch_id: str, bank_records: list[dict], ledger_records: list[dict]
) -> None:
    """Persist the raw uploaded/reference records per batch for offline mode.

    Without this, an upload while Postgres is unreachable would return a batch
    id that /api/reconcile could never populate (silently reconciling nothing).
    """
    _bank_records[batch_id] = [dict(r) for r in bank_records]
    _ledger_records[batch_id] = [dict(r) for r in ledger_records]


def get_batch_records(batch_id: str) -> tuple[list[dict], list[dict]]:
    return _bank_records.get(batch_id, []), _ledger_records.get(batch_id, [])