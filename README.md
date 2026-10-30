<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner-dark.png">
    <img alt="Agent Courses. Agent skills teach your agent. Agent courses teach you, through your agent." src="docs/assets/banner-light.png" width="760">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/agentcourses/agentcourses/actions/workflows/check.yml"><img alt="make check" src="https://github.com/agentcourses/agentcourses/actions/workflows/check.yml/badge.svg?branch=main"></a>
  <img alt="Specification: 0.1 beta" src="https://img.shields.io/badge/specification-0.1_beta-474745">
  <a href="LICENSE"><img alt="Licence: Apache-2.0" src="https://img.shields.io/badge/licence-Apache--2.0-474745"></a>
</p>

<p align="center">
  <a href="https://agentcourses.io/">Documentation</a> ·
  <a href="spec/specification.md">Specification</a> ·
  <a href="https://agentcourses.io/quickstart/">Write a course</a> ·
  <a href="https://agentcourses.io/runners/">Build a runner</a>
</p>

Agent Courses is an open format for courses that an AI agent teaches in your own project.

A course is a folder of Markdown files. The author writes lessons, checks and rubrics. Any agent that supports the format can then tutor a learner through it: building with them, running the checks, and asking them to explain what they made. The agent may do the typing, but the learner makes the decisions, and only evidence counts as progress.

> [!NOTE]
> Agent Courses is in **beta** (0.1). The format may change before 1.0, and every change is listed in the [changelog](CHANGELOG.md).

## A complete course in three files

```text
minimal/
├── COURSE.md
└── finish/
    ├── LESSON.md
    └── tutor/
        └── rubric.md
```

`COURSE.md` names the course and lists its lessons:

```markdown
---
spec: "0.1"
name: minimal
description: Explain one everyday choice. The smallest complete course.
---

# Explain an everyday choice

## Outcome

You can explain an everyday choice and one of its consequences.

## Lessons

1. [Explain your choice](finish/LESSON.md)
```

`finish/LESSON.md` says what the learner can do by the end, and how they show it:

```markdown
---
title: Explain your choice
stage: demonstrate
---

## Goal

You can explain one everyday choice and what follows from it.

## Explain back

Ask the learner to pick an everyday decision, such as their route to work. They explain what they chose, why, and one consequence.
```

`finish/tutor/rubric.md` is for the tutor only. It says what a passing explanation covers:

```markdown
---
pass: 2 of 2
---

- **Describes the choice** and the reason for it
- **Names a consequence** of making that choice
```

Bigger courses add phases, checks that run in the learner's project, learner calls, objectives, quizzes and starter files. See the [`build-an-agent`](examples/build-an-agent) example.

## Check a course

```bash
uvx --from git+https://github.com/agentcourses/agentcourses agentcourses validate path/to/course
```

| Command | What it does |
| --- | --- |
| `agentcourses validate <course>` | Reports errors (the course cannot run) and warnings (likely mistakes). Add `--json` for a report. |
| `agentcourses test <course>` | Runs each command check against its `pass` and `fail` fixture projects. |
| `agentcourses describe <course>` | Prints the runner-neutral reading of a course as JSON. |
| `agentcourses conformance --adapter <command>` | Checks a runner's reading of a course against the [conformance cases](conformance). |

## What is in this repository

| Path | Contents |
| --- | --- |
| [`spec/specification.md`](spec/specification.md) | The specification: one page. |
| [`schemas/`](schemas) | JSON Schemas for each frontmatter shape and the progress file. |
| [`examples/`](examples) | Three valid courses, from minimal to full. |
| [`conformance/`](conformance) | Cases and a checklist for runner implementers. |
| [`src/agentcourses/`](src/agentcourses) | The `agentcourses` command. |
| [`site/`](site) | The documentation site at [agentcourses.io](https://agentcourses.io). |

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md). Run `make check` before opening a pull request.

## Licence

Everything in this repository, including the specification text, is licensed under [Apache-2.0](LICENSE).
