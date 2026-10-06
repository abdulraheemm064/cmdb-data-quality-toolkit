from collections import Counter

from cmdb_dq.checks import CheckConfig, check_relationships, run_all_checks
from cmdb_dq.identification import find_duplicates
from cmdb_dq.model import Dataset
from cmdb_dq.synthetic import EXPECTED

from .conftest import AS_OF, make_ci


def _rules(dataset: Dataset, stale_days: int = 30) -> Counter:
    findings = run_all_checks(dataset, find_duplicates(dataset.cis),
                              CheckConfig(as_of=AS_OF, stale_days=stale_days))
    return Counter(f.rule_id for f in findings)


def test_compliant_model_has_no_findings(small_model):
    assert _rules(small_model) == Counter()


def test_business_app_without_service(small_model):
    small_model.relationships = [r for r in small_model.relationships if r["parent"] != "a1"]
    rules = _rules(small_model)
    assert rules["CSDM-001"] == 1 and rules["CSDM-002"] == 1


def test_service_without_infra_and_orphans(small_model):
    small_model.relationships = small_model.relationships[:1]
    rules = _rules(small_model)
    assert rules["CSDM-003"] == 1
    assert rules["COR-006"] == 2  # host and db now orphaned


def test_stale_and_never_discovered(small_model):
    small_model.cis[2]["last_discovered"] = "2026-05-01"
    small_model.cis[3]["last_discovered"] = ""
    assert _rules(small_model)["COR-007"] == 2
    assert _rules(small_model, stale_days=365)["COR-007"] == 1


def test_retired_ci_still_related(small_model):
    small_model.cis[2]["install_status"] = "Retired"
    rules = _rules(small_model)
    assert rules["CSDM-006"] == 1
    assert rules["COR-007"] == 0  # retired CIs are not expected to be discovered


def test_wrong_relationship_type_and_dangling():
    cis = [make_ci("a", "App", "cmdb_ci_business_app", owned_by="o", business_criticality="1"),
           make_ci("h", "host", serial_number="S", ip_address="1.1.1.1", os="Ubuntu 22.04",
                   manufacturer="Dell")]
    rels = [{"parent": "a", "child": "h", "type": "Depends on::Used by"},
            {"parent": "a", "child": "missing", "type": "Consumes::Consumed by"}]
    findings = check_relationships(Dataset(cis, rels), CheckConfig(as_of=AS_OF))
    ids = Counter(f.rule_id for f in findings)
    assert ids["CSDM-007"] == 1
    assert ids["COR-008"] == 1


def test_missing_owner_and_support_group(small_model):
    small_model.cis[0]["owned_by"] = ""
    small_model.cis[2]["support_group"] = ""
    rules = _rules(small_model)
    assert rules["CSDM-004"] == 1 and rules["CSDM-005"] == 1


def test_completeness_lists_missing_fields(small_model):
    small_model.cis[2]["serial_number"] = ""
    small_model.cis[2]["os"] = ""
    findings = run_all_checks(small_model, [], CheckConfig(as_of=AS_OF))
    [f] = [f for f in findings if f.rule_id == "COMP-001"]
    assert f.message == "Missing: serial_number, os"


def test_synthetic_dataset_injected_issue_counts(synthetic):
    rules = _rules(synthetic)
    dup_total = (EXPECTED["duplicates_serial"] + EXPECTED["duplicates_fqdn"]
                 + EXPECTED["duplicates_name_ip"])
    assert rules["COR-001"] == dup_total
    assert rules["COR-002"] == EXPECTED["manufacturer_variants"]
    assert rules["COR-003"] == EXPECTED["manufacturer_unmapped"]
    assert rules["COR-004"] == EXPECTED["os_variants"]
    assert rules["COR-005"] == EXPECTED["placeholder_serial"]
    # duplicate records are never related to anything, so they are orphans as well
    assert rules["COR-006"] == EXPECTED["orphan_infra"] + dup_total
    assert rules["COR-007"] == EXPECTED["stale"]
    assert rules["COR-008"] == EXPECTED["dangling_relationship"]
    assert rules["CSDM-001"] == EXPECTED["business_app_without_service"]
    assert rules["CSDM-002"] == EXPECTED["service_without_business_app"]
    assert rules["CSDM-003"] == EXPECTED["service_without_infra"]
    assert rules["CSDM-004"] == (EXPECTED["business_app_missing_owner"]
                                 + EXPECTED["app_service_missing_owner"])
    assert rules["CSDM-005"] == EXPECTED["missing_support_group"]
    assert rules["CSDM-006"] == EXPECTED["retired_linked"]
    assert rules["CSDM-007"] == EXPECTED["bad_relationship_type"]
    # fqdn and name+ip duplicates were created without serial numbers (and some without IPs)
    assert rules["COMP-001"] == EXPECTED["duplicates_fqdn"] + EXPECTED["duplicates_name_ip"]
