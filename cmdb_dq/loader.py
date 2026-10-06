"""Load and save CMDB exports (JSON or CSV)."""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from cmdb_dq.model import CI_FIELDS, REL_FIELDS, Dataset

log = logging.getLogger(__name__)


class LoaderError(ValueError):
    """Raised when an export cannot be parsed."""


def _clean(row: dict) -> dict:
    return {k: ("" if v is None else str(v).strip()) for k, v in row.items() if k is not None}


def _validate(dataset: Dataset) -> Dataset:
    seen: set[str] = set()
    for idx, ci in enumerate(dataset.cis):
        sys_id = ci.get("sys_id", "")
        if not sys_id:
            raise LoaderError(f"CI at position {idx} has no sys_id")
        if sys_id in seen:
            raise LoaderError(f"sys_id {sys_id} appears more than once in the export")
        seen.add(sys_id)
        for col in CI_FIELDS:
            ci.setdefault(col, "")
    for idx, rel in enumerate(dataset.relationships):
        missing = [c for c in REL_FIELDS if not rel.get(c)]
        if missing:
            raise LoaderError(f"Relationship at position {idx} is missing {missing}")
    return dataset


def load_json(path: Path) -> Dataset:
    with path.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    if isinstance(payload, list):
        cis, rels = payload, []
    elif isinstance(payload, dict):
        # Accept both our own shape and the "records" key used by REST/JSONv2 exports.
        cis = payload.get("cis", payload.get("records", []))
        rels = payload.get("relationships", [])
    else:
        raise LoaderError("Unsupported JSON structure: expected an object or a list")
    return Dataset([_clean(r) for r in cis], [_clean(r) for r in rels])


def load_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return [_clean(r) for r in csv.DictReader(fh)]


def load_dataset(path: str | Path, relationships_path: str | Path | None = None) -> Dataset:
    path = Path(path)
    if not path.exists():
        raise LoaderError(f"Input file not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".json":
        dataset = load_json(path)
    elif suffix == ".csv":
        dataset = Dataset(load_csv(path), [])
    else:
        raise LoaderError(f"Unsupported file type '{suffix}' (use .json or .csv)")
    if relationships_path:
        dataset.relationships = load_csv(Path(relationships_path))
    log.info("Loaded %d CIs and %d relationships from %s",
             len(dataset.cis), len(dataset.relationships), path)
    return _validate(dataset)


def save_json(dataset: Dataset, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump({"cis": dataset.cis, "relationships": dataset.relationships}, fh, indent=2)
        fh.write("\n")


def save_csv(dataset: Dataset, ci_path: str | Path, rel_path: str | Path) -> None:
    for target, rows, cols in ((ci_path, dataset.cis, CI_FIELDS),
                               (rel_path, dataset.relationships, REL_FIELDS)):
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
