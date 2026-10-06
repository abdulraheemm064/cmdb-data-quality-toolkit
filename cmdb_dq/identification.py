"""Duplicate detection modelled on Identification and Reconciliation (IRE) concepts.

* Identifier rules are evaluated per class family in priority order.
* A rule only applies when every attribute it uses has a usable value
  (placeholder serial numbers such as "To be filled by O.E.M." are ignored).
* Records matched by any rule are grouped (transitively, via union-find).
* Reconciliation picks a master record per group using data-source precedence,
  then discovery recency, then attribute completeness.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from cmdb_dq.model import CI_FIELDS, family_of

log = logging.getLogger(__name__)

PLACEHOLDER_VALUES = {
    "", "n/a", "na", "none", "null", "0", "unknown", "not specified", "default string",
    "to be filled by o.e.m.", "system serial number", "123456789", "0.0.0.0",
}

# Lower number wins, like reconciliation data-source precedence.
SOURCE_PRECEDENCE = {"servicenow": 10, "sccm": 20, "importset": 30, "manual": 40}


@dataclass(frozen=True)
class IdentifierRule:
    name: str
    attributes: tuple[str, ...]


IDENTIFIER_RULES: dict[str, list[IdentifierRule]] = {
    "server": [
        IdentifierRule("serial_number", ("serial_number",)),
        IdentifierRule("fqdn", ("fqdn",)),
        IdentifierRule("name+ip_address", ("name", "ip_address")),
        IdentifierRule("mac_address", ("mac_address",)),
    ],
    "network": [
        IdentifierRule("serial_number", ("serial_number",)),
        IdentifierRule("name+ip_address", ("name", "ip_address")),
    ],
    "database": [IdentifierRule("name+ip_address", ("name", "ip_address"))],
    "business_app": [IdentifierRule("name", ("name",))],
    "app_service": [IdentifierRule("name", ("name",))],
}


def is_placeholder(value: str) -> bool:
    return (value or "").strip().lower() in PLACEHOLDER_VALUES


def _norm(attr: str, value: str) -> str | None:
    value = (value or "").strip().lower()
    if value in PLACEHOLDER_VALUES:
        return None
    if attr == "mac_address":
        value = value.replace("-", ":")
    return value


@dataclass
class DuplicateGroup:
    family: str
    master: dict
    duplicates: list[dict]
    matched_on: list[str] = field(default_factory=list)

    @property
    def size(self) -> int:
        return 1 + len(self.duplicates)

    def to_dict(self) -> dict:
        return {
            "family": self.family,
            "master": {"sys_id": self.master["sys_id"], "name": self.master["name"],
                       "discovery_source": self.master.get("discovery_source", "")},
            "duplicates": [{"sys_id": d["sys_id"], "name": d["name"],
                            "discovery_source": d.get("discovery_source", "")}
                           for d in self.duplicates],
            "matched_on": self.matched_on,
        }


class _UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def _master_sort_key(ci: dict) -> tuple:
    """Source precedence asc, then last_discovered desc, then completeness desc."""
    source = SOURCE_PRECEDENCE.get((ci.get("discovery_source") or "").strip().lower(), 99)
    populated = sum(1 for f in CI_FIELDS if ci.get(f))
    return (source, _desc(ci.get("last_discovered") or ""), -populated, ci["sys_id"])


def _desc(text: str) -> tuple[int, ...]:
    """Sort key that orders ISO date strings newest-first; empty values sort last."""
    return tuple(-ord(c) for c in text) + (0,)


def find_duplicates(cis: list[dict]) -> list[DuplicateGroup]:
    uf = _UnionFind()
    matched: dict[tuple[str, str], set[str]] = {}
    by_family: dict[str, list[dict]] = {}
    for ci in cis:
        by_family.setdefault(family_of(ci.get("sys_class_name", "")), []).append(ci)

    for family, members in by_family.items():
        for rule in IDENTIFIER_RULES.get(family, []):
            index: dict[tuple[str, ...], list[str]] = {}
            for ci in members:
                values = tuple(_norm(a, ci.get(a, "")) for a in rule.attributes)
                if any(v is None for v in values):
                    continue
                index.setdefault(values, []).append(ci["sys_id"])
            for ids in index.values():
                for other in ids[1:]:
                    uf.union(ids[0], other)
                    matched.setdefault((family, ids[0]), set()).add(rule.name)

    groups: dict[str, list[dict]] = {}
    lookup = {ci["sys_id"]: ci for ci in cis}
    for ci in cis:
        uf.find(ci["sys_id"])
    for sys_id in lookup:
        groups.setdefault(uf.find(sys_id), []).append(lookup[sys_id])

    result: list[DuplicateGroup] = []
    for members in groups.values():
        if len(members) < 2:
            continue
        family = family_of(members[0].get("sys_class_name", ""))
        ordered = sorted(members, key=_master_sort_key)
        rules: set[str] = set()
        for m in members:
            rules |= matched.get((family, m["sys_id"]), set())
        result.append(DuplicateGroup(family, ordered[0], ordered[1:], sorted(rules)))
    result.sort(key=lambda g: (g.family, g.master["name"]))
    log.info("Identified %d duplicate groups", len(result))
    return result
