# CMDB Data Quality Report

> Generated from synthetic data for a representative portfolio project. Not derived from any employer or client code or data.

- **Source:** `sample_cmdb_export.json`
- **As of:** 2026-09-30
- **CIs analysed:** 300
- **Overall health:** **83.2 / 100 (grade B)**

## Scorecard

| KPI | Score | CIs affected | Findings |
|---|---|---|---|
| Completeness | 96.0 | 12 | 12 |
| Correctness | 64.3 | 107 | 138 |
| Compliance | 89.3 | 32 | 32 |

Score = share of CIs with no finding for that KPI. Overall = weighted mean of the three KPIs (equal weights by default).

## Findings by rule

| Rule | KPI | Severity | Description | Count |
|---|---|---|---|---|
| COMP-001 | completeness | medium | Required attributes missing | 12 |
| COR-001 | correctness | high | Duplicate CI (not the reconciled master) | 20 |
| COR-002 | correctness | low | Manufacturer not normalized | 30 |
| COR-003 | correctness | medium | Manufacturer not in normalization table | 2 |
| COR-004 | correctness | low | OS name not normalized | 24 |
| COR-005 | correctness | medium | Placeholder serial number | 4 |
| COR-006 | correctness | medium | Orphan infrastructure CI (no relationships) | 32 |
| COR-007 | correctness | medium | Stale discovery date | 25 |
| COR-008 | correctness | high | Relationship references unknown CI | 1 |
| CSDM-001 | compliance | high | Business application has no application service | 1 |
| CSDM-002 | compliance | high | Application service not linked to a business application | 2 |
| CSDM-003 | compliance | high | Application service has no infrastructure dependency | 2 |
| CSDM-004 | compliance | medium | Missing owner (owned_by) | 7 |
| CSDM-005 | compliance | medium | Missing support group | 15 |
| CSDM-006 | compliance | medium | Retired CI still related to active CIs | 3 |
| CSDM-007 | compliance | low | Relationship type not allowed for class pair | 2 |

## Affected CIs by class

| Class | Total | Affected | % affected |
|---|---|---|---|
| cmdb_ci_business_app | 12 | 6 | 50% |
| cmdb_ci_db_mssql_instance | 22 | 4 | 18% |
| cmdb_ci_db_ora_instance | 22 | 5 | 23% |
| cmdb_ci_ip_switch | 28 | 11 | 39% |
| cmdb_ci_linux_server | 111 | 59 | 53% |
| cmdb_ci_service_auto | 24 | 9 | 38% |
| cmdb_ci_win_server | 81 | 44 | 54% |

## Duplicate groups (20)

| Master (kept) | Master source | Duplicates | Matched on |
|---|---|---|---|
| cbk-lnx-app-057 | ServiceNow | CBK-LNX-APP-057 (Manual) | fqdn |
| cbk-lnx-app-061 | ServiceNow | cbk-lnx-app-061-old (SCCM) | mac_address, serial_number |
| cbk-lnx-app-085 | ServiceNow | cbk-lnx-app-085-old (SCCM) | mac_address, serial_number |
| cbk-lnx-batch-012 | ServiceNow | cbk-lnx-batch-012 (ImportSet) | name+ip_address |
| cbk-lnx-batch-020 | ServiceNow | cbk-lnx-batch-020 (ImportSet) | name+ip_address |
| cbk-lnx-batch-048 | ServiceNow | CBK-LNX-BATCH-048 (Manual) | fqdn |
| cbk-lnx-mq-019 | ServiceNow | cbk-lnx-mq-019-old (SCCM) | mac_address, serial_number |
| cbk-lnx-mq-067 | ServiceNow | CBK-LNX-MQ-067 (Manual) | fqdn |
| cbk-lnx-mq-087 | ServiceNow | cbk-lnx-mq-087-old (SCCM) | mac_address, serial_number |
| cbk-lnx-web-030 | ServiceNow | cbk-lnx-web-030 (ImportSet) | name+ip_address |
| cbk-lnx-web-050 | ServiceNow | cbk-lnx-web-050-old (SCCM) | mac_address, serial_number |
| cbk-win-app-025 | ServiceNow | cbk-win-app-025 (ImportSet) | name+ip_address |
| cbk-win-app-053 | ServiceNow | cbk-win-app-053-old (SCCM) | mac_address, serial_number |
| cbk-win-app-069 | ServiceNow | cbk-win-app-069-old (SCCM) | mac_address, serial_number |
| cbk-win-mq-011 | ServiceNow | CBK-WIN-MQ-011 (Manual) | fqdn |

_...and 5 more (see JSON)._

## Normalization suggestions

| Field | Current value | Suggested | Records |
|---|---|---|---|
| manufacturer | HP Enterprise | HPE | 6 |
| manufacturer | VMware, Inc. | VMware | 6 |
| manufacturer | vmware | VMware | 6 |
| os | Windows 2022 Datacenter | Windows Server 2022 | 5 |
| os | RHEL 9 | Red Hat Enterprise Linux 9 | 4 |
| os | windows server 2022 | Windows Server 2022 | 4 |
| os | Red Hat 9 | Red Hat Enterprise Linux 9 | 3 |
| manufacturer | CISCO | Cisco | 2 |
| manufacturer | Dell Computer Corporation | Dell | 2 |
| manufacturer | Dell Inc. | Dell | 2 |
| manufacturer | Hewlett Packard Enterprise | HPE | 2 |
| os | Win2019 | Windows Server 2019 | 2 |
| os | ubuntu 22.04.3 LTS | Ubuntu 22.04 | 2 |
| manufacturer | Arista Networks | Arista | 1 |
| manufacturer | Cisco Systems, Inc. | Cisco | 1 |

## Sample findings (up to 3 per rule, highest severity first)

| Rule | Severity | CI | Class | Detail |
|---|---|---|---|---|
| COR-001 | high | CBK-LNX-APP-057 | cmdb_ci_linux_server | Duplicate of cbk-lnx-app-057 (0a3450fc9918ee461497d6587010f719) matched on fqdn |
| COR-001 | high | CBK-LNX-BATCH-048 | cmdb_ci_linux_server | Duplicate of cbk-lnx-batch-048 (892e6161be2d740a1e9b23bc50c7c006) matched on fqdn |
| COR-001 | high | CBK-LNX-MQ-067 | cmdb_ci_linux_server | Duplicate of cbk-lnx-mq-067 (d85480f0dfcaf0b719b17e80dea4ae17) matched on fqdn |
| COR-008 | high | Retail Payments Hub - PROD | cmdb_ci_service_auto | Relationship 'Depends on::Used by' points to missing CI ffffffffffffffffffffffffffffffff |
| CSDM-001 | high | Statement Archive | cmdb_ci_business_app | No 'Consumes' link to an application service |
| CSDM-002 | high | Batch Scheduler - PROD | cmdb_ci_service_auto | No parent business application |
| CSDM-002 | high | Shared File Transfer - PROD | cmdb_ci_service_auto | No parent business application |
| CSDM-003 | high | General Ledger - PROD | cmdb_ci_service_auto | No infrastructure CIs mapped |
| CSDM-003 | high | General Ledger - UAT | cmdb_ci_service_auto | No infrastructure CIs mapped |
| COMP-001 | medium | CBK-LNX-APP-057 | cmdb_ci_linux_server | Missing: serial_number, ip_address |
| COMP-001 | medium | CBK-LNX-BATCH-048 | cmdb_ci_linux_server | Missing: serial_number, ip_address |
| COMP-001 | medium | CBK-LNX-MQ-067 | cmdb_ci_linux_server | Missing: serial_number, ip_address |
| COR-003 | medium | cbk-lnx-app-049 | cmdb_ci_linux_server | 'Generic OEM' has no normalization entry |
| COR-003 | medium | cbk-win-web-066 | cmdb_ci_win_server | 'Generic OEM' has no normalization entry |
| COR-005 | medium | cbk-lnx-app-077 | cmdb_ci_linux_server | Serial number 'To be filled by O.E.M.' is a placeholder |
| COR-005 | medium | cbk-lnx-batch-060 | cmdb_ci_linux_server | Serial number 'To be filled by O.E.M.' is a placeholder |
| COR-005 | medium | cbk-lnx-batch-068 | cmdb_ci_linux_server | Serial number 'To be filled by O.E.M.' is a placeholder |
| COR-006 | medium | CBK-LNX-APP-057 | cmdb_ci_linux_server | CI has no upstream or downstream relationships |
| COR-006 | medium | CBK-LNX-BATCH-048 | cmdb_ci_linux_server | CI has no upstream or downstream relationships |
| COR-006 | medium | CBK-LNX-MQ-067 | cmdb_ci_linux_server | CI has no upstream or downstream relationships |
| COR-007 | medium | cbk-lnx-app-081 | cmdb_ci_linux_server | Last discovered 207 days ago |
| COR-007 | medium | cbk-lnx-app-089 | cmdb_ci_linux_server | Last discovered 148 days ago |
| COR-007 | medium | cbk-lnx-app-097 | cmdb_ci_linux_server | Last discovered 276 days ago |
| CSDM-004 | medium | Card Disputes - UAT | cmdb_ci_service_auto | owned_by is empty |
| CSDM-004 | medium | Claims Intake - UAT | cmdb_ci_service_auto | owned_by is empty |
| CSDM-004 | medium | Fraud Analytics - UAT | cmdb_ci_service_auto | owned_by is empty |
| CSDM-005 | medium | CBKORA03 | cmdb_ci_db_ora_instance | support_group is empty |
| CSDM-005 | medium | CBKORA21 | cmdb_ci_db_ora_instance | support_group is empty |
| CSDM-005 | medium | CBKORA25 | cmdb_ci_db_ora_instance | support_group is empty |
| CSDM-006 | medium | cbk-win-app-049 | cmdb_ci_win_server | Retired but related to 1 active CI(s): Fraud Analytics - PROD |
| CSDM-006 | medium | cbk-win-app-057 | cmdb_ci_win_server | Retired but related to 1 active CI(s): Retail Payments Hub - PROD |
| CSDM-006 | medium | cbk-win-web-058 | cmdb_ci_win_server | Retired but related to 1 active CI(s): Treasury Liquidity - PROD |
| COR-002 | low | cbk-lnx-app-017 | cmdb_ci_linux_server | 'vmware' should be 'VMware' |
| COR-002 | low | cbk-lnx-app-025 | cmdb_ci_linux_server | 'VMware, Inc.' should be 'VMware' |
| COR-002 | low | cbk-lnx-app-037 | cmdb_ci_linux_server | 'Hewlett Packard Enterprise' should be 'HPE' |
| COR-004 | low | cbk-lnx-app-013 | cmdb_ci_linux_server | OS 'RHEL 8' should be 'Red Hat Enterprise Linux 8' |
| COR-004 | low | cbk-lnx-app-025 | cmdb_ci_linux_server | OS 'RHEL 9' should be 'Red Hat Enterprise Linux 9' |
| COR-004 | low | cbk-lnx-app-041 | cmdb_ci_linux_server | OS 'RHEL 9' should be 'Red Hat Enterprise Linux 9' |
| CSDM-007 | low | Mortgage Origination | cmdb_ci_business_app | 'Depends on::Used by' from business_app to server (cbk-lnx-batch-032) is not an allowed CSDM pattern |
| CSDM-007 | low | Retail Payments Hub | cmdb_ci_business_app | 'Depends on::Used by' from business_app to server (cbk-win-web-026) is not an allowed CSDM pattern |

_Full finding list is in the JSON report._

## Recommended remediation

- **COMP-001** - Make the attributes mandatory on the ingest path (Import Set transform or discovery pattern) rather than on the form only.
- **COR-001** - Review identifier rules and data-source precedence; merge or retire the non-master records and fix the source that created them.
- **COR-002** - Load the variants into the normalization lookup so new records are corrected on insert.
- **COR-003** - Add the vendor to the manufacturer normalization table (or the company table).
- **COR-004** - Add OS normalization rules so reporting and lifecycle data line up.
- **COR-005** - Exclude placeholder serials from identification; fix the BIOS/OEM data at source.
- **COR-006** - Map the CI to an application service or confirm it should be retired.
- **COR-007** - Check MID Server reachability/credentials for the subnet, or retire the CI.
- **COR-008** - Delete or repair relationships that reference CIs which no longer exist.
- **CSDM-001** - Create the application service(s) for each environment and link them.
- **CSDM-002** - Link the service to its business application via 'Consumes::Consumed by'.
- **CSDM-003** - Run Service Mapping or tag-based mapping to populate the service.
- **CSDM-004** - Assign an accountable owner; route through the data certification process.
- **CSDM-005** - Assign a support group so incidents and changes route correctly.
- **CSDM-006** - Remove relationships from retired CIs as part of the retirement workflow.
- **CSDM-007** - Replace the direct relationship with the correct CSDM layer (business app -> application service -> infrastructure).
