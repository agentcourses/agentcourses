"""The agentcourses command."""

from __future__ import annotations

import argparse
import json
import sys

from agentcourses import __version__
from agentcourses.conformance import run_suite
from agentcourses.course import describe, load
from agentcourses.fixtures import run_fixtures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agentcourses", description="Tools for Agent Courses.")
    parser.add_argument("--version", action="version", version=f"agentcourses {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="report errors and warnings in a course")
    validate.add_argument("course")
    validate.add_argument("--json", action="store_true", help="print one JSON report")

    show = commands.add_parser("describe", help="print the runner-neutral reading of a course as JSON")
    show.add_argument("course")

    test = commands.add_parser("test", help="run each command check against its pass and fail fixtures")
    test.add_argument("course")

    suite = commands.add_parser("conformance", help="check a runner's reading against the conformance cases")
    suite.add_argument("--adapter", required=True, help="command that prints a reading for a course folder")

    args = parser.parse_args(argv)
    return {"validate": _validate, "describe": _describe, "test": _test, "conformance": _conformance}[args.command](args)


def _validate(args) -> int:
    course, diagnostics = load(args.course)
    errors = [d for d in diagnostics if d.level == "error"]
    warnings = [d for d in diagnostics if d.level == "warning"]
    name = course.name if course else args.course
    if args.json:
        print(json.dumps({
            "course": name,
            "valid": not errors,
            "errors": [d.as_dict() for d in errors],
            "warnings": [d.as_dict() for d in warnings],
        }, indent=2))
    else:
        for d in diagnostics:
            where = f"{d.path}:{d.line}" if d.line else d.path
            print(f"{where}: {d.level} {d.code}: {d.message}")
        verdict = "valid" if not errors else "invalid"
        print(f"{name}: {verdict}, {len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


def _describe(args) -> int:
    print(json.dumps(describe(args.course), indent=2))
    return 0


def _test(args) -> int:
    course, diagnostics = load(args.course)
    if course is None or any(d.level == "error" for d in diagnostics):
        print("The course has errors. Run agentcourses validate first.")
        return 1
    results = run_fixtures(course)
    for r in results:
        got = "timeout" if r.actual is None else f"exit {r.actual}"
        print(f"{'ok  ' if r.ok else 'FAIL'} {r.lesson}/{r.check} {r.fixture}: expected exit {r.expected}, got {got}")
    failed = sum(not r.ok for r in results)
    print(f"{len(results)} fixtures, {failed} failed")
    return 1 if failed else 0


def _conformance(args) -> int:
    outcomes = run_suite(args.adapter)
    for o in outcomes:
        print(f"{'ok  ' if o.ok else 'FAIL'} {o.case}{': ' + o.detail if o.detail else ''}")
    failed = sum(not o.ok for o in outcomes)
    print(f"{len(outcomes)} cases, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
