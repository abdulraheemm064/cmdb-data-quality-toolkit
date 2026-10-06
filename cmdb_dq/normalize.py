"""Manufacturer and OS name normalization.

Plays the same role as normalization/lookup tables used before data lands in the
CMDB: many discovery sources report the same vendor or OS with different
spellings, which breaks reporting and software/hardware model matching.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Callable

OK, NORMALIZABLE, UNMAPPED, EMPTY = "ok", "normalizable", "unmapped", "empty"

# canonical -> known variants. Keys are matched after _key() folding.
MANUFACTURER_VARIANTS: dict[str, list[str]] = {
    "Dell": ["Dell Inc.", "DELL", "Dell Computer Corporation", "dell inc"],
    "HPE": ["Hewlett Packard Enterprise", "HP Enterprise", "hpe"],
    "HP": ["Hewlett-Packard", "Hewlett Packard", "HP Inc."],
    "VMware": ["VMware, Inc.", "vmware"],
    "Cisco": ["Cisco Systems, Inc.", "cisco systems", "CISCO"],
    "Juniper": ["Juniper Networks", "juniper networks inc"],
    "Arista": ["Arista Networks", "arista networks inc"],
    "Microsoft": ["Microsoft Corporation", "microsoft corp"],
    "Oracle": ["Oracle Corporation", "oracle corp"],
    "IBM": ["International Business Machines", "IBM Corp"],
}


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


_MANUFACTURER_LOOKUP: dict[str, str] = {}
for _canonical, _variants in MANUFACTURER_VARIANTS.items():
    _MANUFACTURER_LOOKUP[_key(_canonical)] = _canonical
    for _variant in _variants:
        _MANUFACTURER_LOOKUP[_key(_variant)] = _canonical


def _windows(match: re.Match) -> str:
    r2 = " R2" if match.group(2) else ""
    return f"Windows Server {match.group(1)}{r2}"


OS_RULES: list[tuple[re.Pattern, Callable[[re.Match], str]]] = [
    (re.compile(r"^(?:rhel|red\s*hat(?:\s+enterprise\s+linux)?)(?:\s+server)?\s*(\d+)", re.I),
     lambda m: f"Red Hat Enterprise Linux {m.group(1)}"),
    (re.compile(r"^(?:microsoft\s+)?win(?:dows)?\s*(?:server\s*)?(20\d\d)(\s*r2)?", re.I),
     _windows),
    (re.compile(r"^ubuntu(?:\s+linux)?\s*(\d{2}\.\d{2})", re.I),
     lambda m: f"Ubuntu {m.group(1)}"),
    (re.compile(r"^(?:suse|sles)(?:\s+linux\s+enterprise\s+server)?\s*(\d+)", re.I),
     lambda m: f"SUSE Linux Enterprise Server {m.group(1)}"),
]


def normalize_manufacturer(value: str) -> tuple[str | None, str]:
    """Return (canonical_value, status)."""
    value = (value or "").strip()
    if not value:
        return None, EMPTY
    canonical = _MANUFACTURER_LOOKUP.get(_key(value))
    if canonical is None:
        return None, UNMAPPED
    return canonical, OK if canonical == value else NORMALIZABLE


def normalize_os(value: str) -> tuple[str | None, str]:
    """Return (canonical_value, status)."""
    value = (value or "").strip()
    if not value:
        return None, EMPTY
    for pattern, render in OS_RULES:
        match = pattern.match(value)
        if match:
            canonical = render(match)
            return canonical, OK if canonical == value else NORMALIZABLE
    return None, UNMAPPED


def apply_normalization(cis: list[dict]) -> tuple[list[dict], int]:
    """Return a normalized deep copy of the CIs and the number of values changed."""
    out = copy.deepcopy(cis)
    changed = 0
    for ci in out:
        for field_name, fn in (("manufacturer", normalize_manufacturer), ("os", normalize_os)):
            canonical, status = fn(ci.get(field_name, ""))
            if status == NORMALIZABLE:
                ci[field_name] = canonical
                changed += 1
    return out, changed
