"""Data quality rules grouped by KPI: completeness, correctness and compliance.

The KPI split follows the same idea as CMDB Health dashboards:

* completeness - are the attributes a CI class needs populated?
* correctness  - is the data right (no duplicates, orphans, stale or unnormalized values)?
* compliance   - does the data follow the governance model (CSDM layering and ownership)?

Ownership (owned_by / support_group) is evaluated under compliance only, so the
same gap is not counted twice.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from cmdb_dq.identification import DuplicateGroup, is_placeholder
from cmdb_dq.model import (
    DISCOVERABLE_FAMILIES,
    INFRA_FAMILIES,
    Dataset,
    Finding,
    family_of,
    is_retired,
)
from cmdb_dq.normalize import NORMALIZABLE, UNMAPPED, normalize_manufacturer, normalize_os


@dataclass(frozen=True)
class Rule:
    rule_id: str
    kpi: str
    severity: str
    title: str


RULES: dict[str, Rule] = {r.rule_id: r for r in [
    Rule("COMP-001", "completeness", "medium", "Required attributes missing"),
    Rule("COR-001", "correctness", "high", "Duplicate CI (not the reconciled master)"),
    Rule("COR-002", "correctness", "low", "Manufacturer not normalized"),
    Rule("COR-003", "correctness", "medium", "Manufacturer not in normalization table"),
    Rule("COR-004", "correctness", "low", "OS name not normalized"),
    Rule("COR-005", "correctness", "medium", "Placeholder serial number"),
    Rule("COR-006", "correctness", "medium", "Orphan infrastructure CI (no relationships)"),
    Rule("COR-007", "correctness", "medium", "Stale discovery date"),
    Rule("COR-008", "correctness", "high", "Relationship references unknown CI"),
    Rule("CSDM-001", "compliance", "high", "Business application has no application service"),
    Rule("CSDM-002", "compliance", "high", "Application service not linked to a business application"),
    Rule("CSDM-003", "compliance", "high", "Application service has no infrastructure dependency"),
    Rule("CSDM-004", "compliance", "medium", "Missing owner (owned_by)"),
    Rule("CSDM-005", "compliance", "medium", "Missing support group"),
    Rule("CSDM-006", "compliance", "medium", "Retired CI still related to active CIs"),
    Rule("CSDM-007", "compliance", "low", "Relationship type not allowed for class pair"),
]}

REQUIRED_FIELDS: dict[str, list[str]] = {
    "business_app": ["name", "business_criticality"],
    "app_service": ["name", "environment"],
    "server": ["name", "serial_number", "ip_address", "os", "manufacturer"],
    "database": ["name", "ip_address", "manufacturer"],
    "network": ["name", "serial_number", "ip_address", "manufacturer"],
}

CONSUMES = "Consumes::Consumed by"
DEPENDS_ON = "Depends on::Used by"
RUNS_ON = "Runs on::Runs"
HOSTED_ON = "Hosted on::Hosts"

ALLOWED_RELATIONSHIPS: dict[tuple[str, str], set[str]] = {
    ("business_app", "app_service"): {CONSUMES},
    ("app_service", "app_service"): {DEPENDS_ON},
    ("app_service", "server"): {DEPENDS_ON},
    ("app_service", "database"): {DEPENDS_ON},
    ("app_service", "network"): {DEPENDS_ON},
    ("database", "server"): {RUNS_ON},
    ("server", "server"): {RUNS_ON, HOSTED_ON, DEPENDS_ON},
    ("server", "database"): {DEPENDS_ON},
}


@dataclass
class CheckConfig:
    as_of: date
    stale_days: int = 30


def _finding(rule_id: str, ci: dict, message: str) -> Finding:
    rule = RULES[rule_id]
    return Finding(rule.rule_id, rule.kpi, rule.severity, ci.get("sys_id", ""),
                   ci.get("name", ""), ci.get("sys_class_name", ""), message)


def check_completeness(dataset: Dataset) -> list[Finding]:
    findings = []
    for ci in dataset.cis:
        if is_retired(ci):
            continue
        required = REQUIRED_FIELDS.get(family_of(ci["sys_class_name"]), ["name"])
        missing = [f for f in required if not ci.get(f)]
        if missing:
            findings.append(_finding("COMP-001", ci, f"Missing: {', '.join(missing)}"))
    return findings


def check_duplicates(groups: list[DuplicateGroup]) -> list[Finding]:
    findings = []
    for group in groups:
        for dup in group.duplicates:
            findings.append(_finding(
                "COR-001", dup,
                f"Duplicate of {group.master['name']} ({group.master['sys_id']}) "
                f"matched on {', '.join(group.matched_on)}"))
    return findings


def check_normalization(dataset: Dataset) -> list[Finding]:
    findings = []
    for ci in dataset.cis:
        canonical, status = normalize_manufacturer(ci.get("manufacturer", ""))
        if status == NORMALIZABLE:
            findings.append(_finding("COR-002", ci,
                                     f"'{ci['manufacturer']}' should be '{canonical}'"))
        elif status == UNMAPPED:
            findings.append(_finding("COR-003", ci,
                                     f"'{ci['manufacturer']}' has no normalization entry"))
        canonical, status = normalize_os(ci.get("os", ""))
        if status in (NORMALIZABLE, UNMAPPED):
            target = f"should be '{canonical}'" if canonical else "has no normalization rule"
            findings.append(_finding("COR-004", ci, f"OS '{ci['os']}' {target}"))
        if family_of(ci["sys_class_name"]) in {"server", "network"}:
            serial = ci.get("serial_number", "")
            if serial and is_placeholder(serial):
                findings.append(_finding("COR-005", ci, f"Serial number '{serial}' is a placeholder"))
    return findings


def _adjacency(dataset: Dataset) -> dict[str, list[tuple[str, str, str]]]:
    """sys_id -> list of (direction, other_sys_id, type)."""
    adj: dict[str, list[tuple[str, str, str]]] = {}
    for rel in dataset.relationships:
        adj.setdefault(rel["parent"], []).append(("child", rel["child"], rel["type"]))
        adj.setdefault(rel["child"], []).append(("parent", rel["parent"], rel["type"]))
    return adj


def check_relationships(dataset: Dataset, config: CheckConfig) -> list[Finding]:
    findings = []
    cis = dataset.by_id()
    adj = _adjacency(dataset)

    for rel in dataset.relationships:
        parent, child = cis.get(rel["parent"]), cis.get(rel["child"])
        if parent is None or child is None:
            anchor = parent or child or {"sys_id": rel["parent"], "name": "(unknown)",
                                         "sys_class_name": ""}
            missing = rel["child"] if parent else rel["parent"]
            findings.append(_finding("COR-008", anchor,
                                     f"Relationship '{rel['type']}' points to missing CI {missing}"))
            continue
        pair = (family_of(parent["sys_class_name"]), family_of(child["sys_class_name"]))
        if rel["type"] not in ALLOWED_RELATIONSHIPS.get(pair, set()):
            findings.append(_finding(
                "CSDM-007", parent,
                f"'{rel['type']}' from {pair[0]} to {pair[1]} ({child['name']}) is not an "
                "allowed CSDM pattern"))

    stale_cutoff = config.as_of - timedelta(days=config.stale_days)
    for ci in dataset.cis:
        fam = family_of(ci["sys_class_name"])
        links = [(d, cis[o], t) for d, o, t in adj.get(ci["sys_id"], []) if o in cis]
        retired = is_retired(ci)

        if fam == "business_app" and not any(
                d == "child" and family_of(o["sys_class_name"]) == "app_service" and t == CONSUMES
                for d, o, t in links):
            findings.append(_finding("CSDM-001", ci, "No 'Consumes' link to an application service"))

        if fam == "app_service":
            if not any(d == "parent" and family_of(o["sys_class_name"]) == "business_app"
                       for d, o, _ in links):
                findings.append(_finding("CSDM-002", ci, "No parent business application"))
            if not any(d == "child" and family_of(o["sys_class_name"]) in INFRA_FAMILIES | {"network"}
                       for d, o, _ in links):
                findings.append(_finding("CSDM-003", ci, "No infrastructure CIs mapped"))

        if fam in INFRA_FAMILIES and not retired and not links:
            findings.append(_finding("COR-006", ci, "CI has no upstream or downstream relationships"))

        if fam in DISCOVERABLE_FAMILIES and not retired:
            last = ci.get("last_discovered", "")
            if not last:
                findings.append(_finding("COR-007", ci, "Never discovered (last_discovered empty)"))
            else:
                try:
                    seen = date.fromisoformat(last[:10])
                except ValueError:
                    findings.append(_finding("COR-007", ci, f"Unparseable last_discovered '{last}'"))
                else:
                    if seen < stale_cutoff:
                        age = (config.as_of - seen).days
                        findings.append(_finding("COR-007", ci, f"Last discovered {age} days ago"))

        if retired:
            active = [o["name"] for _, o, _ in links if not is_retired(o)]
            if active:
                findings.append(_finding(
                    "CSDM-006", ci, f"Retired but related to {len(active)} active CI(s): "
                    f"{', '.join(sorted(active)[:3])}"))
    return findings


def check_ownership(dataset: Dataset) -> list[Finding]:
    findings = []
    for ci in dataset.cis:
        if is_retired(ci):
            continue
        fam = family_of(ci["sys_class_name"])
        if fam in {"business_app", "app_service"} and not ci.get("owned_by"):
            findings.append(_finding("CSDM-004", ci, "owned_by is empty"))
        if not ci.get("support_group"):
            findings.append(_finding("CSDM-005", ci, "support_group is empty"))
    return findings


def run_all_checks(dataset: Dataset, groups: list[DuplicateGroup],
                   config: CheckConfig) -> list[Finding]:
    findings = (check_completeness(dataset) + check_duplicates(groups)
                + check_normalization(dataset) + check_relationships(dataset, config)
                + check_ownership(dataset))
    return sorted(findings, key=lambda f: (f.rule_id, f.name, f.sys_id))
