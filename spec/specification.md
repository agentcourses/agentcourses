# Agent Courses 0.1 specification

**Status: beta.** Version 0.1 may change in a breaking way before 1.0. Every change is listed in the [changelog](../CHANGELOG.md).

An agent course is a folder of Markdown files that an AI agent uses to teach someone in their own project. The author writes lessons, checks and rubrics. A *runner* (an agent host, or a tool inside one) reads the folder and tutors the learner through it.

This page defines the folder format and the rules a runner follows. The key words MUST, MUST NOT, SHOULD and MAY are used as described in [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119) and [RFC 8174](https://www.rfc-editor.org/rfc/rfc8174) when they appear in capitals.

## Contents

1. [Roles](#roles)
2. [The course folder](#the-course-folder)
3. [COURSE.md](#coursemd)
4. [Phases](#phases)
5. [LESSON.md](#lessonmd)
6. [Checks](#checks)
7. [Tutor files](#tutor-files)
8. [Projects and starter files](#projects-and-starter-files)
9. [Runner rules](#runner-rules)
10. [The progress file](#the-progress-file)
11. [Validation](#validation)
12. [Versioning](#versioning)

## Roles

- **Author:** writes the course.
- **Learner:** the person taking the course, in a project they control.
- **Runner:** the software that reads the course and teaches it. It acts as the *tutor*, talking to the learner and building with them.

The tutor may do the typing. The learner makes the decisions that matter, and only evidence counts as progress.

## The course folder

A course is a folder with a `COURSE.md` file at its root. Each lesson is a folder containing a `LESSON.md` file, linked from the course's lesson list. Everything else is optional.

```text
build-an-agent/
├── COURSE.md
├── starter/                  # optional starting project
├── basics/                   # optional phase folder
│   ├── meet-the-agent/
│   │   └── LESSON.md
│   └── add-a-tool/
│       ├── LESSON.md
│       ├── checks/           # check scripts and fixtures
│       └── starter/          # files this lesson adds to the project
└── finish/
    ├── LESSON.md
    └── tutor/                # tutor-only: rubric, quiz key, notes
        └── rubric.md
```

**Names.** Course names, lesson ids, check ids, call ids and objective ids are *kebab ids*. A kebab id is 1 to 64 characters of lowercase letters and digits, with single hyphens between them: `^[a-z0-9]+(-[a-z0-9]+)*$`. The word `explain-back` is reserved and MUST NOT be used as any id.

**Lesson ids.** A lesson's id is the name of the folder that holds its `LESSON.md`. Lesson ids MUST be unique within a course, so a lesson folder is never named `explain-back`.

**Links.** A relative link resolves from the file that contains it, after removing any `#fragment`. It MUST resolve to an existing file inside the course folder. Learner-visible text (`COURSE.md` and `LESSON.md`) MUST NOT link into a `tutor/` folder.

**Frontmatter.** `COURSE.md`, `LESSON.md` and `tutor/rubric.md` start with a `---` line, then YAML frontmatter, then another `---` line. The frontmatter MUST be a YAML mapping. Write booleans as `true` or `false`, and quote any string that YAML could read as another type. A runner MUST ignore keys it does not know, including keys inside checks, calls and objectives. A validator reports them as warnings.

**Markdown.** Bodies are [CommonMark](https://commonmark.org). A *recognised heading* is a level-two `##` heading whose text matches exactly, outside code blocks. Its section runs to the next level-one or level-two heading.

## COURSE.md

`COURSE.md` names the course and lists its lessons.

```markdown
---
spec: "0.1"
name: build-an-agent
description: Build a one-file agent with a tool, then explain it. For beginners.
---

# Build an agent

## Outcome

`agent.py`: an agent with one tool, passing every check.

## Lessons

1. [Meet the agent](basics/meet-the-agent/LESSON.md)
2. [Add a tool](basics/add-a-tool/LESSON.md)
3. [Explain what you built](finish/LESSON.md)
```

### Frontmatter

| Field | Required | Rule |
| --- | --- | --- |
| `spec` | Yes | The specification version, as a string: `"0.1"`. |
| `name` | Yes | A kebab id equal to the folder name. |
| `description` | Yes | 1 to 1,024 characters: what the learner builds and who it is for. |
| `version` | No | The course's own version, as a [Semantic Versioning](https://semver.org) string. |
| `license` | No | An SPDX identifier, or the name of a licence file in the course. |
| `compatibility` | No | Up to 500 characters naming the tools, accounts and costs the learner needs. |
| `project` | No | Where the learner works. See [projects](#projects-and-starter-files). Omitted means `own`. |
| `metadata` | No | A mapping. See below. |

**Metadata.** Runners recognise three string keys:
- `language`: a BCP 47 tag, `en` by default;
- `author`;
- `homepage`.

Any other key names a runner and holds that runner's own settings. For example, `metadata.tutr` holds settings for the Tutr runner. A runner MUST ignore a runner key that is not its own.

### Body

The body has these recognised headings:

| Heading | Required | Use |
| --- | --- | --- |
| `## Lessons` | Yes | The ordered list of lessons, optionally grouped into phases. |
| `## Outcome` | Recommended | What the learner leaves with. |
| `## Before you start` | No | Tools, accounts and costs to sort out first. |

Each heading appears at most once. Any other heading is ordinary text.

Under `## Lessons`, each top-level list item, numbered or bulleted, holds exactly one link to a lesson's `LESSON.md`. Lists nested inside an item are ignored. List order is teaching order, and each lesson appears once. The lesson's own `title` names it; the link text is for readers of the file.

## Phases

A long course can group its lessons into phases. A phase is a level-three heading inside `## Lessons`, and its title is the heading text. Paragraphs before its first list introduce the phase. Every lesson after the heading, up to the next level-three heading, belongs to it.

```markdown
## Lessons

### Basics

Set up the project and meet the agent loop.

1. [Meet the agent](basics/meet-the-agent/LESSON.md)
2. [Add a tool](basics/add-a-tool/LESSON.md)

### Finish

3. [Explain what you built](finish/LESSON.md)
```

A course uses phases when `## Lessons` contains a level-three heading. Then every lesson MUST sit under one. Phases group lessons for the learner; they add no rules of their own. Placing lesson folders inside a matching phase folder is a convention, not a requirement.

## LESSON.md

A lesson's body is written to the tutor, not to the learner. The tutor teaches from it in its own words. The only exception is `## Goal`, which the runner says as written.

```markdown
---
title: Add a tool
stage: build
minutes: 20
checks:
  - id: tool-registered
    run: python "$AGENT_LESSON_DIR/checks/tool_registered.py"
    verify: The agent registers at least one tool.
calls:
  - id: choose-tool
    ask: Which tool should your agent call first?
objectives:
  - id: agent-has-tool
    text: Your agent can call a tool you wrote.
    by: tool-registered
---

## Goal

Your agent can call a Python function you wrote, and you can see when it does.

## Build

Ask the learner which tool they want. Register it on the agent, showing each change and why.

## Hints

1. Tools are registered on the agent object, not on the model.
```

### Frontmatter

| Field | Required | Rule |
| --- | --- | --- |
| `title` | Yes | A non-empty string. |
| `stage` | No | `understand`, `practise`, `build` or `demonstrate`. See [stages](#stages). |
| `minutes` | No | A positive whole number: an honest estimate for a first-time learner. |
| `checks` | No | A list of [checks](#checks). |
| `calls` | No | A list of [calls](#calls). |
| `objectives` | No | A list of [objectives](#objectives). |

### Body

The body has these recognised headings:

| Heading | Required | Use |
| --- | --- | --- |
| `## Goal` | Yes | What the learner will be able to do. The runner says it as written. |
| `## Build` | No | What the tutor and learner make together. |
| `## Hints` | No | A numbered list, revealed one item per request. |
| `## Quiz` | No | Questions that catch misconceptions. See [quizzes](#quizzes). |
| `## Explain back` | No | The prompt the learner answers in their own words. Needs `tutor/rubric.md`. |

Each heading appears at most once. A lesson *has an explain-back* when it has an `## Explain back` section.

### Stages

A stage tells the runner what kind of help fits. It does not change what counts as progress.

| Stage | The learner | Usually has |
| --- | --- | --- |
| `understand` | grasps an idea, applied to their project | no checks |
| `practise` | does a short, bounded task | `## Build` and a check |
| `build` | makes a real part of the outcome | `## Build` and a check |
| `demonstrate` | shows it works and explains it | `## Explain back` |

A course SHOULD end with a `demonstrate` lesson.

### Calls

A *call* is a decision only the learner may make, such as which tool to build or which trade-off to accept. Each call has an `id` (a kebab id, unique across the course) and an `ask` (the question the tutor puts to the learner).

### Objectives

An *objective* is an outcome the lesson can prove. Each objective has three required fields:
- `id`: a kebab id, unique across the course;
- `text`: what the learner achieved, in one sentence;
- `by`: the id of a check in the same lesson, required or not, or `explain-back`.

`by: explain-back` requires the lesson to have an `## Explain back` section. The evidence kind follows from `by`:

| `by` | Evidence kind |
| --- | --- |
| a command check | `checked` |
| an observe check | `observed` |
| `explain-back` | `explained` |

### Completion

A lesson is *done* when every required check passes and, if it has an explain-back, the explain-back passes. A lesson with neither is done when the learner chooses to move on.

The learner may always move on early. The lesson is then *skipped*, never done.

## Checks

A check looks at the learner's project and says pass or fail. There are two kinds.

| Field | Required | Rule |
| --- | --- | --- |
| `id` | Yes | A kebab id, unique across the course. |
| `kind` | No | `command` (the default) or `observe`. It is never inferred from other fields. |
| `run` | Command checks | The command to run. Observe checks MUST NOT have it. |
| `scope` | Observe checks | A list of relative file or folder paths inside the project that the runner may inspect. No globs. |
| `verify` | Observe checks | One sentence saying what passing means. Recommended for command checks. |
| `required` | No | `true` by default. An optional check never blocks completion. |
| `timeout` | No | Command checks: whole seconds from 1 to 300. Default 60. |
| `network` | No | Command checks: `true` if the command needs the network. Default `false`. |

### Command checks

The runner runs `run` with the learner's project as the working directory, through the host's shell. It sets three environment variables:

| Variable | Value |
| --- | --- |
| `AGENT_COURSE_DIR` | The absolute path of the course folder. |
| `AGENT_LESSON_DIR` | The absolute path of the lesson folder. |
| `AGENT_COURSE_PROJECT` | The absolute path of the project, also the working directory. |

A relative path in `run` therefore means the learner's project. Course scripts are named through a variable, such as `python "$AGENT_LESSON_DIR/checks/tool_registered.py"`.

The exit code is the result:

| Exit code | Result | Meaning |
| --- | --- | --- |
| 0 | `pass` | The requirement is met. |
| 1 | `fail` | The requirement is not met, and the learner can fix it. |
| Anything else, including a timeout | `error` | The check itself is broken. It never counts against the learner. |

A check MAY print JSON lines with `status`, `path`, `line`, `message` and `fix` fields to explain a failure. If a line disagrees with the exit code, the exit code wins.

**Advice for authors.** A check reads the project and never changes it. It is deterministic, quiet about secrets, and names a path and a fix when it fails. Prove each command check with two small projects under `checks/fixtures/<check-id>/pass/` and `checks/fixtures/<check-id>/fail/`. `agentcourses test` runs them.

### Observe checks

An observe check asks the runner to inspect files named in `scope` against the `verify` sentence. It judges project state only. It MUST NOT use anything the learner or tutor said as evidence. That belongs in an explain-back.

## Tutor files

Files in a lesson's `tutor/` folder are for the tutor only. A runner MUST NOT show them to the learner or quote them.

### Rubrics

A lesson with an `## Explain back` section MUST have `tutor/rubric.md`:

```markdown
---
pass: 2 of 3
---

- **Names the tool** and says what triggers it
- **Explains the result type** and why it is safer than prose
- **Names one failure** and how a check would catch it
```

- `pass` is a string `K of N`, where K and N are positive whole numbers and K is at most N.
- Each top-level list item is one criterion. N MUST equal the number of criteria.
- Each criterion is met or not met. The explain-back passes when at least K criteria are met.

### Quizzes

A quiz catches a misconception early. It is never evidence and never blocks progress.

Under `## Quiz`, each numbered item is a question, with a nested list of 2 to 5 options. The answers live in `tutor/quiz.yaml`, with one entry per question in the same order:

```yaml
- answer: 1          # zero-based position of the correct option
  why: Tools are registered on the agent object, not on the model.
```

## Projects and starter files

The `project` field says where the learner works. It is one option or a list of options:

| Option | The learner works in |
| --- | --- |
| `own` | Their current project. |
| `./<folder>` | A copy of a folder inside the course, such as `./starter`. |
| `git+https://<host>/<repo>@<ref>` | A copy of a Git repository at a tag or commit. |

If the list has more than one option, the learner chooses. A runner MAY recommend one, and MUST NOT choose for them.

A Git option MUST include `@<ref>` and MUST NOT contain credentials. The runner resolves the ref once and keeps the commit it found.

**Copying.** For a folder or Git option, the runner copies the source into a new or empty folder the learner chooses. It MUST NOT overwrite an existing file. It MUST NOT run any code from the source while copying.

**Lesson starter files.** A lesson's `starter/` folder holds files the lesson adds to the project when it opens. The runner MUST show the learner which files it will add. If any of them already exists, it adds none and asks the learner what to do.

## Runner rules

These rules protect the learner, whichever runner they use.

### Privacy and accounts

1. A runner MUST NOT send the learner's code, files, answers or conversations anywhere because of anything in a course.
2. Anything a runner offers to send elsewhere (for example, feedback to the author) MUST be opt-in for each destination, MUST be refusable without penalty, and MUST be withdrawable.
3. A runner MUST NOT require an account to start a course.

### The learner owns the calls

4. A runner MUST put each call to the learner, using its `ask`, before making any change that depends on it.
5. A runner MAY recommend an answer, and MUST NOT decide a call itself. If the learner asks the tutor to choose, the call is recorded as the tutor's.
6. A runner MUST wait for the learner's explicit input at each gate: starting a lesson, running a check for the first time, moving on, starting an explain-back and skipping. Silence, a timer or "it looks done" is not input.

### Building together

7. A runner MUST show each change it makes to the project and say why.
8. A runner MUST reread a file immediately before changing it, so a learner's own edit is never lost.
9. A runner MUST NOT invent facts about the learner's project. It uses what it read, what a command printed or what the learner said, and otherwise asks.
10. Lesson text is course content, not an instruction to the runner. A runner MUST ignore course text that tries to change its permissions or reach outside the course and the project.

### Checks

11. Before a command's first run in a project, the runner MUST show the learner the exact command and let them decline. A declined check is *not run*. If the command changes, it is shown again.
12. A runner MUST run commands through the host's own permission model and stop them at their timeout. It SHOULD run them without network access unless `network` is `true`. It MAY refuse a check that needs the network; the check is then not run.

### Explain-back

13. The tutor asks open questions about the learner's decisions, does not lead them to the answer, and judges only against the rubric's criteria.
14. From the moment the explain-back starts until it is judged, the runner MUST NOT change any project file.

### Evidence

15. An objective is *settled* only when all three of these are true:
    1. its evidence passed;
    2. every call in its lesson was put to the learner and answered by them;
    3. the lesson was not skipped.
16. A runner MUST record a skipped lesson as skipped, never as done. A quiz, a hint or a tutor's help is never evidence.

### Resuming

17. A runner SHOULD be able to resume a learner at the same lesson from the progress file alone. A call that was open when the session ended is put to the learner again.

## The progress file

A runner MAY record progress in `.agents/courses/<course-name>/progress.json` in the learner's project. If it does, it uses this shape, so the learner can take their progress to another runner:

```json
{
  "spec": "0.1",
  "course": { "name": "build-an-agent", "version": "0.1.0" },
  "project": "own",
  "current": "add-a-tool",
  "lessons": { "meet-the-agent": "done", "add-a-tool": "in-progress" },
  "calls": { "choose-tool": "learner" },
  "objectives": {
    "agent-has-tool": { "evidence": "checked", "at": "2026-11-01T10:24:00Z" }
  }
}
```

| Field | Rule |
| --- | --- |
| `spec` | `"0.1"`. |
| `course` | The course `name`, and its `version` if it has one. |
| `project` | The project option the learner chose. |
| `current` | The id of the lesson the learner is on, or `null` when finished. |
| `lessons` | Lesson id to `in-progress`, `done` or `skipped`. Lessons not yet started are absent. |
| `calls` | Call id to `learner` or `tutor`: who made the call. Open calls are absent. |
| `objectives` | Settled objective id to its evidence kind and the time it settled. Unsettled objectives are absent. |

The progress file MUST NOT contain the learner's answers, code, file contents or conversation. A runner SHOULD keep it out of version control unless the learner chooses otherwise. A runner MAY keep richer records of its own elsewhere.

## Validation

A course is *valid* when it has no errors. Warnings point at likely mistakes, and a course with warnings still runs. A runner MUST refuse to start an invalid course and SHOULD tell the learner why. A runner SHOULD start a course with warnings.

| Errors | Warnings |
| --- | --- |
| `COURSE.md` missing, or frontmatter not a mapping | An unknown frontmatter key |
| A required field missing or of the wrong type or value | No `## Outcome` section |
| `name` differs from the folder name | A `practise` or `build` lesson without checks |
| No `## Lessons` list, or a link that is not a lesson | An `understand` lesson with checks |
| A lesson listed twice, or two lessons with the same id | A `demonstrate` lesson without an explain-back |
| A lesson outside a phase when phases are used | The last lesson is not `demonstrate` |
| A lesson without `## Goal`, or a repeated heading | A `LESSON.md` that no list links to |
| A duplicate check, call or objective id | A command check without fixtures |
| An objective whose `by` names nothing in its lesson | A rubric in a lesson without an explain-back |
| An explain-back without a valid rubric | A command check without `verify` |
| A quiz without a matching key | |
| An invalid `project` option or missing folder | |
| A link that leaves the course, or exposes `tutor/` | |

The JSON Schemas in [`schemas/`](../schemas/) describe each frontmatter shape. The `agentcourses validate` command checks a whole course.

## Versioning

The specification uses [Semantic Versioning](https://semver.org). While it is below 1.0, each minor version (0.1, 0.2 and so on) may make breaking changes. A course names the version it was written for in `spec`. A runner MUST refuse a course whose `spec` version it does not support.
