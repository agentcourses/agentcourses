"""Published schemas accept both course versions without storing learner answers."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from agentcourses import SPEC_VERSION

SCHEMAS = Path(__file__).parents[1] / "schemas"


def validator(name):
    return Draft202012Validator(json.loads((SCHEMAS / f"{name}.schema.json").read_text()))


def test_current_spec_version_and_schema_addresses():
    assert SPEC_VERSION == "0.2"
    for path in SCHEMAS.glob("*.schema.json"):
        schema = json.loads(path.read_text())
        assert schema["$id"] == f"https://agentcourses.io/schemas/0.2/{path.name}"


@pytest.mark.parametrize("version", ["0.1", "0.2"])
def test_course_schema_accepts_supported_versions(version):
    assert list(validator("course").iter_errors({"spec": version, "name": "sample", "description": "A course."})) == []


@pytest.mark.parametrize("version", ["0.1", "0.2"])
def test_progress_versions_share_the_same_content_free_shape(version):
    progress = {
        "spec": version,
        "course": {"name": "sample", "version": "1.0.0"},
        "project": "own",
        "current": "make",
        "lessons": {"make": "done", "finish": "skipped"},
        "calls": {"pick-name": "learner"},
        "objectives": {"it-works": {"evidence": "checked", "at": "2026-11-18T12:00:00Z"}},
    }
    check = validator("progress")
    assert list(check.iter_errors(progress)) == []
    for field in ("answers", "preferences", "homework", "teaching"):
        assert list(check.iter_errors({**progress, field: {"pace": "slow"}}))
    assert list(check.iter_errors({**progress, "calls": {"pick-name": "slow"}}))


@pytest.mark.parametrize("name, document", [
    ("course", {"spec": "0.3", "name": "sample", "description": "A course."}),
    ("progress", {"spec": "0.3", "course": {"name": "sample"}, "lessons": {}}),
])
def test_schemas_refuse_future_versions(name, document):
    assert list(validator(name).iter_errors(document))
