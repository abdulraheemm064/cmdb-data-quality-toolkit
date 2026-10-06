import json

from cmdb_dq.analysis import analyze
from cmdb_dq.model import Finding
from cmdb_dq.report import to_json, to_markdown, write_reports
from cmdb_dq.scorecard import build_scorecard, grade_for

from .conftest import AS_OF, make_ci


def _f(rule, kpi, sys_id):
    return Finding(rule, kpi, "low", sys_id, sys_id, "cmdb_ci_linux_server", "x")


def test_kpi_counts_affected_cis_not_findings():
    cis = [make_ci(str(i), f"h{i}") for i in range(10)]
    findings = [_f("COR-002", "correctness", "1"), _f("COR-004", "correctness", "1"),
                _f("COMP-001", "completeness", "2")]
    sc = build_scorecard(cis, findings)
    assert sc.kpis["correctness"].score == 90.0
    assert sc.kpis["correctness"].findings == 2
    assert sc.kpis["completeness"].score == 90.0
    assert sc.kpis["compliance"].score == 100.0
    assert sc.overall == round((90 + 90 + 100) / 3, 1)


def test_custom_weights():
    cis = [make_ci("1", "h"), make_ci("2", "h2")]
    sc = build_scorecard(cis, [_f("COMP-001", "completeness", "1")],
                         weights={"completeness": 1, "correctness": 0, "compliance": 0})
    assert sc.overall == 50.0


def test_empty_dataset_scores_100():
    assert build_scorecard([], []).overall == 100.0


def test_grades():
    assert [grade_for(s) for s in (95, 85, 75, 65, 10)] == ["A", "B", "C", "D", "F"]


def test_reports_render(tmp_path, synthetic):
    result = analyze(synthetic, as_of=AS_OF, source="synthetic")
    md = to_markdown(result)
    assert "# CMDB Data Quality Report" in md
    assert "synthetic data" in md
    assert "## Duplicate groups (20)" in md
    payload = to_json(result)
    assert payload["scorecard"]["total_cis"] == 300
    # unmapped values have no suggestion, so they must not appear as one
    assert "Generic OEM" not in {s["current"] for s in payload["normalization_suggestions"]}
    md_path, json_path = write_reports(result, tmp_path)
    assert json.loads(json_path.read_text())["as_of"] == "2026-09-30"
    assert md_path.read_text().startswith("# CMDB")


def test_synthetic_scores_are_stable(synthetic):
    sc = analyze(synthetic, as_of=AS_OF).scorecard
    assert sc.kpis["completeness"].score == 96.0
    assert 0 < sc.kpis["correctness"].score < sc.kpis["compliance"].score < 100
    assert sc.grade in {"B", "C"}
