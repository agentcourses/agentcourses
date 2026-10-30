"""Compare a runner's reading of each conformance case with the expected reading."""

from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Outcome:
    case: str
    ok: bool
    detail: str = ""


def cases_dir() -> Path:
    packaged = Path(__file__).parent / "conformance_cases"
    return packaged if packaged.is_dir() else Path(__file__).parents[2] / "conformance" / "cases"


def run_suite(adapter: str, cases: Path | None = None) -> list[Outcome]:
    """Run `<adapter> <course-folder>` for every case and compare its JSON output."""
    outcomes = []
    for case in sorted(p for p in (cases or cases_dir()).iterdir() if p.is_dir()):
        expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
        course = case / expected.pop("course")
        try:
            done = subprocess.run(
                [*shlex.split(adapter), str(course)], capture_output=True, text=True, timeout=60
            )
            actual = json.loads(done.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as error:
            outcomes.append(Outcome(case.name, False, f"no JSON reading: {error}"))
            continue
        problem = mismatch(expected, actual, "")
        outcomes.append(Outcome(case.name, problem is None, problem or ""))
    return outcomes


def mismatch(expected, actual, where: str) -> str | None:
    """Every key in expected must match. Keys the runner adds are ignored; lists must match in full."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return f"{where or 'reading'}: expected an object"
        for key, value in expected.items():
            if key not in actual:
                return f"{where}.{key}: missing"
            problem = mismatch(value, actual[key], f"{where}.{key}")
            if problem:
                return problem
        return None
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return f"{where}: expected {json.dumps(expected)}, got {json.dumps(actual)}"
        for index, (want, got) in enumerate(zip(expected, actual)):
            problem = mismatch(want, got, f"{where}[{index}]")
            if problem:
                return problem
        return None
    if expected != actual:
        return f"{where}: expected {json.dumps(expected)}, got {json.dumps(actual)}"
    return None
