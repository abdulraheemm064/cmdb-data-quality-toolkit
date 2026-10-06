"""Deterministic generator for a synthetic CMDB export ("Contoso Bank").

Every name, address, serial number and user id is invented. Data quality issues
are injected in known quantities (see EXPECTED) so tests can assert exact results.
"""

from __future__ import annotations

import random
from datetime import date, timedelta

from cmdb_dq.model import Dataset

DOMAIN = "corp.contoso-bank.example"

BUSINESS_APPS = [
    "Retail Payments Hub", "Mortgage Origination", "Card Disputes", "Treasury Liquidity",
    "Claims Intake", "Policy Administration", "KYC Screening", "Wire Transfer Gateway",
    "Customer Self-Service Portal", "Fraud Analytics", "General Ledger", "Statement Archive",
]
UNLINKED_SERVICES = ["Shared File Transfer - PROD", "Batch Scheduler - PROD"]

COUNTS = {"linux": 100, "windows": 72, "database": 44, "network": 28}

MANUFACTURER_VARIANTS = {
    "Dell": ["Dell Inc.", "DELL", "Dell Computer Corporation"],
    "HPE": ["Hewlett Packard Enterprise", "HP Enterprise"],
    "VMware": ["VMware, Inc.", "vmware"],
    "Cisco": ["Cisco Systems, Inc.", "CISCO"],
    "Juniper": ["Juniper Networks"],
    "Arista": ["Arista Networks"],
    "Microsoft": ["Microsoft Corporation"],
}
OS_VARIANTS = {
    "Red Hat Enterprise Linux 8": ["RHEL 8", "Red Hat Enterprise Linux Server 8", "rhel8"],
    "Red Hat Enterprise Linux 9": ["RHEL 9", "Red Hat 9"],
    "Ubuntu 22.04": ["Ubuntu Linux 22.04", "ubuntu 22.04.3 LTS"],
    "Windows Server 2019": ["Microsoft Windows Server 2019 Standard", "Win2019"],
    "Windows Server 2022": ["Windows 2022 Datacenter", "windows server 2022"],
}

# Exact counts of injected issues. Tests assert the analyser finds these.
EXPECTED = {
    "total_cis": 300,
    "duplicates_serial": 8,
    "duplicates_fqdn": 6,
    "duplicates_name_ip": 6,
    "orphan_infra": 12,
    "stale": 25,
    "stale_never_discovered": 3,
    "placeholder_serial": 4,
    "retired_linked": 3,
    "os_variants": 24,
    "manufacturer_variants": 30,
    "manufacturer_unmapped": 2,
    "missing_support_group": 15,
    "business_app_missing_owner": 3,
    "app_service_missing_owner": 4,
    "business_app_without_service": 1,
    "service_without_business_app": 2,
    "service_without_infra": 2,
    "bad_relationship_type": 2,
    "dangling_relationship": 1,
}


def generate(seed: int = 42, as_of: date = date(2026, 9, 30)) -> Dataset:
    rng = random.Random(seed)
    used_serials: set[str] = set()

    def sys_id() -> str:
        return f"{rng.getrandbits(128):032x}"

    def serial(prefix: str) -> str:
        while True:
            value = f"{prefix}{rng.randint(10**7, 10**8 - 1)}"
            if value not in used_serials:
                used_serials.add(value)
                return value

    def mac() -> str:
        return ":".join(f"{rng.randint(0, 255):02x}" for _ in range(6))

    def seen(lo: int = 0, hi: int = 6) -> str:
        return (as_of - timedelta(days=rng.randint(lo, hi))).isoformat()

    def base(name: str, cls: str, **extra) -> dict:
        ci = {
            "sys_id": sys_id(), "name": name, "sys_class_name": cls, "fqdn": "",
            "ip_address": "", "mac_address": "", "serial_number": "", "manufacturer": "",
            "os": "", "os_version": "", "environment": "", "install_status": "Installed",
            "operational_status": "Operational", "owned_by": "", "managed_by": "",
            "support_group": "", "business_criticality": "", "discovery_source": "ServiceNow",
            "last_discovered": "",
        }
        ci.update(extra)
        return ci

    cis: list[dict] = []
    rels: list[dict] = []

    # --- Business applications and application services (CSDM "design" layer) ---
    apps = []
    for i, name in enumerate(BUSINESS_APPS):
        apps.append(base(
            name, "cmdb_ci_business_app",
            owned_by="" if i in (3, 7, 10) else f"usr.cb.appowner{i + 1:02d}",
            managed_by=f"usr.cb.itmanager{i % 4 + 1:02d}", support_group="CB-App-Support",
            business_criticality=rng.choice(["1 - most critical", "2 - somewhat critical"]),
            discovery_source="Manual"))
    services = []
    for app in apps[:11]:
        for env in ("PROD", "UAT"):
            services.append(base(
                f"{app['name']} - {env}", "cmdb_ci_service_auto",
                environment="Production" if env == "PROD" else "UAT",
                owned_by=app["owned_by"] or "usr.cb.svcowner00", support_group="CB-App-Support",
                discovery_source="Manual"))
    for name in UNLINKED_SERVICES:
        services.append(base(name, "cmdb_ci_service_auto", environment="Production",
                             owned_by="usr.cb.svcowner99", support_group="CB-App-Support",
                             discovery_source="Manual"))
    for idx in (5, 9, 14, 19):
        services[idx]["owned_by"] = ""
    cis += apps + services

    for app_idx, app in enumerate(apps[:11]):
        for svc in services[app_idx * 2: app_idx * 2 + 2]:
            rels.append({"parent": app["sys_id"], "child": svc["sys_id"],
                         "type": "Consumes::Consumed by"})

    # --- Infrastructure ---
    servers, databases, network = [], [], []
    roles = ["app", "web", "mq", "batch"]
    for n in range(COUNTS["linux"]):
        name = f"cbk-lnx-{roles[n % 4]}-{n + 1:03d}"
        os_name = rng.choice(["Red Hat Enterprise Linux 8", "Red Hat Enterprise Linux 9",
                              "Ubuntu 22.04"])
        servers.append(base(
            name, "cmdb_ci_linux_server", fqdn=f"{name}.{DOMAIN}",
            ip_address=f"10.20.{n // 200}.{n % 200 + 10}", mac_address=mac(),
            serial_number=serial("CZ"), manufacturer=rng.choice(["Dell", "HPE", "VMware"]),
            os=os_name, environment=rng.choice(["Production", "UAT", "Development"]),
            managed_by="usr.cb.linuxlead", support_group="CB-Linux-Platform",
            last_discovered=seen()))
    for n in range(COUNTS["windows"]):
        name = f"cbk-win-{roles[n % 4]}-{n + 1:03d}"
        servers.append(base(
            name, "cmdb_ci_win_server", fqdn=f"{name}.{DOMAIN}",
            ip_address=f"10.30.{n // 200}.{n % 200 + 10}", mac_address=mac(),
            serial_number=serial("WX"), manufacturer=rng.choice(["Dell", "HPE", "VMware"]),
            os=rng.choice(["Windows Server 2019", "Windows Server 2022"]),
            environment=rng.choice(["Production", "UAT", "Development"]),
            managed_by="usr.cb.windowslead", support_group="CB-Windows-Platform",
            last_discovered=seen()))
    for n in range(COUNTS["database"]):
        oracle = n % 2 == 0
        databases.append(base(
            f"CBK{'ORA' if oracle else 'SQL'}{n + 1:02d}",
            "cmdb_ci_db_ora_instance" if oracle else "cmdb_ci_db_mssql_instance",
            ip_address=f"10.40.0.{n + 10}", manufacturer="Oracle" if oracle else "Microsoft",
            environment=rng.choice(["Production", "UAT"]), managed_by="usr.cb.dbalead",
            support_group="CB-Database-Ops", last_discovered=seen()))
    for n in range(COUNTS["network"]):
        name = f"cbk-net-sw-{n + 1:03d}"
        network.append(base(
            name, "cmdb_ci_ip_switch", fqdn=f"{name}.{DOMAIN}", ip_address=f"10.99.0.{n + 10}",
            mac_address=mac(), serial_number=serial("FX"),
            manufacturer=rng.choice(["Cisco", "Juniper", "Arista"]),
            managed_by="usr.cb.netlead", support_group="CB-Network-Ops", last_discovered=seen()))

    infra = servers + databases
    pool = infra[:]
    rng.shuffle(pool)
    orphans = pool[:EXPECTED["orphan_infra"]]
    attached = pool[EXPECTED["orphan_infra"]:]

    # Map attached infra round-robin to services, skipping services 20 and 21 (left empty).
    targets = [s for i, s in enumerate(services) if i not in (20, 21)]
    for i, ci in enumerate(attached):
        svc = targets[i % len(targets)]
        rels.append({"parent": svc["sys_id"], "child": ci["sys_id"], "type": "Depends on::Used by"})
    for i, ci in enumerate(network[:12]):
        rels.append({"parent": targets[i]["sys_id"], "child": ci["sys_id"],
                     "type": "Depends on::Used by"})

    # Disjoint slices of attached servers for each injected issue.
    orphan_ids = {c["sys_id"] for c in orphans}
    attached_servers = [s for s in servers if s["sys_id"] not in orphan_ids]
    rng.shuffle(attached_servers)
    cursor = 0

    def take(n: int) -> list[dict]:
        nonlocal cursor
        chunk = attached_servers[cursor:cursor + n]
        cursor += n
        return chunk

    dup_serial_src = take(EXPECTED["duplicates_serial"])
    dup_fqdn_src = take(EXPECTED["duplicates_fqdn"])
    dup_name_ip_src = take(EXPECTED["duplicates_name_ip"])
    placeholder = take(EXPECTED["placeholder_serial"])
    retired = take(EXPECTED["retired_linked"])
    stale = take(EXPECTED["stale"])
    os_variant = take(EXPECTED["os_variants"])

    for ci in placeholder:
        ci["serial_number"] = "To be filled by O.E.M."
    for ci in retired:
        ci.update(install_status="Retired", operational_status="Non-Operational")
    for i, ci in enumerate(stale):
        never = i < EXPECTED["stale_never_discovered"]
        ci["last_discovered"] = "" if never else seen(45, 400)
    for ci in os_variant:
        ci["os"] = rng.choice(OS_VARIANTS[ci["os"]])

    dup_src_ids = {c["sys_id"] for c in dup_serial_src + dup_fqdn_src + dup_name_ip_src}
    hardware = [c for c in servers + network if c["sys_id"] not in dup_src_ids]
    picks = rng.sample(hardware, EXPECTED["manufacturer_variants"]
                       + EXPECTED["manufacturer_unmapped"])
    for ci in picks[:EXPECTED["manufacturer_variants"]]:
        ci["manufacturer"] = rng.choice(MANUFACTURER_VARIANTS[ci["manufacturer"]])
    for ci in picks[EXPECTED["manufacturer_variants"]:]:
        ci["manufacturer"] = "Generic OEM"

    for ci in rng.sample(databases + network, EXPECTED["missing_support_group"]):
        ci["support_group"] = ""

    # Duplicate records created by lower-precedence sources.
    duplicates = []
    for ci in dup_serial_src:
        duplicates.append({**ci, "sys_id": sys_id(), "name": f"{ci['name']}-old", "fqdn": "",
                           "ip_address": f"10.250.0.{len(duplicates) + 10}",
                           "discovery_source": "SCCM", "last_discovered": seen(10, 20)})
    for ci in dup_fqdn_src:
        duplicates.append({**ci, "sys_id": sys_id(), "name": ci["name"].upper(),
                           "serial_number": "", "ip_address": "", "mac_address": "",
                           "discovery_source": "Manual", "last_discovered": seen(10, 20)})
    for ci in dup_name_ip_src:
        duplicates.append({**ci, "sys_id": sys_id(), "serial_number": "", "fqdn": "",
                           "mac_address": "", "discovery_source": "ImportSet",
                           "last_discovered": seen(10, 20)})

    # CSDM layering violations and a dangling relationship.
    for app, server in zip(apps[:EXPECTED["bad_relationship_type"]], attached_servers[-2:], strict=True):
        rels.append({"parent": app["sys_id"], "child": server["sys_id"],
                     "type": "Depends on::Used by"})
    rels.append({"parent": services[0]["sys_id"], "child": "f" * 32,
                 "type": "Depends on::Used by"})

    cis += servers + databases + network + duplicates
    return Dataset(cis, rels)
