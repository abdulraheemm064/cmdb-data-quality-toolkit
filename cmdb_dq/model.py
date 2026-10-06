"""Shared data structures and CI class taxonomy."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

# Column order used for CSV import/export. Mirrors a typical cmdb_ci list export.
CI_FIELDS = [
    "sys_id",
    "name",
    "sys_class_name",
    "fqdn",
    "ip_address",
    "mac_address",
    "serial_number",
    "manufacturer",
    "os",
    "os_version",
    "environment",
    "install_status",
    "operational_status",
    "owned_by",
    "managed_by",
    "support_group",
    "business_criticality",
    "discovery_source",
    "last_discovered",
]

REL_FIELDS = ["parent", "child", "type"]

# Class -> family. Families drive identifier rules, required fields and CSDM checks.
CLASS_FAMILY = {
    "cmdb_ci_business_app": "business_app",
    "cmdb_ci_service_auto": "app_service",
    "cmdb_ci_service_discovered": "app_service",
    "cmdb_ci_service_calculated": "app_service",
    "cmdb_ci_server": "server",
    "cmdb_ci_linux_server": "server",
    "cmdb_ci_win_server": "server",
    "cmdb_ci_unix_server": "server",
    "cmdb_ci_db_instance": "database",
    "cmdb_ci_db_mssql_instance": "database",
    "cmdb_ci_db_ora_instance": "database",
    "cmdb_ci_netgear": "network",
    "cmdb_ci_ip_switch": "network",
    "cmdb_ci_ip_router": "network",
}

INFRA_FAMILIES = {"server", "database"}
DISCOVERABLE_FAMILIES = {"server", "database", "network"}
RETIRED_STATUSES = {"retired", "stolen", "disposed"}


def family_of(sys_class_name: str) -> str:
    return CLASS_FAMILY.get((sys_class_name or "").strip(), "other")


def is_retired(ci: dict) -> bool:
    return (ci.get("install_status") or "").strip().lower() in RETIRED_STATUSES


@dataclass
class Dataset:
    cis: list[dict] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)

    def by_id(self) -> dict[str, dict]:
        return {ci["sys_id"]: ci for ci in self.cis}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    kpi: str
    severity: str
    sys_id: str
    name: str
    sys_class_name: str
    message: str

    def to_dict(self) -> dict:
        return asdict(self)
