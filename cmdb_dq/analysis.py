"""Run the full pipeline: identify duplicates, run checks, build the scorecard."""

from __future__ import annotations

import logging
from datetime import date

from cmdb_dq.checks import CheckConfig, run_all_checks
from cmdb_dq.identification import find_duplicates
from cmdb_dq.model import Dataset
from cmdb_dq.report import AnalysisResult
from cmdb_dq.scorecard import build_scorecard

log = logging.getLogger(__name__)


def analyze(dataset: Dataset, as_of: date, stale_days: int = 30,
            source: str = "(in-memory)") -> AnalysisResult:
    groups = find_duplicates(dataset.cis)
    findings = run_all_checks(dataset, groups, CheckConfig(as_of=as_of, stale_days=stale_days))
    scorecard = build_scorecard(dataset.cis, findings)
    log.info("Overall health %.1f (%s) with %d findings",
             scorecard.overall, scorecard.grade, len(findings))
    return AnalysisResult(as_of, source, scorecard, findings, groups, dataset.cis)
