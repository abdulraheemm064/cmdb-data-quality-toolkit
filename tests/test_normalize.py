import pytest

from cmdb_dq.normalize import (
    EMPTY,
    NORMALIZABLE,
    OK,
    UNMAPPED,
    apply_normalization,
    normalize_manufacturer,
    normalize_os,
)


@pytest.mark.parametrize("raw,expected,status", [
    ("Dell", "Dell", OK),
    ("Dell Inc.", "Dell", NORMALIZABLE),
    ("DELL", "Dell", NORMALIZABLE),
    ("Hewlett Packard Enterprise", "HPE", NORMALIZABLE),
    ("Cisco Systems, Inc.", "Cisco", NORMALIZABLE),
    ("  vmware ", "VMware", NORMALIZABLE),
    ("Generic OEM", None, UNMAPPED),
    ("", None, EMPTY),
])
def test_manufacturer(raw, expected, status):
    assert normalize_manufacturer(raw) == (expected, status)


@pytest.mark.parametrize("raw,expected,status", [
    ("Red Hat Enterprise Linux 8", "Red Hat Enterprise Linux 8", OK),
    ("RHEL 8", "Red Hat Enterprise Linux 8", NORMALIZABLE),
    ("rhel8", "Red Hat Enterprise Linux 8", NORMALIZABLE),
    ("Red Hat Enterprise Linux Server 9", "Red Hat Enterprise Linux 9", NORMALIZABLE),
    ("Microsoft Windows Server 2019 Standard", "Windows Server 2019", NORMALIZABLE),
    ("Win2019", "Windows Server 2019", NORMALIZABLE),
    ("Windows Server 2012 R2", "Windows Server 2012 R2", OK),
    ("ubuntu 22.04.3 LTS", "Ubuntu 22.04", NORMALIZABLE),
    ("SLES 15", "SUSE Linux Enterprise Server 15", NORMALIZABLE),
    ("AIX 7.2", None, UNMAPPED),
    ("", None, EMPTY),
])
def test_os(raw, expected, status):
    assert normalize_os(raw) == (expected, status)


def test_apply_normalization_does_not_mutate_input():
    cis = [{"manufacturer": "DELL", "os": "RHEL 9"}, {"manufacturer": "Dell", "os": ""}]
    out, changed = apply_normalization(cis)
    assert changed == 2
    assert out[0] == {"manufacturer": "Dell", "os": "Red Hat Enterprise Linux 9"}
    assert cis[0]["manufacturer"] == "DELL"
