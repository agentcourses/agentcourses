"""Run each command check against its pass and fail fixture projects."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from agentcourses.course import Course

EXPECTED = {"pass": 0, "fail": 1}


@dataclass
class Result:
    lesson: str
    check: str
    fixture: str
    expected: int
    actual: int | None  # None when the command timed out

    @property
    def ok(self) -> bool:
        return self.actual == self.expected


def run_fixtures(course: Course) -> list[Result]:
    """Each fixture runs in a temporary copy, so a faulty check cannot change it."""
    results = []
    for lesson in course.lessons:
        for check in lesson.checks:
            folder = lesson.path / "checks" / "fixtures" / check.id
            if check.kind != "command" or not folder.is_dir():
                continue
            for fixture in sorted(p for p in folder.iterdir() if p.is_dir()):
                expected = EXPECTED.get(fixture.name.split("-", 1)[0])
                if expected is None:
                    continue
                actual = _run(course, lesson.path, check, fixture)
                results.append(Result(lesson.id, check.id, fixture.name, expected, actual))
    return results


def _run(course, lesson_dir, check, fixture) -> int | None:
    with tempfile.TemporaryDirectory(prefix="agentcourses-") as scratch:
        project = Path(scratch) / "project"
        shutil.copytree(fixture, project, symlinks=True)
        env = {
            **os.environ,
            "AGENT_COURSE_DIR": str(course.root),
            "AGENT_LESSON_DIR": str(lesson_dir),
            "AGENT_COURSE_PROJECT": str(project),
        }
        try:
            done = subprocess.run(
                check.run, shell=True, cwd=project, env=env, timeout=check.timeout, capture_output=True
            )
        except subprocess.TimeoutExpired:
            return None
        return done.returncode
