"""A listed preference map proves both declared choices and their absence."""

import shlex
import sys

import pytest

from agentcourses.conformance import mismatch, run_suite


@pytest.mark.parametrize(
    ("expected", "actual"),
    [
        ({}, {"choose-pace": "pace"}),
        ({"choose-pace": "pace"}, {}),
        ({"choose-pace": "pace"}, {"choose-pace": "topic"}),
        ({"choose-pace": "pace"}, {"choose-pace": "pace", "choose-topic": "topic"}),
    ],
)
def test_preference_mapping_rejects_missing_extra_or_wrong_entries(expected, actual):
    assert mismatch(expected, actual, ".lessons[0].preferences") is not None


def test_reading_objects_still_allow_unlisted_fields():
    assert mismatch({"valid": True}, {"valid": True, "extra": "allowed"}, "") is None
    assert mismatch({"preferences": {}}, {"preferences": {}}, ".lessons[0]") is None


def test_isolated_preference_mutant_fails_both_version_cases(tmp_path):
    adapter = tmp_path / "preference_mutant.py"
    adapter.write_text(
        "import json, sys\n"
        "from agentcourses import describe\n"
        "reading = describe(sys.argv[1])\n"
        "if reading.get('name') == 'legacy-additions':\n"
        "    reading['lessons'][0]['preferences'] = {'choose-pace': 'pace'}\n"
        "if reading.get('name') == 'preferences':\n"
        "    reading['lessons'][0]['preferences']['choose-topic'] = 'topic'\n"
        "print(json.dumps(reading))\n",
        encoding="utf-8",
    )
    outcomes = run_suite(f"{shlex.quote(sys.executable)} {shlex.quote(str(adapter))}")
    failed = {outcome.case for outcome in outcomes if not outcome.ok}
    assert failed == {"13-preferences", "14-legacy-course-with-additions"}
    for outcome in outcomes:
        if not outcome.ok:
            assert ".preferences" in outcome.detail
