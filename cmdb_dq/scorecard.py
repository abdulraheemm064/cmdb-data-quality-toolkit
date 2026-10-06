"""Health scorecard: per-KPI scores, overall score and grade."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from cmdb_dq.checks import RULES
from cmdb_dq.model import Finding, family_of

KPIS = ("completeness", "correctness", "compliance")
DEFAULT_WEIGHTS = {"completeness": 1.0, "correctness": 1.0, "compliance": 1.0}


@dataclass
class KpiScore:
    kpi: str
    score: float
    affected_cis: int
    findings: int


@dataclass
class Scorecard:
    total_cis: int
    kpis: dict[str, KpiScore]
    overall: float
    grade: str
    by_rule: dict[str, int] = field(default_factory=dict)
    by_class: dict[str, dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "total_cis": self.total_cis,
            "overall_score": self.overall,
            "grade": self.grade,
            "kpis": {k: vars(v) for k, v in self.kpis.items()},
            "findings_by_rule": self.by_rule,
            "affected_cis_by_class": self.by_class,
        }


def grade_for(score: float) -> str:
    for threshold, grade in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
        if score >= threshold:
            return grade
    return "F"


def build_scorecard(cis: list[dict], findings: list[Finding],
                    weights: dict[str, float] | None = None) -> Scorecard:
    weights = weights or DEFAULT_WEIGHTS
    total = len(cis)
    kpis: dict[str, KpiScore] = {}
    for kpi in KPIS:
        kpi_findings = [f for f in findings if f.kpi == kpi]
        affected = {f.sys_id for f in kpi_findings}
        score = 100.0 if total == 0 else round(100.0 * (1 - len(affected) / total), 1)
        kpis[kpi] = KpiScore(kpi, max(score, 0.0), len(affected), len(kpi_findings))

    weight_sum = sum(weights.get(k, 0.0) for k in KPIS) or 1.0
    overall = round(sum(kpis[k].score * weights.get(k, 0.0) for k in KPIS) / weight_sum, 1)

    by_rule = Counter(f.rule_id for f in findings)
    class_names = {ci["sys_id"]: ci["sys_class_name"] for ci in cis}
    affected_by_class: dict[str, set[str]] = {}
    for f in findings:
        cls = class_names.get(f.sys_id, f.sys_class_name or "(unknown)")
        affected_by_class.setdefault(cls, set()).add(f.sys_id)
    totals_by_class = Counter(ci["sys_class_name"] for ci in cis)
    by_class = {
        cls: {"total": totals_by_class.get(cls, 0), "affected": len(ids),
              "family": family_of(cls)}
        for cls, ids in sorted(affected_by_class.items())
    }
    return Scorecard(total, kpis, overall, grade_for(overall),
                     {r: by_rule[r] for r in RULES if by_rule.get(r)}, by_class)
