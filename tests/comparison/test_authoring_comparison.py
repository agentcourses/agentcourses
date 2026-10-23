"""Synthetic observations exercise the instrument, never owner performance."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = "f39cbea910c475f76d87ae186184f1c1d1150f34"
PROTOCOL = ROOT / "docs/delivery/authoring-comparison-protocol.md"
FIELDS = ("required_material", "assessment", "tutor_privacy", "consent")
ORDER = (("baseline", "minimal", "A"), ("new", "minimal", "B"),
         ("new", "representative", "A"), ("baseline", "representative", "B"))


def observations(case="pass"):
    """Build input independently so absent production files fail at runtime."""
    protocol_hash = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() if PROTOCOL.exists() else "0" * 64
    data = dict(participant="synthetic-owner", synthetic=True, baseline_commit=BASE,
                candidate_commit="a" * 40, protocol_sha256=protocol_hash, runs=[])
    cursor = datetime(2026, 10, 23, 9, tzinfo=timezone.utc)
    for (candidate, task, variant), seconds in zip(ORDER, (900, 600, 1200, 1800)):
        if case == "slower" and (candidate, task) == ("new", "representative"):
            seconds = 2300
        run = dict(candidate=candidate, task=task, variant=variant,
                   started_at=cursor.isoformat().replace("+00:00", "Z"),
                   ended_at=(cursor + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z"),
                   pauses=[], active_seconds=seconds, completed=True, errors=[], assistance=[],
                   comprehension=dict.fromkeys(FIELDS, True))
        if case == "assisted" and candidate == "new" and task == "minimal":
            run["assistance"] = [dict(time=run["started_at"], text="Add a lesson reference.")]
        data["runs"].append(run)
        cursor += timedelta(seconds=seconds + 60)
    if case == "incomplete":
        data["runs"].pop()
    return data


def expected(data, verdict="pass", reasons=None):
    runs = []
    totals = {}
    comprehension = {}
    for candidate, task, variant in ORDER:
        found = next((deepcopy(r) for r in data["runs"] if (r["candidate"], r["task"]) == (candidate, task)), None)
        if found is None:
            found = dict(candidate=candidate, task=task, variant=variant, started_at=None, ended_at=None,
                         pauses=None, active_seconds=None, completed=None, errors=None, assistance=None,
                         comprehension=dict.fromkeys(FIELDS))
        runs.append(found)
    for candidate in ("baseline", "new"):
        selected = [r for r in runs if r["candidate"] == candidate]
        totals[candidate] = {}
        for output, field in (("active_seconds", "active_seconds"), ("errors", "errors"), ("help", "assistance")):
            values = [r[field] for r in selected]
            totals[candidate][output] = None if any(v is None for v in values) else sum(
                len(v) if isinstance(v, list) else v for v in values)
        comprehension[candidate] = {r["task"]: r["comprehension"] for r in selected}
    return dict(verdict=verdict, synthetic=data["synthetic"], totals=totals,
                comprehension=comprehension, runs=runs, reasons=reasons or [])


def cli(data, tmp_path, baseline=None):
    path = tmp_path / "observations.json"
    path.write_text(json.dumps(data))
    result = subprocess.run([sys.executable, str(ROOT / "tools/authoring_comparison.py"),
                             "--observations", str(path), "--baseline",
                             str(baseline or ROOT / "docs/delivery/authoring-baseline.json")],
                            text=True, capture_output=True, cwd=ROOT)
    try:
        output = json.loads(result.stdout)
    except ValueError:
        output = None
    return result, output


def scorer():
    path = ROOT / "tools/authoring_comparison.py"
    assert path.is_file(), "missing scorer result: tools/authoring_comparison.py is absent"
    spec = importlib.util.spec_from_file_location("authoring_comparison", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_baseline_bytes():
    path = ROOT / "docs/delivery/authoring-baseline.json"
    assert path.is_file(), "absent baseline manifest: docs/delivery/authoring-baseline.json"
    manifest = json.loads(path.read_text())
    assert manifest["baseline_commit"] == BASE
    assert len(manifest["schemas"]) == 8
    assert scorer().verify_baseline(path) == manifest
    for entry in manifest["schemas"]:
        payload = subprocess.run(["git", "show", f"{BASE}:{entry['path']}"], cwd=ROOT,
                                 check=True, capture_output=True).stdout
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]


def test_synthetic_pass(tmp_path):
    data = observations()
    result, output = cli(data, tmp_path)
    assert result.returncode == 0, f"CLI exit {result.returncode}: {result.stderr}; expected passing complete result"
    assert output == expected(data)


def test_assistance_fails(tmp_path):
    data = observations("assisted")
    result, output = cli(data, tmp_path)
    assert output == expected(data, "fail", ["assistance"]), f"missing scorer result: {output!r}; expected exactly ['assistance']"
    assert result.returncode == 1


def test_missing_observation_is_incomplete(tmp_path):
    data = observations("incomplete")
    result, output = cli(data, tmp_path)
    assert output == expected(data, "incomplete", ["missing-run:baseline:representative"]), f"missing scorer result: {output!r}; expected incomplete with missing-run:baseline:representative"
    assert result.returncode == 1


def test_slower_fails(tmp_path):
    data = observations("slower")
    result, output = cli(data, tmp_path)
    assert output == expected(data, "fail", ["active-time"]), f"missing scorer result: {output!r}; expected exactly ['active-time']"
    assert result.returncode == 1


@pytest.mark.parametrize("case", ["pass", "assisted", "incomplete", "slower"])
def test_checked_in_synthetic_fixture(case):
    fixture = ROOT / "tests/comparison/fixtures" / f"{case}.json"
    assert fixture.is_file(), f"missing synthetic fixture: {fixture.name}"
    assert json.loads(fixture.read_text()) == observations(case)


def test_all_failure_reasons_are_ordered():
    data = observations()
    run = data["runs"][1]
    run.update(completed=False, active_seconds=1201, errors=[dict(code="broken-ref", description="Missing target")],
               assistance=[dict(time=run["started_at"], text="Task-specific help")])
    start = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
    run["ended_at"] = (start + timedelta(seconds=1201)).isoformat()
    run["comprehension"]["consent"] = False
    data["runs"][2]["active_seconds"] = 2399
    start = datetime.fromisoformat(data["runs"][2]["started_at"].replace("Z", "+00:00")) + timedelta(seconds=600)
    data["runs"][2]["started_at"] = start.isoformat()
    data["runs"][2]["ended_at"] = (start + timedelta(seconds=2399)).isoformat()
    start = start + timedelta(seconds=2459)
    data["runs"][3]["started_at"] = start.isoformat()
    data["runs"][3]["ended_at"] = (start + timedelta(seconds=1800)).isoformat()
    assert scorer().score_comparison(data) == expected(data, "fail", ["completion", "time-cap", "assistance", "active-time", "errors", "comprehension"])


@pytest.mark.parametrize("field", ["active_seconds", "errors", "assistance", "completed", "started_at", "ended_at", "pauses", "variant"])
def test_missing_run_field_retains_known_measures(field):
    data = observations()
    del data["runs"][1][field]
    output = scorer().score_comparison(data)
    assert output["verdict"] == "incomplete"
    assert output["reasons"] == [f"missing-field:new:minimal:{field}"]
    assert output["runs"][1][field] is None
    assert output["totals"]["baseline"] == dict(active_seconds=2700, errors=0, help=0)
    if field in ("active_seconds", "errors", "assistance"):
        total = {"assistance": "help"}.get(field, field)
        assert output["totals"]["new"][total] is None


@pytest.mark.parametrize("field", FIELDS)
def test_missing_explanation_is_explicit(field):
    data = observations()
    del data["runs"][1]["comprehension"][field]
    output = scorer().score_comparison(data)
    assert output["verdict"] == "incomplete"
    assert output["reasons"] == [f"missing-field:new:minimal:comprehension.{field}"]
    assert output["comprehension"]["new"]["minimal"][field] is None
    assert output["totals"]["new"] == dict(active_seconds=1800, errors=0, help=0)


@pytest.mark.parametrize("field", tuple(observations()))
def test_missing_session_field_is_incomplete(field):
    data = observations()
    module = scorer()
    assert set(data) == set(module.SESSION_FIELDS)
    del data[field]
    output = module.score_comparison(data)
    assert output["verdict"] == "incomplete"
    reasons = [f"missing-field:{field}"]
    if field == "runs":
        reasons.extend(f"missing-run:{candidate}:{task}" for candidate, task, _ in ORDER)
    assert output["reasons"] == reasons


@pytest.mark.parametrize("mutation, message", [
    (lambda d: d["runs"][1].update(active_seconds=-1), "active_seconds"),
    (lambda d: d["runs"][1].update(active_seconds=True), "active_seconds"),
    (lambda d: d["runs"][1].update(active_seconds=float("nan")), "active_seconds"),
    (lambda d: d["runs"][1].update(active_seconds=599), "timing"),
    (lambda d: d["runs"][1].update(completed="yes"), "completed"),
    (lambda d: d["runs"][1]["comprehension"].update(consent=1), "consent"),
    (lambda d: d["runs"][1].update(started_at="2026-10-23T09:00:00"), "UTC"),
    (lambda d: d["runs"][1].update(ended_at=d["runs"][1]["started_at"]), "timing"),
    (lambda d: d["runs"][1].update(variant="A"), "variant"),
    (lambda d: d["runs"].reverse(), "order"),
    (lambda d: d["runs"].append(deepcopy(d["runs"][0])), "duplicate"),
    (lambda d: d["runs"][1].update(candidate="other"), "candidate"),
    (lambda d: d.update(baseline_commit="b" * 40), "baseline_commit"),
    (lambda d: d.update(candidate_commit="main"), "candidate_commit"),
    (lambda d: d.update(protocol_sha256="0" * 64), "protocol_sha256"),
    (lambda d: d.update(synthetic="true"), "synthetic"),
    (lambda d: d["runs"][1].update(errors=[dict(code="x", description="x"), dict(code="x", description="x")]), "distinct"),
    (lambda d: d["runs"][1].update(assistance=[dict(time="2026-10-23T00:00:00Z", text="help")]), "assistance"),
])
def test_malformed_observations_raise(mutation, message):
    data = observations()
    mutation(data)
    with pytest.raises(ValueError, match=message):
        scorer().score_comparison(data)


def test_recorded_pause_is_subtracted():
    data = observations()
    run = data["runs"][1]
    start = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
    run["pauses"] = [dict(start=(start + timedelta(seconds=60)).isoformat(),
                          end=(start + timedelta(seconds=120)).isoformat(), reason="External interruption")]
    run["active_seconds"] = 540
    assert scorer().score_comparison(data) == expected(data)


@pytest.mark.parametrize("pauses", [
    [(60, 120), (100, 140)], [(120, 60)], [(-10, 10)], [(500, 700)],
])
def test_invalid_pause_boundaries(pauses):
    data = observations()
    run = data["runs"][1]
    start = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
    run["pauses"] = [dict(start=(start + timedelta(seconds=a)).isoformat(),
                          end=(start + timedelta(seconds=b)).isoformat(), reason="External interruption")
                      for a, b in pauses]
    with pytest.raises(ValueError, match="pause"):
        scorer().score_comparison(data)


def test_equal_time_fails_and_cap_boundary_passes():
    data = observations()
    data["runs"][1]["active_seconds"] = 1200
    data["runs"][1]["ended_at"] = data["runs"][2]["started_at"] = "2026-10-23T09:36:00Z"
    data["runs"][2]["active_seconds"] = 1500
    data["runs"][2]["ended_at"] = data["runs"][3]["started_at"] = "2026-10-23T10:01:00Z"
    data["runs"][3]["ended_at"] = "2026-10-23T10:31:00Z"
    assert scorer().score_comparison(data) == expected(data, "fail", ["active-time"])
    data["runs"][2]["active_seconds"] = 1499
    data["runs"][2]["ended_at"] = "2026-10-23T10:00:59Z"
    assert scorer().score_comparison(data) == expected(data)


def test_real_observations_remain_distinct_from_synthetic():
    data = observations()
    data["synthetic"] = False
    assert scorer().score_comparison(data) == expected(data)


@pytest.mark.parametrize("field", ["baseline_commit", "manifest_sha256", "protocol_sha256", "schemas"])
def test_baseline_tampering_is_refused(field, tmp_path):
    source = ROOT / "docs/delivery/authoring-baseline.json"
    assert source.is_file(), "absent baseline manifest: docs/delivery/authoring-baseline.json"
    manifest = json.loads(source.read_text())
    manifest[field] = [] if field == "schemas" else "0" * (40 if field == "baseline_commit" else 64)
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="baseline"):
        scorer().verify_baseline(path)


def test_malformed_cli_returns_two(tmp_path):
    data = observations()
    data["runs"][1]["active_seconds"] = None
    result, output = cli(data, tmp_path)
    assert result.returncode == 2
    assert output is None
    assert "active_seconds" in result.stderr, f"expected active_seconds validation error; actual stderr: {result.stderr}"


def test_duplicate_json_keys_are_refused(tmp_path):
    path = tmp_path / "duplicate.json"
    path.write_text('{"synthetic":true,"synthetic":false}')
    result = subprocess.run([sys.executable, str(ROOT / "tools/authoring_comparison.py"),
                             "--observations", str(path), "--baseline",
                             str(ROOT / "docs/delivery/authoring-baseline.json")],
                            text=True, capture_output=True)
    assert result.returncode == 2
    assert "duplicate" in result.stderr, f"expected duplicate JSON key error; actual stderr: {result.stderr}"


def test_huge_numeric_value_is_malformed():
    data = observations()
    data["runs"][1]["active_seconds"] = 10 ** 1000
    with pytest.raises(ValueError, match="active_seconds"):
        scorer().score_comparison(data)


@pytest.mark.parametrize("position", [0, 3])
def test_baseline_task_caps_also_apply(position):
    data = observations()
    data["runs"][position]["active_seconds"] = 1201 if position == 0 else 2401
    cursor = datetime(2026, 10, 23, 9, tzinfo=timezone.utc)
    for run in data["runs"]:
        run["started_at"] = cursor.isoformat()
        cursor += timedelta(seconds=run["active_seconds"])
        run["ended_at"] = cursor.isoformat()
        cursor += timedelta(seconds=60)
    assert scorer().score_comparison(data) == expected(data, "fail", ["time-cap"])


def test_run_overlap_is_malformed():
    data = observations()
    data["runs"][1]["started_at"] = "2026-10-23T09:14:00Z"
    data["runs"][1]["ended_at"] = "2026-10-23T09:24:00Z"
    with pytest.raises(ValueError, match="overlapping run"):
        scorer().score_comparison(data)


def test_missing_scores_do_not_hide_bad_timing():
    data = observations()
    del data["runs"][1]["completed"]
    data["runs"][1]["active_seconds"] = 5
    with pytest.raises(ValueError, match="timing"):
        scorer().score_comparison(data)
