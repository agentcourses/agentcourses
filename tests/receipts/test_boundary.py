"""Synthetic authority assertions; these do not qualify any host."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
PROBE = ROOT / "experiments/call-receipts/probe.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("receipt_probe", PROBE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample(**changes):
    binding = dict(snapshot="snapshot-a", lesson="lesson-a", call="call-a", occurrence="input-a", challenge="challenge-a")
    case = dict(case="genuine-isolated", host="embedded", origin="learner", mechanism="isolated-confirmation",
                authority=dict(controller="learner", tutor_access=[]), context=binding.copy(),
                confirmation=binding.copy(), used_occurrences=[], expected_outcome="unverified",
                expected_binding_failures=[], expected_candidate_eligible=True)
    case.update(changes)
    return case


def test_adversarial_cases():
    probe = load_probe()
    cases = probe.load_cases(ROOT / "experiments/call-receipts/cases")
    assert {"genuine-isolated", "tutor-authored", "missing", "repeated", "changed-snapshot", "cross-lesson"} <= {c["case"] for c in cases}
    for case in cases:
        actual = probe.evaluate_case(case)
        assert actual["outcome"] == case["expected_outcome"], case["case"]
        assert actual["binding_failures"] == case["expected_binding_failures"], case["case"]
        assert actual["candidate_eligible"] == case["expected_candidate_eligible"], case["case"]
        assert actual["evidence_class"] == "simulated"
        assert actual["outcome"] != "verified"


@pytest.mark.parametrize("changes", [dict(extra=True), dict(authority={"controller": "learner", "tutor_access": [], "signed": True}), dict(context={"snapshot": "snapshot-a"}), dict(host="made-up"), dict(used_occurrences="input-a"), dict(expected_candidate_eligible=1)])
def test_fixture_envelope_rejects_unknown_or_malformed_fields(changes):
    with pytest.raises(ValueError):
        load_probe().evaluate_case(sample(**changes))


def test_empty_cases_are_invalid(tmp_path):
    with pytest.raises(ValueError, match="empty"):
        load_probe().load_cases(tmp_path)


def test_report_records_each_inspected_host():
    report = load_probe().audit_report(ROOT / "docs/delivery/call-receipts.md")
    assert {h["host"] for h in report["hosts"]} == {"claude-code", "codex", "embedded"}
    assert all(h["evidence_class"] == "inspected" for h in report["hosts"])
    assert report["decision"]["status"] in {"pending", "approved"}


@pytest.mark.parametrize("field", ["version", "source", "source_digest", "commands", "input_origin", "authority", "privacy", "limitations", "evidence_class"])
def test_report_audit_rejects_missing_host_evidence(tmp_path, field):
    probe = load_probe()
    text = (ROOT / "docs/delivery/call-receipts.md").read_text()
    report = probe.audit_report(ROOT / "docs/delivery/call-receipts.md")
    original = json.dumps(report, indent=2)
    del report["hosts"][0][field]
    path = tmp_path / "report.md"
    path.write_text(text.replace(original, json.dumps(report, indent=2)))
    with pytest.raises(ValueError, match="host evidence"):
        probe.audit_report(path)


@pytest.mark.parametrize("host", ["claude-code", "codex", "embedded"])
@pytest.mark.parametrize("access", ["filesystem", "tools", "configuration", "signer"])
def test_forged_envelope(host, access):
    # Copying all success-shaped public fields cannot cross an independent authority boundary.
    result = load_probe().evaluate_case(sample(host=host, authority=dict(controller="learner", tutor_access=[access])))
    assert result["outcome"] == "unverified"
    assert result["candidate_eligible"] is False


def test_public_user_role_is_not_a_receipt():
    result = load_probe().evaluate_case(sample(mechanism="public-envelope"))
    assert result["outcome"] == "unverified"
    assert result["candidate_eligible"] is False


@pytest.mark.parametrize("field", ["snapshot", "lesson", "call", "occurrence", "challenge"])
def test_replay_and_binding_mismatch(field):
    case = sample()
    case["confirmation"][field] = field + "-stale"
    result = load_probe().evaluate_case(case)
    assert result["outcome"] == "rejected"
    assert result["candidate_eligible"] is False
    assert result["binding_failures"] == [field]


def test_replay_and_binding_one_matching_confirmation():
    probe = load_probe()
    case = sample()
    used = []
    results = []
    for attempt in range(3):
        result = probe.evaluate_case({**case, "used_occurrences": used.copy()})
        results.append(result)
        if result["candidate_eligible"]:
            used.append(case["confirmation"]["occurrence"])
    assert sum(r["candidate_eligible"] for r in results) == 1
    assert [r["outcome"] for r in results] == ["unverified", "rejected", "rejected"]
    assert results[-1]["binding_failures"] == ["replay"]



def synthetic_decision():
    # This is a validator test fixture, never an approval of the checked-in report.
    return dict(status="approved", date="2026-10-19", owner="Synthetic test owner", choice="isolated-confirmation",
                owner_input_reference="Synthetic validator fixture only; not actual owner evidence",
                evidence_references=["#host-evidence", "#adversarial-results"],
                verifier_trust="Separate learner controller, protected configuration and durable replay ledger",
                unsupported_policy="unverified", scope="Capability contract only; no actual host qualified",
                limitations="No production verifier or human provenance demonstrated",
                stores_answer_text=False, stores_conversations=False, hashes_free_text=False,
                tutor_can_invoke_verifier=False)


def test_owner_decision_pending_fails_honestly(tmp_path):
    probe = load_probe()
    path = ROOT / "docs/delivery/call-receipts.md"
    report = probe.audit_report(path)
    original = json.dumps(report, indent=2)
    report["decision"] = {"status": "pending"}
    pending = tmp_path / "pending.md"
    pending.write_text(path.read_text().replace(original, json.dumps(report, indent=2)))
    with pytest.raises(ValueError, match="owner-decision-pending"):
        probe.audit_report(pending, require_decision=True)


@pytest.mark.parametrize("field,value", [("date", "not-a-date"), ("owner", ""), ("owner_input_reference", ""),
    ("evidence_references", []), ("verifier_trust", ""), ("unsupported_policy", "verified"),
    ("stores_answer_text", True), ("stores_conversations", True), ("hashes_free_text", True),
    ("tutor_can_invoke_verifier", True), ("choice", "public-envelope")])
def test_decision_cannot_weaken_hard_lines(field, value):
    decision = synthetic_decision()
    decision[field] = value
    with pytest.raises(ValueError):
        load_probe().validate_decision(decision)


def test_decision_validation_checks_attribution_and_both_options():
    probe = load_probe()
    decision = synthetic_decision()
    probe.validate_decision(decision)
    probe.validate_decision({**decision, "choice": "defer-unverified"})
    for field in decision:
        with pytest.raises(ValueError):
            probe.validate_decision({k: v for k, v in decision.items() if k != field})


def test_make_check_requires_report_and_owner_choice_after_inherited_checks():
    makefile = (ROOT / "Makefile").read_text()
    assert "--audit-report" in makefile
    assert "--require-decision" in makefile
    assert "--cases" in makefile
    assert makefile.index("$(MAKE) check-receipts") > makefile.index("pnpm --dir site exec playwright test")



def test_attributable_decision_fixture_can_pass_mechanical_gate(tmp_path):
    probe = load_probe()
    path = ROOT / "docs/delivery/call-receipts.md"
    report = probe.audit_report(path)
    original = json.dumps(report, indent=2)
    report["decision"] = synthetic_decision()
    synthetic = tmp_path / "synthetic-decision.md"
    synthetic.write_text(path.read_text().replace(original, json.dumps(report, indent=2)))
    assert probe.audit_report(synthetic, require_decision=True)["decision"]["owner"] == "Synthetic test owner"



def deferred_report_fixture(tmp_path):
    probe = load_probe()
    path = ROOT / "docs/delivery/call-receipts.md"
    report = probe.audit_report(path)
    original = json.dumps(report, indent=2)
    report["decision"] = {**synthetic_decision(), "choice": "defer-unverified",
                          "scope": "Records and settlement remain blocked pending a demonstrated host"}
    deferred = tmp_path / "docs/delivery/call-receipts.md"
    deferred.parent.mkdir(parents=True)
    deferred.write_text(path.read_text().replace(original, json.dumps(report, indent=2)))
    return deferred


def test_deferred_choice_blocks_required_decision_cli(tmp_path):
    deferred = deferred_report_fixture(tmp_path)
    audit = subprocess.run([sys.executable, str(PROBE), "--audit-report", str(deferred)], capture_output=True, text=True)
    assert audit.returncode == 0, audit.stderr
    required = subprocess.run([sys.executable, str(PROBE), "--require-decision", str(deferred)], capture_output=True, text=True)
    assert required.returncode == 1
    assert "owner-decision-deferred" in required.stderr
    assert "owner decision approved" not in required.stdout


def test_deferred_choice_blocks_receipt_make_gate(tmp_path):
    deferred_report_fixture(tmp_path)
    shutil.copytree(ROOT / "experiments/call-receipts/cases", tmp_path / "experiments/call-receipts/cases")
    completed = subprocess.run(["make", "check-receipts", f"CHECK_ROOT={tmp_path}"], cwd=ROOT, capture_output=True, text=True)
    assert completed.returncode == 2
    assert "Receipt report complete; owner decision checked separately" in completed.stdout
    assert "owner-decision-deferred" in completed.stderr
    assert "owner decision approved" not in completed.stdout
