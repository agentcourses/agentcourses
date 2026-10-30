"""Each rule in the specification's validation table, proven on a small course."""

from pathlib import Path

import pytest

from agentcourses import load

COURSE = """---
spec: "0.1"
name: sample
description: A sample course.
---

# Sample

## Outcome

A working thing.

## Lessons

1. [Make it](make/LESSON.md)
2. [Finish](finish/LESSON.md)
"""

MAKE = """---
title: Make it
stage: build
checks:
  - id: it-runs
    run: python "$AGENT_LESSON_DIR/checks/it_runs.py"
    verify: It runs.
calls:
  - id: pick-name
    ask: What should it be called?
objectives:
  - id: it-works
    text: It works.
    by: it-runs
---

## Goal

Make the thing.

## Build

Build it together.
"""

FINISH = """---
title: Finish
stage: demonstrate
---

## Goal

Explain the thing.

## Explain back

Ask the learner to explain it.
"""

RUBRIC = """---
pass: 1 of 2
---

- **Explains** what it does
- **Names** one risk
"""


def write(root: Path, files: dict[str, str]) -> Path:
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


@pytest.fixture
def course(tmp_path):
    root = write(tmp_path / "sample", {
        "COURSE.md": COURSE,
        "make/LESSON.md": MAKE,
        "make/checks/it_runs.py": "raise SystemExit(0)\n",
        "make/checks/fixtures/it-runs/pass/app.py": "",
        "make/checks/fixtures/it-runs/fail/app.py": "",
        "finish/LESSON.md": FINISH,
        "finish/tutor/rubric.md": RUBRIC,
    })
    return root


def codes(root, level):
    _, diagnostics = load(root)
    return [d.code for d in diagnostics if d.level == level]


def test_the_sample_course_is_clean(course):
    assert codes(course, "error") == []
    assert codes(course, "warning") == []


def edit(root, rel, old, new):
    path = root / rel
    text = path.read_text(encoding="utf-8")
    assert old in text, f"{old!r} not in {rel}"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


ERRORS = [
    ("frontmatter not a mapping", "COURSE.md", 'spec: "0.1"\nname: sample\ndescription: A sample course.\n', "- a list\n", "bad-frontmatter"),
    ("required field missing", "COURSE.md", "description: A sample course.\n", "", "bad-field"),
    ("field of the wrong type", "make/LESSON.md", "stage: build", "stage: building", "bad-field"),
    ("unsupported spec", "COURSE.md", 'spec: "0.1"', 'spec: "1.0"', "unsupported-spec"),
    ("name differs from folder", "COURSE.md", "name: sample", "name: other", "name-mismatch"),
    ("no lessons list", "COURSE.md", "## Lessons", "## Lesson plan", "missing-lessons"),
    ("link that is not a lesson", "COURSE.md", "make/LESSON.md", "make/NOTES.md", "bad-lesson-link"),
    ("lesson listed twice", "COURSE.md", "2. [Finish](finish/LESSON.md)", "2. [Again](make/LESSON.md)\n3. [Finish](finish/LESSON.md)", "duplicate-lesson"),
    ("lesson outside a phase", "COURSE.md", "2. [Finish]", "### Finish\n\n2. [Finish]", "lesson-outside-phase"),
    ("no goal", "make/LESSON.md", "## Goal", "## Aim", "missing-goal"),
    ("repeated heading", "make/LESSON.md", "## Build", "## Goal\n\nAgain.\n\n## Build", "duplicate-heading"),
    ("duplicate id", "finish/LESSON.md", "stage: demonstrate\n", "stage: demonstrate\ncalls:\n  - id: pick-name\n    ask: Again?\n", "duplicate-id"),
    ("objective naming nothing", "make/LESSON.md", "by: it-runs", "by: no-such-check", "unknown-evidence"),
    ("explain-back objective without explain-back", "make/LESSON.md", "by: it-runs", "by: explain-back", "unknown-evidence"),
    ("quiz without a key", "make/LESSON.md", "## Build", "## Quiz\n\n1. Which?\n   - A\n   - B\n\n## Build", "bad-quiz"),
    ("invalid project option", "COURSE.md", "description: A sample course.\n", "description: A sample course.\nproject: elsewhere\n", "bad-project"),
    ("project folder missing", "COURSE.md", "description: A sample course.\n", "description: A sample course.\nproject: ./starter\n", "bad-project"),
    ("link leaving the course", "make/LESSON.md", "Build it together.", "See [notes](../../notes.md).", "bad-link"),
    ("link to tutor material", "make/LESSON.md", "Build it together.", "See [rubric](../finish/tutor/rubric.md).", "tutor-link"),
    ("lesson id not a kebab id", "COURSE.md", "make/LESSON.md", "Make_It/LESSON.md", "bad-lesson-id"),
]


@pytest.mark.parametrize(("name", "rel", "old", "new", "code"), ERRORS, ids=[e[0] for e in ERRORS])
def test_errors(course, name, rel, old, new, code):
    if code == "bad-lesson-id":
        (course / "make").rename(course / "Make_It")
    edit(course, rel, old, new)
    assert code in codes(course, "error")


def test_unquoted_spec_gets_a_clear_message(course):
    edit(course, "COURSE.md", 'spec: "0.1"', "spec: 0.1")
    _, diagnostics = load(course)
    assert [(d.code, d.message) for d in diagnostics] == [("bad-field", 'spec must be a quoted string, such as spec: "0.1"')]


def test_missing_course_file(tmp_path):
    assert codes(tmp_path, "error") == ["missing-course-file"]


def test_missing_rubric(course):
    (course / "finish/tutor/rubric.md").unlink()
    assert "missing-rubric" in codes(course, "error")


@pytest.mark.parametrize(("old", "new"), [("pass: 1 of 2", "pass: 1 of 3"), ("pass: 1 of 2", "pass: 3 of 2"), ("pass: 1 of 2", "pass: one")])
def test_bad_rubric(course, old, new):
    edit(course, "finish/tutor/rubric.md", old, new)
    assert "bad-rubric" in codes(course, "error")


def test_quiz_key_must_match(course):
    edit(course, "make/LESSON.md", "## Build", "## Quiz\n\n1. Which?\n   - A\n   - B\n\n## Build")
    write(course, {"make/tutor/quiz.yaml": "- answer: 0\n  why: A.\n"})
    assert codes(course, "error") == []
    write(course, {"make/tutor/quiz.yaml": "- answer: 2\n  why: Past the end.\n"})
    assert "bad-quiz" in codes(course, "error")


WARNINGS = [
    ("unknown key", "COURSE.md", "name: sample\n", "name: sample\ncolour: blue\n", "unknown-key"),
    ("no outcome", "COURSE.md", "## Outcome", "## Result", "missing-outcome"),
    ("understand lesson with checks", "make/LESSON.md", "stage: build", "stage: understand", "understand-with-checks"),
    ("demonstrate without explain-back", "make/LESSON.md", "stage: build", "stage: demonstrate", "demonstrate-without-explain-back"),
    ("last lesson not demonstrate", "finish/LESSON.md", "stage: demonstrate", "stage: practise", "last-lesson-not-demonstrate"),
    ("command check without verify", "make/LESSON.md", "    verify: It runs.\n", "", "missing-verify"),
]


@pytest.mark.parametrize(("name", "rel", "old", "new", "code"), WARNINGS, ids=[w[0] for w in WARNINGS])
def test_warnings(course, name, rel, old, new, code):
    edit(course, rel, old, new)
    assert code in codes(course, "warning")
    assert codes(course, "error") == []


def test_build_lesson_without_checks_warns(course):
    write(course, {"make/LESSON.md": "---\ntitle: Make it\nstage: build\n---\n\n## Goal\n\nMake it.\n"})
    assert "stage-without-checks" in codes(course, "warning")


def test_unlisted_lesson_and_unused_rubric_warn(course):
    write(course, {"spare/LESSON.md": "---\ntitle: Spare\n---\n\n## Goal\n\nSpare.\n", "make/tutor/rubric.md": RUBRIC})
    warnings = codes(course, "warning")
    assert "unlisted-lesson" in warnings
    assert "unused-rubric" in warnings


def test_check_without_fixtures_warns(course):
    for kind in ("pass", "fail"):
        (course / f"make/checks/fixtures/it-runs/{kind}/app.py").unlink()
        (course / f"make/checks/fixtures/it-runs/{kind}").rmdir()
    assert "missing-fixtures" in codes(course, "warning")


def test_headings_inside_code_do_not_count(course):
    edit(course, "make/LESSON.md", "## Goal\n\nMake the thing.", "```\n## Goal\n```")
    assert "missing-goal" in codes(course, "error")


def test_phases_are_read_in_order(course):
    edit(course, "COURSE.md", "1. [Make it]", "### Start\n\nBegin here.\n\n1. [Make it]")
    edit(course, "COURSE.md", "2. [Finish]", "### End\n\n2. [Finish]")
    loaded, diagnostics = load(course)
    assert [d for d in diagnostics if d.level == "error"] == []
    assert loaded.phases == [
        {"title": "Start", "intro": "Begin here.", "lessons": ["make"]},
        {"title": "End", "intro": "", "lessons": ["finish"]},
    ]
