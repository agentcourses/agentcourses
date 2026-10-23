<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner-dark.png">
    <img alt="Agent Courses. Agent skills teach your agent. Agent courses teach you, through your agent." src="docs/assets/banner-light.png" width="760">
  </picture>
</p>

<p align="center">
  <a href="https://github.com/agentcourses/agentcourses/actions/workflows/gates.yml"><img alt="make check" src="https://github.com/agentcourses/agentcourses/actions/workflows/gates.yml/badge.svg?branch=main"></a>
  <img alt="Specification: 1.0.0-rc.2" src="https://img.shields.io/badge/specification-1.0.0--rc.2-474745">
  <a href="LICENSE"><img alt="Licence: Apache-2.0" src="https://img.shields.io/badge/licence-Apache--2.0-474745"></a>
</p>

<p align="center">
  <a href="https://agentcourses.io/">Documentation</a> ·
  <a href="https://agentcourses.io/specification/">Specification</a> ·
  <a href="https://agentcourses.io/authors/quickstart/">Write a course</a> ·
  <a href="https://agentcourses.io/implementers/support/">Add course support</a>
</p>

An open format for courses that an AI agent teaches in your own project.

> [!NOTE]
> Agent Courses `1.0.0-rc.2` is a pre-release specification, open for review.
> Repository checks validate current-format courses, schemas, fixtures and controlled replay rules from a checkout.
> No runner or host is qualified yet.
> A public validator, reference library and conformance suite are future work.

## What are Agent Courses?

Agent Courses is an open, folder-based format for courses an agent can teach.
A course is a readable folder of Markdown, YAML and check programs.
The agent tutors and can type the edits; the learner owns the decisions.

```text
my-course/
├── COURSE.md          # identity, checks, optional feedback, outcome and lesson order
├── lessons/           # one Markdown file per lesson
├── tutor/             # private rubrics, quiz keys and teaching guidance
├── scripts/           # check programs and fixtures
└── assets/            # reading, images, data and starter/ skeleton files
```

## Why Agent Courses?

[Agent Skills](https://agentskills.io) give an agent new capabilities.
Agent Courses give a person new capabilities, with their own agent as the tutor.
The format makes a few commitments:

- **Your project, not a sandbox.** Lessons teach against the learner's own code.
- **You own the calls.** The tutor can explain options and recommend one. Decisions reserved for the learner wait for the learner.
- **Evidence, not assertion.** An objective settles on passing evidence and verified learner ownership of its calls. A page view or a tutor's claim never counts.
- **Local by default.** No account, telemetry or feedback service is needed. Records stay local and hold no code, conversations, call answers or answer hashes. A host may keep its own prompt history.
- **Readable and portable.** Any runner can load plain Markdown, YAML and check programs.

## How do Agent Courses work?

A **runner** is the agent, or agent extension, that teaches a course.
It loads only what each moment needs:

1. **Catalogue:** it validates the format and exposes only name, description, version, licence, compatibility and spec when authored.
2. **Start:** when the learner starts, it reads the full course page.
3. **Teach:** it loads each lesson as it begins, check files when a check runs, and tutor rubrics when judging.

Each lesson declares one stage: `understand`, `practise`, `build` or `demonstrate`.
The last lesson is the only `demonstrate` lesson.
The tutor follows one loop: goal, build together, learner calls, checks and review.
The last lesson adds an explain-back: the learner explains their work and the runner judges it.

## Where can I use Agent Courses?

The [runner showcase](https://agentcourses.io/runners/) lists planned runners and the evidence each still needs.
No runner or host is qualified against the 1.0 candidate yet.
To build one, start with [adding course support](https://agentcourses.io/implementers/support/) and the [conformance guide](https://agentcourses.io/implementers/conformance/).

## Getting started

- **[Documentation](https://agentcourses.io/)**: the overview and guides.
- **[Specification](https://agentcourses.io/specification/)**: the full format, composed from the [canonical sources](spec/format.md).
- **[Author quickstart](https://agentcourses.io/authors/quickstart/)**: write and check a first course.
- **[Schema inventory](schemas/manifest.json)**: current candidate schema identifiers, source paths and exact checksums.

## Open development

Agent Courses is developed in the open, and the 1.0 candidate is open for review.
Questions and proposals are welcome as [issues](https://github.com/agentcourses/agentcourses/issues).
Use an issue to describe a concrete authoring or runner problem and the behaviour you need.

## Licence

Everything owned in this repository is licensed under [Apache-2.0](LICENSE).
The bundled IBM Plex and Source Serif 4 fonts keep their SIL Open Font License; see `site/public/fonts/`.
