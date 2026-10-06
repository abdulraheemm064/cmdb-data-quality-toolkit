import json

import pytest

from cmdb_dq.cli import EXIT_BELOW_THRESHOLD, EXIT_INPUT_ERROR, EXIT_OK, main
from cmdb_dq.loader import LoaderError, load_dataset, save_csv, save_json


def test_json_and_csv_round_trip(tmp_path, synthetic):
    save_json(synthetic, tmp_path / "x.json")
    from_json = load_dataset(tmp_path / "x.json")
    save_csv(synthetic, tmp_path / "ci.csv", tmp_path / "rel.csv")
    from_csv = load_dataset(tmp_path / "ci.csv", tmp_path / "rel.csv")
    assert len(from_json.cis) == len(from_csv.cis) == 300
    assert from_json.cis[0] == from_csv.cis[0]
    assert from_json.relationships == from_csv.relationships


def test_accepts_records_key(tmp_path):
    path = tmp_path / "export.json"
    path.write_text(json.dumps({"records": [{"sys_id": "1", "name": "a"}]}))
    ds = load_dataset(path)
    assert ds.cis[0]["serial_number"] == ""


@pytest.mark.parametrize("payload,match", [
    ([{"name": "no id"}], "no sys_id"),
    ([{"sys_id": "1"}, {"sys_id": "1"}], "more than once"),
    ({"cis": [], "relationships": [{"parent": "a"}]}, "missing"),
])
def test_validation_errors(tmp_path, payload, match):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(LoaderError, match=match):
        load_dataset(path)


def test_unsupported_extension(tmp_path):
    path = tmp_path / "x.xml"
    path.write_text("<x/>")
    with pytest.raises(LoaderError):
        load_dataset(path)


def test_cli_end_to_end(tmp_path, capsys):
    export = tmp_path / "export.json"
    assert main(["generate", "--out", str(export)]) == EXIT_OK
    out_dir = tmp_path / "reports"
    normalized = tmp_path / "normalized.json"
    code = main(["analyze", "--input", str(export), "--as-of", "2026-09-30",
                 "--out-dir", str(out_dir), "--export-normalized", str(normalized)])
    assert code == EXIT_OK
    assert "Overall health" in capsys.readouterr().out
    assert (out_dir / "cmdb-health-report.md").exists()
    data = json.loads(normalized.read_text())
    assert "Dell Inc." not in {ci["manufacturer"] for ci in data["cis"]}


def test_cli_fail_under_gate(tmp_path):
    export = tmp_path / "export.json"
    main(["generate", "--out", str(export)])
    code = main(["analyze", "--input", str(export), "--as-of", "2026-09-30",
                 "--out-dir", str(tmp_path), "--fail-under", "99"])
    assert code == EXIT_BELOW_THRESHOLD


def test_cli_csv_generation_and_missing_input(tmp_path):
    assert main(["generate", "--format", "csv", "--out", str(tmp_path / "csv")]) == EXIT_OK
    assert (tmp_path / "csv" / "cmdb_ci.csv").exists()
    assert main(["analyze", "--input", str(tmp_path / "nope.json")]) == EXIT_INPUT_ERROR


def test_cli_rejects_bad_date():
    with pytest.raises(SystemExit):
        main(["analyze", "--input", "x.json", "--as-of", "30/09/2026"])
