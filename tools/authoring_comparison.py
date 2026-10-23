"""Internal, locked authoring comparison; synthetic results are not owner evidence."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
import argparse
import hashlib
import json
import math
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASELINE_COMMIT = "f39cbea910c475f76d87ae186184f1c1d1150f34"
PROTOCOL = ROOT / "docs/delivery/authoring-comparison-protocol.md"
ORDER = (("baseline", "minimal", "A"), ("new", "minimal", "B"),
         ("new", "representative", "A"), ("baseline", "representative", "B"))
EXPLANATIONS = ("required_material", "assessment", "tutor_privacy", "consent")
SESSION_FIELDS = ("participant", "synthetic", "baseline_commit", "candidate_commit", "protocol_sha256", "runs")
RUN_FIELDS = ("variant", "started_at", "ended_at", "pauses", "active_seconds", "completed",
              "errors", "assistance", "comprehension")


def _mapping(value, name):
    if not isinstance(value, Mapping):
        raise ValueError(f"{name}: expected mapping")
    return value


def _keys(value, allowed, name):
    _mapping(value, name)
    if set(value) - set(allowed):
        raise ValueError(f"{name}: unknown fields")


def _text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: expected non-empty text")


def _boolean(value, name):
    if type(value) is not bool:
        raise ValueError(f"{name}: expected boolean")


def _number(value, name):
    if (type(value) not in (int, float) or value < 0
            or (type(value) is float and not math.isfinite(value))
            or (type(value) is int and value > 10 ** 12)):
        raise ValueError(f"{name}: expected finite non-negative number")


def _list(value, name):
    if not isinstance(value, list):
        raise ValueError(f"{name}: expected list")


def _timestamp(value, name):
    if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|\+00:00)", value):
        raise ValueError(f"{name}: expected UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError(f"{name}: invalid UTC timestamp") from error
    return parsed


def _json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _load(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=_json_pairs)


def _git_bytes(path):
    try:
        return subprocess.run(["git", "show", f"{BASELINE_COMMIT}:{path}"], cwd=ROOT,
                              check=True, capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError(f"baseline: cannot read pinned Git bytes for {path}") from error


def verify_baseline(path: Path) -> Mapping:
    """Verify immutable source bytes, rather than the mutable working schemas."""
    try:
        baseline = _load(path)
        _keys(baseline, ("baseline_commit", "candidate", "manifest_sha256", "schemas", "protocol_sha256"), "baseline")
        if baseline.get("baseline_commit") != BASELINE_COMMIT:
            raise ValueError("baseline: source commit differs from locked source")
        source = _git_bytes("schemas/manifest.json")
        manifest = json.loads(source)
        schemas = manifest["releases"][0]["schemas"]
        if (baseline.get("candidate") != manifest["candidate"] or len(schemas) != 8
                or baseline.get("schemas") != schemas
                or baseline.get("manifest_sha256") != hashlib.sha256(source).hexdigest()
                or baseline.get("protocol_sha256") != hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()):
            raise ValueError("baseline: manifest, schema inventory or protocol differs")
        for entry in schemas:
            if hashlib.sha256(_git_bytes(entry["path"])).hexdigest() != entry["sha256"]:
                raise ValueError(f"baseline: schema bytes differ: {entry['path']}")
        return baseline
    except (OSError, KeyError, TypeError, ValueError) as error:
        raise ValueError(f"baseline verification failed: {error}") from error


def _validate_run(run, name):
    """Validate every supplied measure even when another measure is missing."""
    _keys(run, ("candidate", "task", *RUN_FIELDS), name)
    for field in ("started_at", "ended_at"):
        if field in run:
            _timestamp(run[field], name + ":" + field)
    if "active_seconds" in run:
        _number(run["active_seconds"], name + ":active_seconds")
    if "completed" in run:
        _boolean(run["completed"], name + ":completed")
    if "comprehension" in run:
        _keys(run["comprehension"], EXPLANATIONS, name + ":comprehension")
        for key, value in run["comprehension"].items():
            _boolean(value, name + ":comprehension." + key)
    if "errors" in run:
        _list(run["errors"], name + ":errors")
        codes = set()
        for entry in run["errors"]:
            _keys(entry, ("code", "description"), name + ":error")
            for key in ("code", "description"):
                _text(entry.get(key), name + ":error." + key)
            if entry["code"] in codes:
                raise ValueError(name + ":errors: codes must be distinct")
            codes.add(entry["code"])
    pauses = []
    if "pauses" in run:
        _list(run["pauses"], name + ":pauses")
        for pause in run["pauses"]:
            _keys(pause, ("start", "end", "reason"), name + ":pause")
            _text(pause.get("reason"), name + ":pause.reason")
            a = _timestamp(pause.get("start"), name + ":pause.start")
            b = _timestamp(pause.get("end"), name + ":pause.end")
            if b <= a:
                raise ValueError(name + ":pause: duration must be positive")
            pauses.append((a, b))
        ordered = sorted(pauses)
        if any(right[0] < left[1] for left, right in zip(ordered, ordered[1:])):
            raise ValueError(name + ":pause: overlapping interruptions")
    if "assistance" in run:
        _list(run["assistance"], name + ":assistance")
        for entry in run["assistance"]:
            _keys(entry, ("time", "text"), name + ":assistance")
            _timestamp(entry.get("time"), name + ":assistance.time")
            _text(entry.get("text"), name + ":assistance.text")
    if "started_at" not in run or "ended_at" not in run:
        return
    start = _timestamp(run["started_at"], name)
    end = _timestamp(run["ended_at"], name)
    if end <= start:
        raise ValueError(name + ":timing: end must follow start")
    if any(a < start or b > end for a, b in pauses):
        raise ValueError(name + ":pause: interruption outside run")
    for entry in run.get("assistance", []):
        if not start <= _timestamp(entry["time"], name) <= end:
            raise ValueError(name + ":assistance: time outside run")
    if "pauses" in run and "active_seconds" in run:
        active = ((end - start) - sum((b - a for a, b in pauses), timedelta())).total_seconds()
        if not math.isclose(active, run["active_seconds"], rel_tol=0, abs_tol=0.000001):
            raise ValueError(name + ":timing: active_seconds differs from elapsed minus pauses")


def score_comparison(observations: Mapping) -> Mapping:
    """Return complete measures and deterministic reasons, without treating gaps as zero."""
    _keys(observations, SESSION_FIELDS, "observations")
    missing = ["missing-field:" + field for field in SESSION_FIELDS if field not in observations]
    if "participant" in observations:
        _text(observations["participant"], "participant")
    if "synthetic" in observations:
        _boolean(observations["synthetic"], "synthetic")
    if "baseline_commit" in observations and observations["baseline_commit"] != BASELINE_COMMIT:
        raise ValueError("baseline_commit: expected locked source")
    if "candidate_commit" in observations and (not isinstance(observations["candidate_commit"], str)
            or not re.fullmatch(r"[0-9a-f]{40}", observations["candidate_commit"])):
        raise ValueError("candidate_commit: expected full Git commit identifier")
    if "protocol_sha256" in observations and observations["protocol_sha256"] != hashlib.sha256(PROTOCOL.read_bytes()).hexdigest():
        raise ValueError("protocol_sha256: expected locked protocol bytes")
    source_runs = observations.get("runs", [])
    _list(source_runs, "runs")
    indexed = {}
    positions = []
    for run in source_runs:
        _mapping(run, "run")
        candidate, task = run.get("candidate"), run.get("task")
        if candidate not in ("baseline", "new"):
            raise ValueError("run:candidate: expected baseline or new")
        if task not in ("minimal", "representative"):
            raise ValueError("run:task: expected minimal or representative")
        key = (candidate, task)
        if key in indexed:
            raise ValueError("runs: duplicate candidate/task")
        position = next(i for i, pair in enumerate(ORDER) if pair[:2] == key)
        if "variant" in run and run["variant"] != ORDER[position][2]:
            raise ValueError("run:variant: differs from fixed protocol")
        positions.append(position)
        _validate_run(run, candidate + ":" + task)
        indexed[key] = run
    if positions != sorted(positions):
        raise ValueError("runs: order differs from fixed protocol")
    previous_end = None
    for run in source_runs:
        start = _timestamp(run["started_at"], "run") if "started_at" in run else None
        end = _timestamp(run["ended_at"], "run") if "ended_at" in run else None
        if previous_end and start and start < previous_end:
            raise ValueError("runs: order has overlapping run times")
        if end:
            previous_end = end
    runs = []
    for candidate, task, variant in ORDER:
        raw = indexed.get((candidate, task))
        if raw is None:
            missing.append(f"missing-run:{candidate}:{task}")
            run = dict(candidate=candidate, task=task, variant=variant,
                       **{field: None for field in RUN_FIELDS if field != "variant"})
            run["comprehension"] = dict.fromkeys(EXPLANATIONS)
        else:
            run = deepcopy(dict(raw))
            for field in RUN_FIELDS:
                if field not in raw:
                    missing.append(f"missing-field:{candidate}:{task}:{field}")
                    run[field] = None
            scores = raw.get("comprehension", {})
            run["comprehension"] = {key: scores.get(key) for key in EXPLANATIONS}
            if "comprehension" in raw:
                missing.extend(f"missing-field:{candidate}:{task}:comprehension.{key}"
                               for key in EXPLANATIONS if key not in scores)
        runs.append(run)
    totals = {}
    comprehension = {}
    for candidate in ("baseline", "new"):
        selected = [run for run in runs if run["candidate"] == candidate]
        totals[candidate] = {}
        for output, field in (("active_seconds", "active_seconds"), ("errors", "errors"), ("help", "assistance")):
            values = [run[field] for run in selected]
            totals[candidate][output] = None if any(v is None for v in values) else sum(
                len(v) if isinstance(v, list) else v for v in values)
        comprehension[candidate] = {run["task"]: run["comprehension"] for run in selected}
    reasons = missing
    verdict = "incomplete"
    if not missing:
        new = [run for run in runs if run["candidate"] == "new"]
        failures = (
            ("completion", any(not run["completed"] for run in new)),
            ("time-cap", any(run["active_seconds"] > (1200 if run["task"] == "minimal" else 2400) for run in runs)),
            ("assistance", totals["new"]["help"] > 0),
            ("active-time", totals["new"]["active_seconds"] >= totals["baseline"]["active_seconds"]),
            ("errors", totals["new"]["errors"] > totals["baseline"]["errors"]),
            ("comprehension", any(not score for run in new for score in run["comprehension"].values())),
        )
        reasons = [name for name, failed in failures if failed]
        verdict = "fail" if reasons else "pass"
    return dict(verdict=verdict, synthetic=observations.get("synthetic"), totals=totals,
                comprehension=comprehension, runs=runs, reasons=reasons)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        verify_baseline(args.baseline)
        result = score_comparison(_load(args.observations))
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0 if result["verdict"] == "pass" else 1
    except (OSError, ValueError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    sys.exit(main())
