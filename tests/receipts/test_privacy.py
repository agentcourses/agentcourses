"""Only synthetic sentinels enter temporary inputs; no host history is read."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "experiments/call-receipts/probe.py"
SENTINEL = "synthetic-private-answer-keep-ephemeral"
OUTPUT_FIELDS = {"case", "host", "outcome", "binding_failures", "evidence_class", "candidate_eligible"}


def probe_module():
    spec = importlib.util.spec_from_file_location("privacy_probe", PROBE)
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    return probe


def test_no_private_payload(tmp_path):
    probe = probe_module()
    case = probe.load_cases(ROOT / "experiments/call-receipts/cases")[0]
    case = {**case, "answer": SENTINEL}
    result = probe.evaluate_case(case)
    encoded = probe.encode_results([{**result, "answer": SENTINEL, "conversation": SENTINEL, "answer_hash": SENTINEL}])
    assert SENTINEL not in encoded
    assert set(json.loads(encoded)[0]) == OUTPUT_FIELDS
    source = tmp_path / "ephemeral-input.json"
    source.write_text(json.dumps([case]))
    completed = subprocess.run([sys.executable, str(PROBE), "--cases", str(source)], capture_output=True, text=True)
    assert completed.returncode == 0
    output = tmp_path / "minimised-output.json"
    output.write_text(completed.stdout)
    assert SENTINEL not in output.read_text() + completed.stderr
    assert set(json.loads(output.read_text())[0]) == OUTPUT_FIELDS


@pytest.mark.parametrize("field", ["conversation", "transcript", "answer_hash", "transcript_path"])
def test_unknown_private_fields_fail_without_echo(tmp_path, field):
    probe = probe_module()
    case = probe.load_cases(ROOT / "experiments/call-receipts/cases")[0]
    source = tmp_path / "invalid-envelope.json"
    source.write_text(json.dumps([{**case, field: SENTINEL}]))
    completed = subprocess.run([sys.executable, str(PROBE), "--cases", str(source)], capture_output=True, text=True)
    assert completed.returncode == 1
    assert SENTINEL not in completed.stdout + completed.stderr
    assert "invalid fixture fields" in completed.stderr


def test_unsupported_host_stays_unverified():
    probe = probe_module()
    case = next(c for c in probe.load_cases(ROOT / "experiments/call-receipts/cases") if c["case"] == "unknown-host")
    result = probe.evaluate_case(case)
    assert result["outcome"] == "unverified"
    assert result["candidate_eligible"] is False
    assert set(result) == OUTPUT_FIELDS


def test_checked_in_inputs_and_report_have_no_sentinel():
    for path in (ROOT / "experiments/call-receipts/cases").glob("*.json"):
        assert SENTINEL not in path.read_text()
        for case in json.loads(path.read_text()):
            assert "answer" not in case
    assert SENTINEL not in (ROOT / "docs/delivery/call-receipts.md").read_text()
