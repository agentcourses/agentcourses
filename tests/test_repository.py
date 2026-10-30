"""The examples, conformance suite, schemas and specification stay true to each other."""

import json
import os
import re
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from agentcourses import load
from agentcourses.conformance import run_suite
from agentcourses.fixtures import run_fixtures

ROOT = Path(__file__).parents[1]
EXAMPLES = sorted(p for p in (ROOT / "examples").iterdir() if p.is_dir())
SPEC = (ROOT / "spec/specification.md").read_text(encoding="utf-8")
AGENTCOURSES = Path(sys.executable).with_name("agentcourses")


@pytest.mark.parametrize("example", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_examples_are_valid_without_warnings(example):
    _, diagnostics = load(example)
    assert [f"{d.code}: {d.message}" for d in diagnostics] == []


@pytest.mark.parametrize("example", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_example_fixtures_pass(example, monkeypatch):
    # Example checks call `python`; use the interpreter running the tests.
    monkeypatch.setenv("PATH", f"{Path(sys.executable).parent}{os.pathsep}{os.environ['PATH']}")
    course, _ = load(example)
    assert all(r.ok for r in run_fixtures(course))


def test_reference_reading_passes_every_case():
    outcomes = run_suite(f"{AGENTCOURSES} describe")
    assert [(o.case, o.detail) for o in outcomes if not o.ok] == []
    assert len(outcomes) >= 15


def test_faulty_reading_is_caught():
    adapter = f"{sys.executable} {ROOT / 'tests/faulty_adapter.py'}"
    failed = {o.case for o in run_suite(adapter) if not o.ok}
    assert "03-phases" in failed
    assert {case for case in failed if case.startswith("2")} == {
        p.name for p in (ROOT / "conformance/cases").iterdir() if p.name.startswith("2")
    }


def test_specification_stays_small():
    lines = SPEC.count("\n")
    musts = len(re.findall(r"\bMUST\b", SPEC))
    assert lines <= 500, f"the specification has {lines} lines"
    assert musts <= 60, f"the specification has {musts} MUSTs"


def test_progress_example_matches_its_schema():
    example = re.search(r"## The progress file.*?```json\n(.*?)```", SPEC, re.S)[1]
    schema = json.loads((ROOT / "schemas/progress.schema.json").read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(json.loads(example))) == []


def test_readme_shows_the_minimal_example():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for rel in ("COURSE.md", "finish/LESSON.md", "finish/tutor/rubric.md"):
        assert (ROOT / "examples/minimal" / rel).read_text(encoding="utf-8").strip() in readme


@pytest.mark.parametrize("schema", sorted((ROOT / "schemas").glob("*.json")), ids=lambda p: p.name)
def test_schemas_are_valid(schema):
    Draft202012Validator.check_schema(json.loads(schema.read_text(encoding="utf-8")))
