"""Each rule in the specification's validation table, proven on a small course."""

from pathlib import Path

import pytest

from agentcourses import describe, load

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
    assert [(d.code, d.message) for d in diagnostics] == [("bad-field", 'spec must be a quoted string, such as spec: "0.2"')]


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


@pytest.fixture
def additions(course):
    edit(course, "COURSE.md", 'spec: "0.1"', 'spec: "0.2"')
    edit(course, "COURSE.md", "## Lessons", "## Teaching\n\nLet the learner set the pace.\n\n## Lessons\n\n### Make a thing\n\nBegin here.")
    edit(course, "COURSE.md", "2. [Finish]", "\nYou made the thing.\n\n### Explain it\n\n2. [Finish]")
    edit(course, "make/LESSON.md", "    ask: What should it be called?", "    ask: What should it be called?\n    preference: project-name")
    edit(course, "make/LESSON.md", "Build it together.", "Build it together.\n\n## Homework\n\nShow a friend.")
    return course


def test_0_2_recognises_every_addition(additions):
    assert codes(additions, "error") == []
    assert codes(additions, "warning") == []
    reading = describe(additions)
    assert reading["spec"] == "0.2"
    assert reading["teaching"] is True
    assert reading["phases"] == [
        {"title": "Make a thing", "lessons": ["make"], "closing": True},
        {"title": "Explain it", "lessons": ["finish"], "closing": False},
    ]
    assert reading["lessons"][0]["homework"] is True
    assert reading["lessons"][0]["calls"] == ["pick-name"]
    assert reading["lessons"][0]["preferences"] == {"pick-name": "project-name"}
    assert reading["lessons"][1]["homework"] is False
    assert reading["lessons"][1]["preferences"] == {}


def test_0_1_leaves_additions_unrecognised_and_warns_once_each(additions):
    edit(additions, "COURSE.md", 'spec: "0.2"', 'spec: "0.1"')
    assert codes(additions, "error") == []
    assert sorted(codes(additions, "warning")) == [
        "unknown-key", "unsupported-heading", "unsupported-heading", "unsupported-phase-closing",
    ]
    reading = describe(additions)
    assert reading["spec"] == "0.1"
    assert reading["teaching"] is False
    assert all(phase["closing"] is False for phase in reading["phases"])
    assert all(lesson["homework"] is False for lesson in reading["lessons"])
    assert all(lesson["preferences"] == {} for lesson in reading["lessons"])
    assert reading["lessons"][0]["calls"] == ["pick-name"]
    loaded, _ = load(additions)
    assert "preference" not in loaded.lessons[0].calls[0]


@pytest.mark.parametrize("preference", ['""', '"Too Fast"', '"explain-back"', '"' + 'a' * 65 + '"', 'null', '42', '[pace]', '{pace: fast}'])
@pytest.mark.parametrize("version", ["0.1", "0.2"])
def test_supplied_preference_is_checked_only_in_0_2(course, version, preference):
    edit(course, "COURSE.md", 'spec: "0.1"', f'spec: "{version}"')
    edit(course, "make/LESSON.md", "    ask: What should it be called?", f"    ask: What should it be called?\n    preference: {preference}")
    assert codes(course, "error") == (["bad-field"] if version == "0.2" else [])
    assert codes(course, "warning") == (["unknown-key"] if version == "0.1" else [])


@pytest.mark.parametrize("version", ["0.1", "0.2"])
def test_closing_without_blank_line_warns_and_is_not_read(additions, version):
    edit(additions, "COURSE.md", 'spec: "0.2"', f'spec: "{version}"')
    # Markdown folds this paragraph into the final list item's first paragraph.
    edit(additions, "COURSE.md", "make/LESSON.md)\n\nYou", "make/LESSON.md)\nYou")
    assert codes(additions, "error") == []
    assert codes(additions, "warning").count("missing-phase-closing-break") == 1
    assert all(phase["closing"] is False for phase in describe(additions)["phases"])


def test_closing_uses_paragraphs_after_the_last_list_in_its_phase(additions):
    edit(additions, "COURSE.md", "You made the thing.", "A note before the last list.\n\n2. [Finish](finish/LESSON.md)\n\nYou made the thing.\n\nKeep exploring.")
    edit(additions, "COURSE.md", "### Explain it\n\n2. [Finish](finish/LESSON.md)", "### Later\n\nIntroduction only.")
    loaded, diagnostics = load(additions)
    assert diagnostics == []
    assert loaded.phases[0]["intro"] == "Begin here."
    assert loaded.phases[0]["closing"] == "You made the thing.\n\nKeep exploring."
    assert describe(additions)["phases"][1]["closing"] is False


@pytest.mark.parametrize("version", ["0.1", "0.2"])
@pytest.mark.parametrize(("rel", "heading"), [("COURSE.md", "Teaching"), ("make/LESSON.md", "Homework")])
def test_new_heading_duplicates_are_versioned(additions, version, rel, heading):
    edit(additions, "COURSE.md", 'spec: "0.2"', f'spec: "{version}"')
    edit(additions, rel, f"## {heading}", f"## {heading}\n\nAgain.\n\n## {heading}")
    assert codes(additions, "error") == (["duplicate-heading"] if version == "0.2" else [])


def test_addition_headings_inside_code_are_not_recognised(course):
    edit(course, "COURSE.md", 'spec: "0.1"', 'spec: "0.2"')
    edit(course, "COURSE.md", "## Outcome", "```md\n## Teaching\n```\n\n## Outcome")
    edit(course, "make/LESSON.md", "## Build", "```md\n## Homework\n```\n\n## Build")
    assert codes(course, "warning") == []
    reading = describe(course)
    assert reading["teaching"] is False
    assert reading["lessons"][0]["homework"] is False


def test_loading_versions_does_not_change_later_validation(additions):
    assert codes(additions, "warning") == []
    edit(additions, "COURSE.md", 'spec: "0.2"', 'spec: "0.1"')
    assert codes(additions, "warning").count("unknown-key") == 1
    edit(additions, "COURSE.md", 'spec: "0.1"', 'spec: "0.2"')
    assert codes(additions, "warning") == []
