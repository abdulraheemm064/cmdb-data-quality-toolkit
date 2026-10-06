"""Render the analysis as Markdown and JSON."""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from cmdb_dq import __version__
from cmdb_dq.checks import RULES
from cmdb_dq.identification import DuplicateGroup
from cmdb_dq.model import Finding
from cmdb_dq.normalize import NORMALIZABLE, normalize_manufacturer, normalize_os
from cmdb_dq.scorecard import Scorecard

DISCLAIMER = ("Generated from synthetic data for a representative portfolio project. "
              "Not derived from any employer or client code or data.")

RECOMMENDATIONS = {
    "COMP-001": "Make the attributes mandatory on the ingest path (Import Set transform or "
                "discovery pattern) rather than on the form only.",
    "COR-001": "Review identifier rules and data-source precedence; merge or retire the "
               "non-master records and fix the source that created them.",
    "COR-002": "Load the variants into the normalization lookup so new records are "
               "corrected on insert.",
    "COR-003": "Add the vendor to the manufacturer normalization table (or the company table).",
    "COR-004": "Add OS normalization rules so reporting and lifecycle data line up.",
    "COR-005": "Exclude placeholder serials from identification; fix the BIOS/OEM data at source.",
    "COR-006": "Map the CI to an application service or confirm it should be retired.",
    "COR-007": "Check MID Server reachability/credentials for the subnet, or retire the CI.",
    "COR-008": "Delete or repair relationships that reference CIs which no longer exist.",
    "CSDM-001": "Create the application service(s) for each environment and link them.",
    "CSDM-002": "Link the service to its business application via 'Consumes::Consumed by'.",
    "CSDM-003": "Run Service Mapping or tag-based mapping to populate the service.",
    "CSDM-004": "Assign an accountable owner; route through the data certification process.",
    "CSDM-005": "Assign a support group so incidents and changes route correctly.",
    "CSDM-006": "Remove relationships from retired CIs as part of the retirement workflow.",
    "CSDM-007": "Replace the direct relationship with the correct CSDM layer "
                "(business app -> application service -> infrastructure).",
}


@dataclass
class AnalysisResult:
    as_of: date
    source: str
    scorecard: Scorecard
    findings: list[Finding]
    duplicate_groups: list[DuplicateGroup]
    cis: list[dict]


def normalization_suggestions(cis: list[dict]) -> list[dict]:
    counts: Counter = Counter()
    for ci in cis:
        for field_name, fn in (("manufacturer", normalize_manufacturer), ("os", normalize_os)):
            value = ci.get(field_name, "")
            canonical, status = fn(value)
            if status == NORMALIZABLE:
                counts[(field_name, value, canonical)] += 1
    return [{"field": f, "current": cur, "suggested": sug, "count": n}
            for (f, cur, sug), n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]


def to_json(result: AnalysisResult) -> dict:
    return {
        "tool": "cmdb-data-quality-toolkit",
        "version": __version__,
        "as_of": result.as_of.isoformat(),
        "source": result.source,
        "disclaimer": DISCLAIMER,
        "scorecard": result.scorecard.to_dict(),
        "duplicate_groups": [g.to_dict() for g in result.duplicate_groups],
        "normalization_suggestions": normalization_suggestions(result.cis),
        "findings": [f.to_dict() for f in result.findings],
    }


def _table(headers: list[str], rows: list[list]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |" for row in rows]
    return lines


def to_markdown(result: AnalysisResult, max_rows: int = 15) -> str:
    sc = result.scorecard
    out = [
        "# CMDB Data Quality Report",
        "",
        f"> {DISCLAIMER}",
        "",
        f"- **Source:** `{result.source}`",
        f"- **As of:** {result.as_of.isoformat()}",
        f"- **CIs analysed:** {sc.total_cis}",
        f"- **Overall health:** **{sc.overall} / 100 (grade {sc.grade})**",
        "",
        "## Scorecard",
        "",
    ]
    out += _table(["KPI", "Score", "CIs affected", "Findings"],
                  [[k.capitalize(), f"{v.score}", v.affected_cis, v.findings]
                   for k, v in sc.kpis.items()])
    out += ["", "Score = share of CIs with no finding for that KPI. "
            "Overall = weighted mean of the three KPIs (equal weights by default).", ""]

    out += ["## Findings by rule", ""]
    out += _table(["Rule", "KPI", "Severity", "Description", "Count"],
                  [[rid, RULES[rid].kpi, RULES[rid].severity, RULES[rid].title, n]
                   for rid, n in sc.by_rule.items()])

    out += ["", "## Affected CIs by class", ""]
    out += _table(["Class", "Total", "Affected", "% affected"],
                  [[cls, d["total"], d["affected"],
                    f"{(100 * d['affected'] / d['total']) if d['total'] else 0:.0f}%"]
                   for cls, d in sc.by_class.items()])

    out += ["", f"## Duplicate groups ({len(result.duplicate_groups)})", ""]
    if result.duplicate_groups:
        rows = [[g.master["name"], g.master.get("discovery_source", ""),
                 ", ".join(f"{d['name']} ({d.get('discovery_source', '')})" for d in g.duplicates),
                 ", ".join(g.matched_on)]
                for g in result.duplicate_groups[:max_rows]]
        out += _table(["Master (kept)", "Master source", "Duplicates", "Matched on"], rows)
        if len(result.duplicate_groups) > max_rows:
            out += ["", f"_...and {len(result.duplicate_groups) - max_rows} more (see JSON)._"]
    else:
        out += ["No duplicates found."]

    suggestions = normalization_suggestions(result.cis)
    out += ["", "## Normalization suggestions", ""]
    if suggestions:
        out += _table(["Field", "Current value", "Suggested", "Records"],
                      [[s["field"], s["current"], s["suggested"], s["count"]]
                       for s in suggestions[:max_rows]])
    else:
        out += ["All manufacturer and OS values are normalized."]

    out += ["", "## Sample findings (up to 3 per rule, highest severity first)", ""]
    severity_rank = {"high": 0, "medium": 1, "low": 2}
    ranked = sorted(result.findings, key=lambda f: (severity_rank[f.severity], f.rule_id, f.name))
    per_rule: Counter = Counter()
    sample = []
    for f in ranked:
        if per_rule[f.rule_id] < 3:
            per_rule[f.rule_id] += 1
            sample.append(f)
    out += _table(["Rule", "Severity", "CI", "Class", "Detail"],
                  [[f.rule_id, f.severity, f.name, f.sys_class_name, f.message] for f in sample])
    out += ["", "_Full finding list is in the JSON report._"]

    out += ["", "## Recommended remediation", ""]
    for rid in sc.by_rule:
        out.append(f"- **{rid}** - {RECOMMENDATIONS[rid]}")
    out.append("")
    return "\n".join(out)


def write_reports(result: AnalysisResult, out_dir: str | Path) -> tuple[Path, Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path, json_path = out_dir / "cmdb-health-report.md", out_dir / "cmdb-health-report.json"
    md_path.write_text(to_markdown(result), encoding="utf-8")
    json_path.write_text(json.dumps(to_json(result), indent=2) + "\n", encoding="utf-8")
    return md_path, json_path
