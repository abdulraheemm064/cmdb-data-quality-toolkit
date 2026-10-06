"""Command line interface.

    python -m cmdb_dq generate --out data/sample_cmdb_export.json
    python -m cmdb_dq analyze --input data/sample_cmdb_export.json --out-dir reports
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

from cmdb_dq import __version__
from cmdb_dq.analysis import analyze
from cmdb_dq.loader import LoaderError, load_dataset, save_csv, save_json
from cmdb_dq.model import Dataset
from cmdb_dq.normalize import apply_normalization
from cmdb_dq.report import write_reports
from cmdb_dq.synthetic import generate

log = logging.getLogger("cmdb_dq")

EXIT_OK, EXIT_INPUT_ERROR, EXIT_BELOW_THRESHOLD = 0, 1, 2


def _iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"not an ISO date (YYYY-MM-DD): {value}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cmdb_dq", description="CMDB data quality scorecard (synthetic-data portfolio demo)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate", help="write a synthetic CMDB export")
    gen.add_argument("--out", required=True, help="output .json, or a directory for CSV")
    gen.add_argument("--format", choices=["json", "csv"], default="json")
    gen.add_argument("--seed", type=int, default=42)
    gen.add_argument("--as-of", type=_iso_date, default=date(2026, 9, 30))

    ana = sub.add_parser("analyze", help="analyse an export and write the health report")
    ana.add_argument("--input", required=True, help="CI export (.json or .csv)")
    ana.add_argument("--relationships", help="relationship CSV (parent,child,type) for CSV input")
    ana.add_argument("--out-dir", default="reports")
    ana.add_argument("--as-of", type=_iso_date, default=date.today(),
                     help="reference date for staleness (default: today)")
    ana.add_argument("--stale-days", type=int, default=30)
    ana.add_argument("--export-normalized", help="write a normalized copy of the export (.json)")
    ana.add_argument("--fail-under", type=float, default=None,
                     help="exit with code 2 if the overall score is below this value")
    return parser


def cmd_generate(args: argparse.Namespace) -> int:
    dataset = generate(seed=args.seed, as_of=args.as_of)
    if args.format == "json":
        save_json(dataset, args.out)
        log.info("Wrote %d CIs to %s", len(dataset.cis), args.out)
    else:
        out = Path(args.out)
        save_csv(dataset, out / "cmdb_ci.csv", out / "cmdb_rel_ci.csv")
        log.info("Wrote CSV export to %s", out)
    return EXIT_OK


def cmd_analyze(args: argparse.Namespace) -> int:
    try:
        dataset = load_dataset(args.input, args.relationships)
    except (LoaderError, OSError) as exc:
        log.error("Could not load input: %s", exc)
        return EXIT_INPUT_ERROR
    result = analyze(dataset, as_of=args.as_of, stale_days=args.stale_days,
                     source=Path(args.input).name)
    md_path, json_path = write_reports(result, args.out_dir)
    sc = result.scorecard
    print(f"Overall health: {sc.overall}/100 (grade {sc.grade})")
    for kpi in sc.kpis.values():
        print(f"  {kpi.kpi:<13} {kpi.score:>6}  ({kpi.affected_cis} CIs affected)")
    print(f"Reports: {md_path} , {json_path}")

    if args.export_normalized:
        normalized, changed = apply_normalization(dataset.cis)
        save_json(Dataset(normalized, dataset.relationships), args.export_normalized)
        log.info("Normalized %d values -> %s", changed, args.export_normalized)

    if args.fail_under is not None and sc.overall < args.fail_under:
        log.warning("Overall score %.1f is below threshold %.1f", sc.overall, args.fail_under)
        return EXIT_BELOW_THRESHOLD
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                        stream=sys.stderr)
    handlers = {"generate": cmd_generate, "analyze": cmd_analyze}
    return handlers[args.command](args)
