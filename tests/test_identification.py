from cmdb_dq.identification import find_duplicates
from cmdb_dq.synthetic import EXPECTED

from .conftest import make_ci


def test_serial_match_and_source_precedence():
    cis = [
        make_ci("1", "web-01-old", serial_number="ABC", discovery_source="SCCM"),
        make_ci("2", "web-01", serial_number="ABC", discovery_source="ServiceNow"),
    ]
    [group] = find_duplicates(cis)
    assert group.master["sys_id"] == "2"
    assert [d["sys_id"] for d in group.duplicates] == ["1"]
    assert group.matched_on == ["serial_number"]


def test_placeholder_serials_are_not_identifiers():
    cis = [make_ci(str(i), f"h{i}", serial_number="To be filled by O.E.M.") for i in range(3)]
    assert find_duplicates(cis) == []


def test_name_ip_is_case_insensitive_and_needs_both_values():
    cis = [
        make_ci("1", "APP-01", ip_address="10.1.1.1"),
        make_ci("2", "app-01", ip_address="10.1.1.1"),
        make_ci("3", "app-01", ip_address=""),
    ]
    [group] = find_duplicates(cis)
    assert {group.master["sys_id"], *(d["sys_id"] for d in group.duplicates)} == {"1", "2"}


def test_transitive_grouping_across_rules():
    cis = [
        make_ci("1", "a", serial_number="S1", fqdn="a.example"),
        make_ci("2", "b", serial_number="S1"),
        make_ci("3", "c", fqdn="a.example"),
    ]
    [group] = find_duplicates(cis)
    assert group.size == 3
    assert set(group.matched_on) == {"serial_number", "fqdn"}


def test_recency_breaks_source_tie():
    cis = [
        make_ci("1", "x", serial_number="S", last_discovered="2026-01-01"),
        make_ci("2", "x2", serial_number="S", last_discovered="2026-09-01"),
    ]
    assert find_duplicates(cis)[0].master["sys_id"] == "2"


def test_families_are_not_mixed():
    cis = [
        make_ci("1", "core", ip_address="10.0.0.1"),
        make_ci("2", "core", "cmdb_ci_ip_switch", ip_address="10.0.0.1"),
    ]
    assert find_duplicates(cis) == []


def test_synthetic_duplicates_found_and_masters_are_discovery(synthetic):
    groups = find_duplicates(synthetic.cis)
    expected = (EXPECTED["duplicates_serial"] + EXPECTED["duplicates_fqdn"]
                + EXPECTED["duplicates_name_ip"])
    assert len(groups) == expected
    assert all(g.master["discovery_source"] == "ServiceNow" for g in groups)
    assert all(d["discovery_source"] != "ServiceNow" for g in groups for d in g.duplicates)
