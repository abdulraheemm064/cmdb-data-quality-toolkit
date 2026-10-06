from datetime import date

import pytest

from cmdb_dq.model import CI_FIELDS, Dataset
from cmdb_dq.synthetic import generate

AS_OF = date(2026, 9, 30)


def make_ci(sys_id: str, name: str, cls: str = "cmdb_ci_linux_server", **extra) -> dict:
    ci = {f: "" for f in CI_FIELDS}
    ci.update(sys_id=sys_id, name=name, sys_class_name=cls, install_status="Installed",
              support_group="CB-Test", last_discovered="2026-09-29")
    ci.update(extra)
    return ci


@pytest.fixture(scope="session")
def synthetic() -> Dataset:
    return generate(seed=42, as_of=AS_OF)


@pytest.fixture
def small_model() -> Dataset:
    """A minimal, fully compliant CSDM chain: app -> service -> server, db."""
    cis = [
        make_ci("a1", "Payments", "cmdb_ci_business_app", owned_by="usr.x",
                business_criticality="1 - most critical", last_discovered=""),
        make_ci("s1", "Payments - PROD", "cmdb_ci_service_auto", owned_by="usr.x",
                environment="Production", last_discovered=""),
        make_ci("h1", "host-1", serial_number="SN1", ip_address="10.0.0.1",
                os="Red Hat Enterprise Linux 9", manufacturer="Dell"),
        make_ci("d1", "DB1", "cmdb_ci_db_ora_instance", ip_address="10.0.0.1",
                manufacturer="Oracle"),
    ]
    rels = [
        {"parent": "a1", "child": "s1", "type": "Consumes::Consumed by"},
        {"parent": "s1", "child": "h1", "type": "Depends on::Used by"},
        {"parent": "s1", "child": "d1", "type": "Depends on::Used by"},
        {"parent": "d1", "child": "h1", "type": "Runs on::Runs"},
    ]
    return Dataset(cis, rels)
