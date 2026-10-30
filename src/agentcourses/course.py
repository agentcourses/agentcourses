"""Read a course folder into a model, and report every error and warning on the way."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from urllib.parse import unquote

import yaml
from jsonschema import Draft202012Validator

from agentcourses import markdown as md

SPEC_VERSION = "0.1"
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
COURSE_HEADINGS = {"Lessons", "Outcome", "Before you start"}
LESSON_HEADINGS = {"Goal", "Build", "Hints", "Quiz", "Explain back"}
EVIDENCE = {"command": "checked", "observe": "observed"}
NOT_LESSONS = {"starter", "tutor", "fixtures", ".git", "node_modules"}


@dataclass
class Diagnostic:
    level: str  # "error" or "warning"
    code: str
    path: str
    message: str
    line: int | None = None

    def as_dict(self) -> dict:
        return {"code": self.code, "path": self.path, "line": self.line, "message": self.message}


@dataclass
class Check:
    id: str
    kind: str = "command"
    run: str | None = None
    scope: list[str] | None = None
    verify: str | None = None
    required: bool = True
    timeout: int = 60
    network: bool = False


@dataclass
class Lesson:
    id: str
    path: Path  # the lesson folder
    title: str
    stage: str | None = None
    minutes: int | None = None
    checks: list[Check] = field(default_factory=list)
    calls: list[dict] = field(default_factory=list)
    objectives: list[dict] = field(default_factory=list)
    headings: set[str] = field(default_factory=set)
    quiz: int = 0


@dataclass
class Course:
    root: Path
    name: str
    spec: str
    description: str
    version: str | None
    project: list[str]
    metadata: dict
    lessons: list[Lesson]
    phases: list[dict] | None  # [{"title", "intro", "lessons": [ids]}], or None without phases


@cache
def schema(name: str) -> dict:
    packaged = Path(__file__).parent / "schemas"
    folder = packaged if packaged.is_dir() else Path(__file__).parents[2] / "schemas"
    return json.loads((folder / f"{name}.schema.json").read_text(encoding="utf-8"))


def load(root: str | Path) -> tuple[Course | None, list[Diagnostic]]:
    """Read the course at root. The course is None when it is too broken to model."""
    return _Reader(Path(root)).read()


def describe(root: str | Path) -> dict:
    """The runner-neutral reading of a course that the conformance suite compares."""
    course, diagnostics = load(root)
    errors = sorted({d.code for d in diagnostics if d.level == "error"})
    if course is None or errors:
        return {"valid": False, "errors": errors}
    return {
        "valid": True,
        "name": course.name,
        "spec": course.spec,
        "project": course.project,
        "phases": [{"title": p["title"], "lessons": p["lessons"]} for p in course.phases or []],
        "lessons": [
            {
                "id": lesson.id,
                "title": lesson.title,
                "stage": lesson.stage,
                "checks": [vars(check) for check in lesson.checks],
                "calls": [call["id"] for call in lesson.calls],
                "objectives": [{"id": o["id"], "evidence": _evidence(lesson, o["by"])} for o in lesson.objectives],
                "explain_back": "Explain back" in lesson.headings,
                "quiz": lesson.quiz,
            }
            for lesson in course.lessons
        ],
    }


def _evidence(lesson: Lesson, by: str) -> str:
    if by == "explain-back":
        return "explained"
    return next(EVIDENCE[c.kind] for c in lesson.checks if c.id == by)


class _Reader:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.diagnostics: list[Diagnostic] = []
        self.ids: dict[str, set[str]] = {"check": set(), "call": set(), "objective": set()}

    def error(self, code, path, message, line=None):
        self.diagnostics.append(Diagnostic("error", code, self.rel(path), message, line))

    def warn(self, code, path, message, line=None):
        self.diagnostics.append(Diagnostic("warning", code, self.rel(path), message, line))

    def rel(self, path: Path) -> str:
        try:
            return Path(path).resolve().relative_to(self.root).as_posix() or "."
        except ValueError:
            return str(path)

    def read(self):
        course_file = self.root / "COURSE.md"
        if not course_file.is_file():
            self.error("missing-course-file", self.root, "the folder has no COURSE.md")
            return None, self.diagnostics
        try:
            data, body, first = md.split_frontmatter(course_file.read_text(encoding="utf-8"))
        except (md.FrontmatterError, UnicodeError) as error:
            self.error("bad-frontmatter", course_file, str(error))
            return None, self.diagnostics
        if "spec" in data and not isinstance(data["spec"], str):
            self.error("bad-field", course_file, f'spec must be a quoted string, such as spec: "{SPEC_VERSION}"')
            return None, self.diagnostics
        if "spec" in data and data["spec"] != SPEC_VERSION:
            self.error("unsupported-spec", course_file, f"spec {data['spec']!r} is not supported; this is {SPEC_VERSION!r}")
            return None, self.diagnostics
        self.check_schema("course", data, course_file)
        name = data.get("name")
        if isinstance(name, str) and name != self.root.name:
            self.error("name-mismatch", course_file, f"name {name!r} differs from the folder name {self.root.name!r}")

        blocks = md.parse(body, first)
        found, order = md.sections(blocks)
        self.check_headings(order, COURSE_HEADINGS, course_file)
        if "Outcome" not in found:
            self.warn("missing-outcome", course_file, "the course has no ## Outcome section")
        project = self.read_project(data.get("project", "own"), course_file)
        entries, phases = self.read_lesson_list(found.get("Lessons"), course_file)

        lessons, seen, ids = [], {}, {}
        for href, line in entries:
            lesson = self.read_lesson(href, line, course_file, seen)
            if lesson:
                lessons.append(lesson)
                ids[href] = lesson.id
        for phase in phases or []:
            phase["lessons"] = [ids[href] for href in phase["lessons"] if href in ids]
        self.check_links(course_file, body, skip={href for href, _ in entries})
        self.check_unlisted(seen.values(), project)
        if lessons and lessons[-1].stage != "demonstrate":
            self.warn("last-lesson-not-demonstrate", lessons[-1].path / "LESSON.md", "a course should end with a demonstrate lesson")

        course = Course(
            root=self.root,
            name=name if isinstance(name, str) else self.root.name,
            spec=SPEC_VERSION,
            description=data.get("description", ""),
            version=data.get("version"),
            project=project,
            metadata=data.get("metadata") or {},
            lessons=lessons,
            phases=phases,
        )
        return course, self.diagnostics

    def check_schema(self, name, data, path, where=""):
        validator = Draft202012Validator(schema(name))
        for problem in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
            location = ".".join(str(p) for p in problem.path)
            code = "bad-project" if location.startswith("project") else "bad-field"
            if name in ("rubric", "quiz"):
                code = f"bad-{name}"
            self.error(code, path, f"{where}{location or 'frontmatter'}: {problem.message}")
        known = schema(name).get("properties", {})
        if isinstance(data, dict):
            for key in data.keys() - known.keys():
                self.warn("unknown-key", path, f"{where}unknown key {key!r} is ignored")

    def check_headings(self, order, recognised, path):
        seen = set()
        for text, line in order:
            if text in recognised and text in seen:
                self.error("duplicate-heading", path, f"## {text} appears more than once", line)
            seen.add(text)

    def read_project(self, value, path) -> list[str]:
        options = value if isinstance(value, list) else [value]
        for option in options:
            if isinstance(option, str) and option.startswith("./"):
                folder = (self.root / option).resolve()
                if not folder.is_relative_to(self.root) or not folder.is_dir() or not any(folder.iterdir()):
                    self.error("bad-project", path, f"project folder {option!r} must be a non-empty folder inside the course")
        return [o for o in options if isinstance(o, str)]

    def read_lesson_list(self, section, path):
        if not section or not any(b.kind == "list" for b in section):
            self.error("missing-lessons", path, "COURSE.md needs a ## Lessons section with a list of lessons")
            return [], None
        phases: list[dict] = []
        entries: list[tuple[str, int]] = []
        phase = None
        for block in section:
            if block.kind == "heading" and block.level == 3:
                phase = {"title": block.text, "intro": "", "lessons": []}
                phases.append(phase)
            elif block.kind == "paragraph" and phase is not None and not phase["lessons"]:
                phase["intro"] = (phase["intro"] + "\n\n" + block.text).strip()
            elif block.kind == "list":
                for item in block.items:
                    hrefs = md.item_links(item)
                    line = item[0].line if item else block.line
                    if len(hrefs) != 1:
                        self.error("bad-lesson-link", path, "each lesson list item must hold exactly one link", line)
                        continue
                    entries.append((hrefs[0], line))
                    if phase is None and phases == [] and any(b.kind == "heading" and b.level == 3 for b in section):
                        self.error("lesson-outside-phase", path, f"{hrefs[0]} is not under a phase heading", line)
                    if phase is not None:
                        phase["lessons"].append(hrefs[0])
        return entries, phases or None

    def read_lesson(self, href, line, course_file, seen):
        target = (self.root / unquote(href.split("#")[0])).resolve()
        if not md.is_relative(href) or target.name != "LESSON.md" or not target.is_file() or not target.is_relative_to(self.root):
            self.error("bad-lesson-link", course_file, f"{href} is not a LESSON.md inside the course", line)
            return None
        folder = target.parent
        lesson_id = folder.name
        if folder in seen.values():
            self.error("duplicate-lesson", course_file, f"{href} is listed more than once", line)
            return None
        if lesson_id in seen:
            self.error("duplicate-lesson", course_file, f"two lessons have the id {lesson_id!r}", line)
            return None
        seen[lesson_id] = folder
        if not KEBAB.match(lesson_id) or len(lesson_id) > 64 or lesson_id == "explain-back":
            self.error("bad-lesson-id", folder, f"lesson folder name {lesson_id!r} is not a kebab id")
        try:
            data, body, first = md.split_frontmatter(target.read_text(encoding="utf-8"))
        except (md.FrontmatterError, UnicodeError) as error:
            self.error("bad-frontmatter", target, str(error))
            return None
        self.check_schema("lesson", data, target)
        for key in ("checks", "calls", "objectives"):
            entries = data.get(key)
            known = schema("lesson")["$defs"][key[:-1]]["properties"]
            for index, entry in enumerate(entries if isinstance(entries, list) else []):
                if isinstance(entry, dict):
                    for unknown in entry.keys() - known.keys():
                        self.warn("unknown-key", target, f"{key}[{index}]: unknown key {unknown!r} is ignored")

        found, order = md.sections(md.parse(body, first))
        self.check_headings(order, LESSON_HEADINGS, target)
        lesson = Lesson(
            id=lesson_id,
            path=folder,
            title=data.get("title") if isinstance(data.get("title"), str) else lesson_id,
            stage=data.get("stage") if isinstance(data.get("stage"), str) else None,
            minutes=data.get("minutes") if isinstance(data.get("minutes"), int) else None,
            checks=[self.read_check(c, target) for c in _dicts(data.get("checks")) if isinstance(c.get("id"), str)],
            calls=[c for c in _dicts(data.get("calls")) if isinstance(c.get("id"), str)],
            objectives=[o for o in _dicts(data.get("objectives")) if isinstance(o.get("id"), str)],
            headings={text for text, _ in order if text in LESSON_HEADINGS},
        )
        if "Goal" not in lesson.headings:
            self.error("missing-goal", target, "the lesson has no ## Goal section")
        for kind, items in (("call", lesson.calls), ("objective", lesson.objectives)):
            for item in items:
                self.claim(kind, item["id"], target)
        self.check_objectives(lesson, target)
        self.check_rubric(lesson, target)
        lesson.quiz = self.check_quiz(lesson, found.get("Quiz"), target)
        self.check_stage(lesson, target)
        self.check_links(target, body)
        return lesson

    def read_check(self, entry, path) -> Check:
        check = Check(
            id=entry["id"],
            kind=entry.get("kind", "command"),
            run=entry.get("run"),
            scope=entry.get("scope"),
            verify=entry.get("verify"),
            required=entry.get("required", True),
            timeout=entry.get("timeout", 60),
            network=entry.get("network", False),
        )
        self.claim("check", check.id, path)
        if check.kind == "command":
            if not check.verify:
                self.warn("missing-verify", path, f"check {check.id!r} has no verify sentence")
            fixtures = path.parent / "checks" / "fixtures" / check.id
            if not ((fixtures / "pass").is_dir() and (fixtures / "fail").is_dir()):
                self.warn("missing-fixtures", path, f"check {check.id!r} has no pass and fail fixtures")
        return check

    def claim(self, kind, ident, path):
        if ident in self.ids[kind]:
            self.error("duplicate-id", path, f"{kind} id {ident!r} is used more than once in the course")
        self.ids[kind].add(ident)

    def check_objectives(self, lesson, path):
        check_ids = {c.id for c in lesson.checks}
        for objective in lesson.objectives:
            by = objective.get("by")
            if by == "explain-back" and "Explain back" not in lesson.headings:
                self.error("unknown-evidence", path, f"objective {objective['id']!r} uses explain-back, but the lesson has none")
            elif by != "explain-back" and by not in check_ids:
                self.error("unknown-evidence", path, f"objective {objective['id']!r} names {by!r}, which is not a check in this lesson")

    def check_rubric(self, lesson, path):
        rubric = lesson.path / "tutor" / "rubric.md"
        if "Explain back" not in lesson.headings:
            if rubric.exists():
                self.warn("unused-rubric", rubric, "the lesson has a rubric but no ## Explain back section")
            return
        if not rubric.is_file():
            self.error("missing-rubric", path, "a lesson with ## Explain back needs tutor/rubric.md")
            return
        try:
            data, body, first = md.split_frontmatter(rubric.read_text(encoding="utf-8"))
        except (md.FrontmatterError, UnicodeError) as error:
            self.error("bad-rubric", rubric, str(error))
            return
        self.check_schema("rubric", data, rubric)
        match = re.fullmatch(r"([1-9]\d*) of ([1-9]\d*)", str(data.get("pass", "")))
        criteria = sum(len(b.items) for b in md.parse(body, first) if b.kind == "list")
        if match:
            k, n = int(match[1]), int(match[2])
            if k > n:
                self.error("bad-rubric", rubric, f"pass {k} of {n} asks for more criteria than exist")
            if n != criteria:
                self.error("bad-rubric", rubric, f"pass says {n} criteria, but the rubric lists {criteria}")

    def check_quiz(self, lesson, section, path) -> int:
        if section is None:
            return 0
        questions = [item for block in section if block.kind == "list" for item in block.items]
        options = [sum(len(b.items) for b in item if b.kind == "list") for item in questions]
        if not questions or any(not 2 <= count <= 5 for count in options):
            self.error("bad-quiz", path, "each quiz question needs a nested list of 2 to 5 options")
        key_file = lesson.path / "tutor" / "quiz.yaml"
        if not key_file.is_file():
            self.error("bad-quiz", path, "a lesson with ## Quiz needs tutor/quiz.yaml")
            return len(questions)
        try:
            key = yaml.safe_load(key_file.read_text(encoding="utf-8"))
        except (yaml.YAMLError, UnicodeError) as error:
            self.error("bad-quiz", key_file, f"tutor/quiz.yaml is not valid YAML: {error}")
            return len(questions)
        self.check_schema("quiz", key, key_file)
        if isinstance(key, list):
            if len(key) != len(questions):
                self.error("bad-quiz", key_file, f"the key has {len(key)} answers for {len(questions)} questions")
            for index, (entry, count) in enumerate(zip(key, options)):
                if isinstance(entry, dict) and isinstance(entry.get("answer"), int) and entry["answer"] >= count:
                    self.error("bad-quiz", key_file, f"answer {index + 1} points past the last option")
        return len(questions)

    def check_stage(self, lesson, path):
        if lesson.stage in ("practise", "build") and not lesson.checks:
            self.warn("stage-without-checks", path, f"a {lesson.stage} lesson usually has a check")
        if lesson.stage == "understand" and lesson.checks:
            self.warn("understand-with-checks", path, "an understand lesson usually has no checks")
        if lesson.stage == "demonstrate" and "Explain back" not in lesson.headings:
            self.warn("demonstrate-without-explain-back", path, "a demonstrate lesson usually has an ## Explain back")

    def check_links(self, path, body, skip=()):
        for href in md.links(body):
            if href in skip or not md.is_relative(href):
                continue
            target = (path.parent / unquote(href.split("#")[0])).resolve()
            if not target.is_relative_to(self.root) or not target.exists():
                self.error("bad-link", path, f"link {href} leaves the course or points at nothing")
            elif "tutor" in target.relative_to(self.root).parts:
                self.error("tutor-link", path, f"link {href} exposes tutor-only material")

    def check_unlisted(self, listed, project):
        listed = set(listed)
        projects = {(self.root / o).resolve() for o in project if o.startswith("./")}
        for found in self.root.rglob("LESSON.md"):
            parts = found.relative_to(self.root).parts
            inside_project = any(found.is_relative_to(p) for p in projects)
            if found.parent not in listed and not inside_project and not NOT_LESSONS & set(parts):
                self.warn("unlisted-lesson", found, "no lesson list links to this LESSON.md")


def _dicts(value) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []
