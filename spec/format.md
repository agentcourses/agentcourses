# Agent Courses 1.0: course format

This page defines what a course is: its folder, its entry file, its lessons and the project it runs in. It is the normative source for structure. Teaching behaviour, checks and evidence are in [the execution contract](execution.md). Learner feedback is in [the consent contract](consent.md). The [record contract](records.md) defines progress and receipts; [identity](identity.md) pins authored course bytes.

The current pre-release format is `1.0.0-rc.2`. The public validator, reference library and runner conformance suite are not released. No runner or host is qualified by this specification.

## Current format <a id="candidate-interpretation"></a>

A course places its identity, checks and optional feedback in `COURSE.md` frontmatter.
Lessons live in `lessons/`, private assessment in `tutor/`, programs in `scripts/` and learner resources in `assets/`.
The [baseline course](#baseline-course) shows the complete declaration shape.

### Case inputs <a id="candidate-baseline"></a>

The **candidate baseline** means the [baseline course](#baseline-course).
The **minimal candidate baseline** removes `final-check`, its script and fixtures, the lesson check reference and the check-based objective.
It retains the explain-back objective, final rubric and lessons.
It omits `checks` and `feedback`, and still requires `format`.

### Resource case inputs <a id="candidate-resource-baseline"></a>

The **candidate resource baseline** extends the [extended baseline](#baseline-course) with these additions:

- Set course `project: own` and add `starter: [plan/README.md]` to `make` frontmatter.
- Add `assets/notes.md` with UTF-8 bytes `Read the project notes.\n`.
- Add `assets/starter/plan/README.md` with UTF-8 bytes `Write your project plan here.\n`.
- Add `assets/starter/src/main.py` with UTF-8 bytes `# Begin your implementation here.\n`.

Here `\n` denotes one LF byte, not a literal backslash and letter.
The lesson order is `intro`, `make`, `finish`; central checks are `final-check` and `agent-runs`.
Both checks are referenced, `make` has no objectives or calls, and `finish` keeps its rubric and objectives.
Feedback is omitted. The starter files are a skeleton, never a finished answer.
Unless a case changes selection, use `own` and resolve only `make`'s listed starter file.

The **candidate provenance baseline** adds the [feedback object](consent.md#feedback-hooks) as central `feedback` and sets `project: [own, starter]`.
Whole-project and lesson-source assertions use separate fresh editable destinations.
The former explicitly selects `starter` and expects both starter files; the latter selects `own` and expects only `plan/README.md`.

### Format identifier <a id="format-identifier"></a>

<a id="candidate-cases"></a>
<a id="case-provenance-new-context-match"></a>
<a id="case-provenance-new-context-mismatch"></a>
<a id="case-provenance-new-context-missing"></a>
<a id="case-provenance-new-context-unknown"></a>
<a id="case-provenance-old-checks-extension"></a>
<a id="case-provenance-old-feedback-extension"></a>
<a id="case-provenance-old-format-absent"></a>
<a id="case-provenance-old-format-arbitrary"></a>
<a id="case-provenance-old-format-boolean"></a>
<a id="case-provenance-old-format-empty"></a>
<a id="case-provenance-old-format-list"></a>
<a id="case-provenance-old-format-mapping"></a>
<a id="case-provenance-old-format-new-value"></a>
<a id="case-provenance-old-format-null"></a>
<a id="case-provenance-old-format-number"></a>

`COURSE.md` MUST carry the exact YAML string `format: "1.0.0-rc.2"`, even without checks or feedback.
An absent, empty, unsupported or non-string value produces only `req-format-identifier` at `COURSE.md`.
Validate it before declaration values, check references and other dependent checks.
`format` identifies the interpretation rules. Authored `version` identifies the author's course release.
Optional `spec: "1.0"` identifies the supported major/minor contract family and defaults to `1.0`.
Neither field substitutes for `format`.

A reader selects its supported format before interpreting authored metadata.
For retained snapshots, [trusted installation provenance](records.md#candidate-provenance) establishes that context; authored values and digests cannot establish it.

### Identifier boundary cases <a id="identifier-boundaries"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-format-minimal-accepted"></a>Minimal identified course | Minimal candidate baseline | Course syntax | Accepted | Exact `format` string is present despite omitted declarations |
| <a id="case-format-minimal-missing-rejected"></a>Missing identifier | Minimal baseline without `format` | Course syntax | Rejected | Only `req-format-identifier` |
| <a id="case-format-version-independent-accepted"></a>Independent course version | Baseline with `version: "2.3.4"` and `spec: "1.0"` | Course syntax | Accepted | Course version and contract family do not change the required format |
| <a id="case-format-spec-substitute-rejected"></a>Spec cannot substitute | Minimal baseline without `format`, with `spec: "1.0"` | Course syntax | Rejected | Only `req-format-identifier` |
| <a id="case-format-normal-null-rejected"></a>Null identifier | Minimal baseline with `format: null` | Course syntax | Rejected | Only `req-format-identifier` |
| <a id="case-format-normal-number-rejected"></a>Numeric identifier | Minimal baseline with `format: 42` | Course syntax | Rejected | Only `req-format-identifier` |
| <a id="case-format-normal-boolean-rejected"></a>Boolean identifier | Minimal baseline with `format: true` | Course syntax | Rejected | Only `req-format-identifier` |
| <a id="case-format-normal-list-rejected"></a>List identifier | Minimal baseline with `format: [private-extension]` | Course syntax | Rejected | Only `req-format-identifier` |
| <a id="case-format-normal-mapping-rejected"></a>Mapping identifier | Minimal baseline with `format: {private-extension: true}` | Course syntax | Rejected | Only `req-format-identifier` |
| <a id="case-format-normal-empty-rejected"></a>Empty identifier | Minimal baseline with `format: ""` | Course syntax | Rejected | Only `req-format-identifier` |
| <a id="case-format-normal-unknown-rejected"></a>Unsupported identifier | Minimal baseline with `format: private-extension` | Course syntax | Rejected | Only `req-format-identifier` |

### Central declarations <a id="central-declarations"></a>

`checks` is an optional list of the [typed check entries](execution.md#check-declarations).
Omitted or empty means no checks.
Lessons continue to reference central check identifiers rather than redeclare them.
`feedback` is an optional [feedback object](consent.md#candidate-feedback); absence declares no collection, while explicit null is invalid.
Neither declaration grants execution permission or feedback consent.
Rubrics and quiz keys stay in `tutor/` and never move into frontmatter.

Either separate declaration file, `checks/checks.yaml` or `feedback.yaml`, makes a course invalid.
After accepting the discriminator, a reader MUST report only `req-mixed-declarations` when either or both files are present.
This applies even to empty files, identical declarations and a course with neither central field.
Reject presence before validating nested declarations or dependent references.
Ordinary unknown extension keys still follow [the existing ignore-and-warn rule](#unknown-keys).
This rule applies inside central check entries and the feedback object too.
Known nested fields retain their existing type and value constraints.

### Central declaration cases <a id="central-declaration-cases"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-central-checks-accepted"></a>Central typed checks | Candidate baseline | Course syntax | Accepted | Central `final-check` resolves from the lesson; no findings |
| <a id="case-central-omitted-accepted"></a>Declarations omitted | Minimal candidate baseline | Course syntax | Accepted | No checks or feedback collection |
| <a id="case-central-empty-accepted"></a>Empty checks and feedback | Minimal baseline with `checks: []` and `feedback: {}` | Course syntax | Accepted | Empty checks means none; the valid empty feedback object enables no hook |
| <a id="case-central-checks-null-rejected"></a>Null checks | Minimal baseline with `checks: null` | Course syntax | Rejected | Only `schema-course`; checks must be a list |
| <a id="case-central-checks-type-rejected"></a>Non-list checks | Minimal baseline with `checks: {id: final-check}` | Course syntax | Rejected | Only `schema-course`; checks must be a list |
| <a id="case-central-feedback-null-rejected"></a>Null feedback | Minimal baseline with `feedback: null` | Course syntax | Rejected | Only `schema-course`; feedback must be an object |
| <a id="case-central-feedback-type-rejected"></a>Non-object feedback | Minimal baseline with `feedback: []` | Course syntax | Rejected | Only `schema-course`; feedback must be an object |
| <a id="case-central-checks-duplicate-rejected"></a>Duplicate central check ids | Candidate baseline with a second identical complete `final-check` entry | Course syntax | Rejected | Only `req-check-declaration`; compare ids rather than whole entries |
| <a id="case-central-check-shape-rejected"></a>Invalid nested check | Candidate baseline with only `final-check.timeout` changed to 301 | Course syntax | Rejected | Only `schema-course`; the existing timeout bound is unchanged |
| <a id="case-central-extension-warning"></a>Ordinary extension | Minimal baseline with `difficulty: easy` | Advisory lint | Accepted with a warning | Only the ordinary unknown-key warning; extensions remain permitted |
| <a id="case-mixed-checks-equal-rejected"></a>Equal separate checks | Candidate baseline plus `checks/checks.yaml` containing its central list | Course syntax | Rejected | Only `req-mixed-declarations`; equality does not remove file presence |
| <a id="case-mixed-checks-empty-rejected"></a>Empty separate checks | Minimal baseline plus an empty `checks/checks.yaml` | Course syntax | Rejected | Only `req-mixed-declarations` despite omitted central checks |
| <a id="case-mixed-feedback-empty-rejected"></a>Empty separate feedback | Minimal baseline with `feedback: {}` plus empty `feedback.yaml` | Course syntax | Rejected | Only `req-mixed-declarations` |
| <a id="case-mixed-feedback-equal-rejected"></a>Equal separate feedback | Minimal baseline with `feedback: {rating: at-end}` and `feedback.yaml` containing `rating: at-end` | Course syntax | Rejected | Only `req-mixed-declarations` |
| <a id="case-mixed-both-rejected"></a>Both separate files | Minimal baseline plus both empty separate files | Course syntax | Rejected | Exactly one `req-mixed-declarations` finding |
| <a id="case-mixed-precedence-rejected"></a>Mixed before dependent checks | Candidate baseline plus empty `checks/checks.yaml`; central checks set to null | Course syntax | Rejected | Only `req-mixed-declarations`; suppress nested and unresolved-reference findings |

### Four resource roles <a id="resource-roles"></a>

Authored resources use these course-root-relative paths:

| Role | Path and base |
| --- | --- |
| Lessons | `lessons/<lesson-id>.md`; lesson filenames remain stable identifiers |
| Tutor-only assessment | `tutor/<lesson-id>.rubric.md` and existing quiz keys and guidance |
| Command programs | `scripts/<program>`; commands name course files through `AGENT_COURSE_DIR` |
| Command fixtures | `scripts/fixtures/<check-id>/{pass,fail}/`; each directory is one test project root |
| Learner resources | `assets/<resource>`, including reading, images and data |
| Starter material | `assets/starter/`; whole-project and lesson selection share this base |

Do not create empty optional folders.
Relative Markdown links remain course-root-relative, even inside lessons.
A lesson links `assets/notes.md`, never `../assets/notes.md`.
Existing containment, target-existence and tutor-only disclosure rules remain binding.
Loading an asset never permits exposing tutor material.

`project: starter` selects all files under `assets/starter/`, which must exist and contain at least one file.
A lesson's `starter: [plan/README.md]` selects `assets/starter/plan/README.md`, copied as `plan/README.md`.
Lesson paths keep the existing path syntax, existence and containment rules relative to that base.
Other explicit local sources retain `./<course-root-relative-path>` syntax and the existing non-empty-directory rules.
The selected directory remains source material for a separate editable project.
[Project choice](#project-selection) remains explicit for a list of alternatives; absence never chooses its first item.

Fixture material under `scripts/fixtures/` MUST NOT be selected as a learner project or starter source.
Selecting that directory or any descendant, including through a resolved link, fails only `req-resource-roles` when otherwise valid.
Apply existing containment and safe-source checks before any copy.
[Starter preparation](execution.md#candidate-starters) validates every target before writing and refuses collisions without overwriting.

### Resource role cases <a id="resource-role-cases"></a>

These cases use the complete [candidate resource baseline](#candidate-resource-baseline), with `own` selected unless the row changes it.
Each row starts afresh; it does not inherit another row's changes.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-resource-program-accepted"></a>Program and fixtures | Resource baseline unchanged; command uses `scripts/final_check.py` with its passing and failing fixture projects | Course syntax | Accepted | Program and fixtures use their course-root bases |
| <a id="case-resource-markdown-accepted"></a>Course-root resource link | Add `[Notes](assets/notes.md)` to the resource baseline's `make.md` body | Course syntax | Accepted | Target exists from the course root |
| <a id="case-resource-markdown-relative-rejected"></a>Lesson-relative resource link | Add `[Notes](../assets/notes.md)` to `make.md`; the asset exists at its baseline path | Course syntax | Rejected | Existing course-link containment rule; resolving from the course root escapes |
| <a id="case-resource-project-starter-accepted"></a>Whole starter source | Set `project: starter`; resolve its source | Project start | Accepted | Source is both baseline files under `assets/starter/`, with their exact bytes |
| <a id="case-resource-lesson-starter-accepted"></a>Lesson subset | Resource baseline unchanged; resolve `make`'s `starter: [plan/README.md]` | Course syntax | Accepted | Source is `assets/starter/plan/README.md`; target is plan/README.md |
| <a id="case-resource-old-base-rejected"></a>Wrong lesson starter base | Move only assets/starter/plan/README.md to assets/other/plan/README.md; keep make's selector unchanged | Course syntax | Rejected | `req-starter-files`; declared starter base has no selected file |
| <a id="case-resource-local-accepted"></a>Explicit local source | `project: ./assets/starter`; directory is non-empty and contained | Project start | Accepted | Explicit source syntax still resolves from the installed course root |
| <a id="case-resource-fixture-project-rejected"></a>Fixture selected as project | `project: ./scripts/fixtures/final-check/pass`; source is otherwise valid | Course syntax | Rejected | Only `req-resource-roles`; a check fixture is not learner source |
| <a id="case-resource-fixture-starter-rejected"></a>Fixture selected as lesson starter | Replace assets/starter with a link to scripts/fixtures/final-check/pass; change make's starter list to [agent.py]; keep project: own | Course syntax | Rejected | Only `req-resource-roles`; a contained fixture remains assessment material |
| <a id="case-resource-selection-accepted"></a>Learner selects starter | `project: [own, starter]`; learner explicitly selects starter | Project start | Accepted | Resolve assets/starter only after selection |
| <a id="case-resource-selection-missing-rejected"></a>Missing learner selection | Set project: [own, starter]; no learner answer; runner selects own | Project start | Rejected | `req-project-selection`; no default is allowed |

### Catalogue summary <a id="catalogue-summary"></a>

Catalogue output MUST contain only `name`, `description`, `version`, `license`, `compatibility` and `spec`, when present.
Return the fields actually authored; do not insert an omitted optional field into this summary.
Candidate selection is reader metadata, outside the catalogue's model context.
The reader validates the expected candidate before returning a summary.
Parsing frontmatter never requires exposing all parsed fields to the tutor or learner.
Exclude `format`, `checks`, `feedback`, `project`, `metadata`, teaching bodies and tutor files from that context.
Do not read tutor files to build the summary.

### Catalogue cases <a id="catalogue-cases"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-catalogue-summary-accepted"></a>Summary allow-list | Candidate baseline with `compatibility: Python 3.12` and `spec: "1.0"` | Runner behaviour | Accepted | Exactly name, description, version, license, compatibility and spec are returned with authored values; zero tutor-file reads |
| <a id="case-catalogue-optional-accepted"></a>Absent optional summary fields | Minimal candidate with license omitted | Runner behaviour | Accepted | Exactly name, description and version are returned; optional fields are not synthesised |
| <a id="case-catalogue-private-rejected"></a>Declarations leak into catalogue | Candidate baseline; summary also returns checks, feedback or teaching text | Runner behaviour | Rejected | `req-catalogue-summary`; only the six permitted authored fields enter catalogue context |
| <a id="case-catalogue-tutor-rejected"></a>Tutor loaded for catalogue | Candidate baseline; reader opens tutor/finish.rubric.md while building the summary | Runner behaviour | Rejected | `req-catalogue-summary`; tutor files are excluded |
| <a id="case-catalogue-identifier-rejected"></a>Unidentified catalogue input | Minimal candidate without format | Runner behaviour | Rejected | Only `req-format-identifier`; no summary is returned |

## Reading this page <a id="reading-this-page"></a>

### Required rules and advice <a id="rules-and-advice"></a>

The words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are used as defined in RFC 2119 and RFC 8174. A sentence without one of those words in capitals is a definition or an example. A paragraph under the label **Advice** is guidance only. Advice never makes a course invalid, and a validator may report it only as a warning.

Every example in this specification has exactly one outcome, chosen from three words. **Accepted**: the course or runner behaviour is valid and nothing is reported. **Accepted with a warning**: it is valid, and a validator or runner reports the warning. **Rejected**: it is invalid, and a validator reports an error, a runner refuses it, or a runner that behaves that way breaks a MUST. A runner action that is accepted can still produce a failed check, a skipped lesson or an unresolved-link warning; those are recorded results, never a sign that the runner or the course is invalid. A table that maps a case to a result, such as a check result or whether an objective settles, states that single result instead.

Each rule has one of three enforcers. A *schema* can check the shape of one file. A *Markdown validator* must read several files or the Markdown body. A *runner* acts at teaching time. [Constraints a schema cannot check](#markdown-only-constraints) lists the second group, so schema builders do not try to express it.

### How the case tables work <a id="case-tables"></a>

The examples are *cases*. A case is a row with five parts.

- **Case**: a short name and a stable anchor, which the registers link to.
- **Baseline and change**: the complete accepted course or situation, then the single change made to it. Where a case has no change, it uses the baseline unchanged.
- **Judged as**: the subject and stage of the judgement. *Course syntax* is the shape of the course files. *Source resolution* is finding a reference's files. *Project start* is what must hold before lessons begin. *Runner behaviour* is what a runner does while teaching. *Advisory lint* is advice reported as a warning. *Candidate wording* is a statement the candidate itself makes.
- **Outcome**: one of the three outcome words.
- **Deciding rule**: the derived fact that settles it, so a reader can recompute the outcome from the baseline.

Each rejected case changes one thing. If a case could fail for two reasons, the change is written so that only the intended reason remains. A warning case is never presented as a way to make a course invalid.

### The baseline course <a id="baseline-course"></a>

The baseline is `sample-course`, a current course with one command check and an explain-back. Case tables change only the fields they name.

```text
sample-course/
├── COURSE.md
├── lessons/
│   ├── intro.md
│   └── finish.md
├── scripts/
│   ├── final_check.py
│   └── fixtures/final-check/{pass,fail}/agent.py
└── tutor/
    └── finish.rubric.md
```

`COURSE.md`:

```markdown
---
format: "1.0.0-rc.2"
name: sample-course
description: Build a one-file agent and explain it. For beginners.
version: "1.0.0"
license: Apache-2.0
checks:
  - id: final-check
    run: python "$AGENT_COURSE_DIR/scripts/final_check.py"
    verify: agent.py defines an agent
    timeout: 30
    network: false
---

# Sample course

You'll build a small agent.

## Outcome

`agent.py`: an agent that passes `final-check`.

## Lessons

1. [Meet the agent](lessons/intro.md)
2. [Finish and explain](lessons/finish.md)
```

`lessons/intro.md` is the `understand` lesson:

```markdown
---
title: Meet the agent
stage: understand
calls:
  - id: choose-tool
    ask: Which tool will your agent call first?
---

## Goal

You can say what an agent tool is.
```

`lessons/finish.md` is the final `demonstrate` lesson:

```markdown
---
title: Finish and explain
stage: demonstrate
checks: [final-check]
calls:
  - id: choose-check
    ask: Which behaviour will the final check protect?
objectives:
  - id: agent-passes
    text: The agent passes the final check
    by: final-check
  - id: agent-explained
    text: The learner explains the agent
    by: explain-back
---

## Goal

You can show the agent works and say why.

## Explain back

Explain which tool your agent calls and why you chose it.
```

`COURSE.md` declares `final-check` in its `checks` list. Its program lives at `scripts/final_check.py`, with passing and failing projects under `scripts/fixtures/final-check/{pass,fail}/`. `tutor/finish.rubric.md` has `pass: 2 of 3` and three criteria.

The **extended baseline** adds a build lesson. It adds `lessons/make.md` as item 2, between the two baseline items, and one observe check in the course frontmatter `checks` list:

```markdown
---
title: Make the agent
stage: build
checks: [agent-runs]
---

## Goal

Your agent runs.

## Build

Ask the learner how to start the agent, then create `agent.py` with them.
```

```yaml
- id: agent-runs
  kind: observe
  verify: agent.py exists and defines an agent
```

The extended baseline has no objectives in `make.md`, no calls in it and no `assets/starter/`. Both baselines are accepted and report nothing.

### Licence and attribution <a id="licence"></a>

This specification, its schemas and its examples are licensed under Apache-2.0. The first proposal for the format, dated 13 October 2026, was drafted under a different licence. Its structure is kept and its attribution is preserved here. Every example course in this specification uses `license: Apache-2.0`. A course author may choose any licence for their own course.

#### Licence cases <a id="example-licence"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-licence-example-accepted"></a>Specification example is Apache-2.0 | Baseline, unchanged: `license: Apache-2.0` | Candidate wording | Accepted | Every example course here declares Apache-2.0 |
| <a id="case-licence-example-historical-rejected"></a>Specification example keeps a different licence | Baseline with `license: CC-BY-4.0`, offered as a specification example | Candidate wording | Rejected | The value is not Apache-2.0, and this is a specification example |
| <a id="case-licence-author-own-accepted"></a>An author's own course | Baseline with `license: MIT` in an author's own course, not offered as a specification example | Course syntax | Accepted | `license` is any SPDX identifier; the Apache-2.0 rule covers specification examples only |
| <a id="case-licence-attribution-removed-rejected"></a>Attribution removed | The paragraph above with the sentence about the 13 October 2026 proposal deleted | Candidate wording | Rejected | The source attribution must be kept |

### What this version leaves out <a id="scope-exclusions"></a>

Two groups of things are not in this candidate.

**Not part of 1.0 at all.** A course or runner MUST NOT claim these as part of 1.0:

- Simulated-learner evaluations, an `evals/` folder or an evals file. The name `evals/` is not reserved; a runner ignores it like any unlisted path.
- A `render` capability. Only the three capabilities in [the execution contract](execution.md#capabilities) exist.
- Certification, branching paths, translations, cohorts and selling courses.

**Part of 1.0, but not available or not defined in this candidate.** The accepted scope of version 1.0 also includes a reference library with a validator, a runner conformance suite and a stable release. This candidate defines none of them, so nobody may claim to be conformant or stable yet. The conformance classes and claim wording arrive with the conformance suite, and a stable release arrives with launch qualification. A runner may describe itself only as supporting named capabilities, as the cases show.

**Outside the candidate.** Four matters are external and no rule here depends on them: whether package names are free on the registries (⚠️ unverified; a release-time check), whether another host agrees the agents folder layout, who the second independent runner is, and who besides the owner approves specification changes. The specification's home is agentcourses.io.

#### Scope and exclusion cases <a id="example-exclusions"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-scope-supported-accepted"></a>Names only supported capabilities | A runner states "Supports `run-checks` and `judge`, Agent Courses 1.0 candidate" | Candidate wording | Accepted | Both names are among the three capabilities that exist |
| <a id="case-render-claim-rejected"></a>Claims `render` | A runner states "Supports `render`" | Candidate wording | Rejected | No `render` capability exists in 1.0 |
| <a id="case-evals-defined-claim-rejected"></a>Claims evals are defined | A document states "The `evals/evals.json` file shape is defined by Agent Courses 1.0" | Candidate wording | Rejected | Evals and their folder are not defined in 1.0 |
| <a id="case-evals-key-warning"></a>An `evals` key in frontmatter | Baseline `COURSE.md` with `evals: evals/evals.json` added | Course syntax | Accepted with a warning | The key is unknown; a runner ignores it and a validator warns. See [unknown keys](#unknown-keys) |
| <a id="case-evals-key-schema-rejected"></a>A schema rejects that key | The same course, rejected because of the `evals` key | Course syntax | Rejected | Schemas MUST allow additional properties, so rejecting the key is invalid behaviour |
| <a id="case-v1-tools-accepted"></a>Library, validator and suite stay in version one | The candidate says the library, validator and suite are part of 1.0 and are not yet available | Candidate wording | Accepted | The accepted scope includes them; availability is stated truthfully |
| <a id="case-v1-tools-excluded-rejected"></a>Library, validator and suite dropped | The candidate says the library, validator and suite are not part of 1.0 | Candidate wording | Rejected | They are in the accepted version-one scope |
| <a id="case-conforming-claim-rejected"></a>Claims conformance | A runner states "Conforming Runner, Agent Courses 1.0" | Candidate wording | Rejected | The candidate defines no conformance class and no suite exists |
| <a id="case-stable-claim-rejected"></a>Claims a stable runner | A runner states "Stable Agent Courses 1.0 runner" | Candidate wording | Rejected | A stable release waits for launch qualification |
| <a id="case-home-accepted"></a>Home | The candidate names agentcourses.io as its home | Candidate wording | Accepted | The owner chose agentcourses.io |
| <a id="case-home-superseded-rejected"></a>Superseded home | The candidate names `agentcourses.dev` as the official home | Candidate wording | Rejected | The official home is `agentcourses.io` |
| <a id="case-package-availability-accepted"></a>Package names | The candidate says name availability is left to release-time checking | Candidate wording | Accepted | No evidence of availability exists, so none is claimed |
| <a id="case-package-availability-rejected"></a>Claims availability | The candidate says the package names are free on the registries | Candidate wording | Rejected | The claim has no evidence; it stays ⚠️ unverified |
| <a id="case-host-adoption-accepted"></a>Host adoption | The candidate says host agreement on the folder layout is external work and qualifies no host | Candidate wording | Accepted | No contract rule changes with the answer |
| <a id="case-host-adoption-rejected"></a>Claims or waits for a host | The candidate says a host has agreed the layout, or holds the contract until a host endorses it | Candidate wording | Rejected | There is no evidence of agreement, and the contract is implementable without it |
| <a id="case-second-runner-accepted"></a>Second runner | The candidate defines its contract before another runner adopts it | Candidate wording | Accepted | A contract can be written before a second implementation exists |
| <a id="case-second-runner-rejected"></a>Claims a second runner | The candidate says an independent second runner exists | Candidate wording | Rejected | No evidence of one exists |
| <a id="case-governance-accepted"></a>Governance | The candidate records broader governance as a separate strategy matter | Candidate wording | Accepted | No rule here needs it |
| <a id="case-governance-rejected"></a>Invents approval rights | The candidate says named people besides the owner approve specification changes | Candidate wording | Rejected | No such rights are agreed |

#### Other exclusion cases <a id="example-exclusion-claims"></a>

Each case is one statement a course or runner makes about version 1.0. It joins the exclusion cases above.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-excl-certification-accepted"></a>Truthful about certification | A runner states "Agent Courses 1.0 defines no certification" | Candidate wording | Accepted | The statement claims nothing about certification as part of 1.0 |
| <a id="case-excl-certification-rejected"></a>Claims certification | A runner states "Supports certification, Agent Courses 1.0 candidate"; nothing else in its statement changes | Candidate wording | Rejected | Certification are not part of 1.0, and a runner MUST NOT claim them |
| <a id="case-excl-branching-accepted"></a>Truthful about branching paths | A runner states "Agent Courses 1.0 defines no branching paths" | Candidate wording | Accepted | The statement claims nothing about branching paths as part of 1.0 |
| <a id="case-excl-branching-rejected"></a>Claims branching paths | A runner states "Supports branching paths, Agent Courses 1.0 candidate"; nothing else in its statement changes | Candidate wording | Rejected | Branching paths are not part of 1.0, and a runner MUST NOT claim them |
| <a id="case-excl-translations-accepted"></a>Truthful about translations | A runner states "Agent Courses 1.0 defines no translations" | Candidate wording | Accepted | The statement claims nothing about translations as part of 1.0 |
| <a id="case-excl-translations-rejected"></a>Claims translations | A runner states "Supports translations, Agent Courses 1.0 candidate"; nothing else in its statement changes | Candidate wording | Rejected | Translations are not part of 1.0, and a runner MUST NOT claim them |
| <a id="case-excl-cohorts-accepted"></a>Truthful about cohorts | A runner states "Agent Courses 1.0 defines no cohorts" | Candidate wording | Accepted | The statement claims nothing about cohorts as part of 1.0 |
| <a id="case-excl-cohorts-rejected"></a>Claims cohorts | A runner states "Supports cohorts, Agent Courses 1.0 candidate"; nothing else in its statement changes | Candidate wording | Rejected | Cohorts are not part of 1.0, and a runner MUST NOT claim them |
| <a id="case-excl-selling-accepted"></a>Truthful about selling courses | A runner states "Agent Courses 1.0 defines no selling courses" | Candidate wording | Accepted | The statement claims nothing about selling courses as part of 1.0 |
| <a id="case-excl-selling-rejected"></a>Claims selling courses | A runner states "Supports selling courses, Agent Courses 1.0 candidate"; nothing else in its statement changes | Candidate wording | Rejected | Selling courses are not part of 1.0, and a runner MUST NOT claim them |

## Principles <a id="principles"></a>

Nine principles shape the rules. They explain intent; the rules below are what a validator and a runner enforce.

1. **A course is a folder you can read.** Plain Markdown and YAML in Git.
2. **The learner owns the calls.** The tutor builds with the learner and may type every edit. Achievement is checks passed, calls made by the learner and an explain-back judged. The tutor never makes a call the learner owns.
3. **Evidence over attendance.** Completion means evidence, not a page view.
4. **Bind the machinery, never the prose.** The format fixes structure, gates, check results and what is recorded. How the tutor teaches is the runner's craft.
5. **One source of truth.** Identity lives in frontmatter, order lives in the lesson list, and anything countable is derived.
6. **Load only what is needed.** A runner reads a catalogue entry first and loads a lesson only when it starts.
7. **Any project, by reference.** A course runs in the learner's own project, in a starter it ships, in a pinned Git repository or in a copy of a local folder.
8. **Learner-visible and tutor-only files are separate.** Keys, rubrics and misconception notes live in `tutor/`.
9. **Privacy by construction.** Code, files and tutor conversations never leave the learner's machine through anything this specification defines.

## The course folder <a id="course-shape"></a>

A course is a directory with a `COURSE.md` at its root. Everything else is optional and has one job. The directory name MUST equal the course `name`. Lesson files are named by their id, without numbers, because order is written in one place only.

### Layout <a id="folder-layout"></a>

Each optional folder has one resource role. Keep declarations in `COURSE.md`; omit optional folders that the course does not use.

```text
build-your-first-agent/
├── COURSE.md              # identity, checks, feedback, outcome and lesson order
├── lessons/               # one Markdown file per lesson, named by lesson id
├── tutor/                 # private rubrics, quiz keys and teaching guidance
│   └── explain-it.rubric.md
├── scripts/               # command check programs
│   ├── tool_is_registered.py
│   └── fixtures/tool-is-registered/{pass,fail}/
└── assets/                # reading, images, data and starter material
    └── starter/           # skeleton files copied into the learner's project
```

| Path | Seen by the learner | Loaded by the runner |
| --- | --- | --- |
| `COURSE.md` | The course page; each feedback question before it is asked | Summary fields at catalogue time; full page at start; declarations when needed |
| `lessons/` | Only the `## Goal` text, verbatim | When the lesson starts |
| `tutor/` | Never verbatim | When judging, hinting, remedying or setting the tutor's voice |
| `scripts/` | The command, before it first runs | When a check is run; fixtures are assessment inputs |
| `assets/` | On request or when a link needs it | When the question or link needs it |
| `assets/starter/` | Copied into their project | At the start, or when a lesson asks for it |

An unlisted file or folder is ignored by runners. A course MUST NOT place a finished answer in `assets/starter/`.
`tutor/` MUST NOT be linked from `COURSE.md` or from a lesson's `## Goal`.

#### Folder cases <a id="example-folder"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-folder-accepted"></a>Folder and name agree | Baseline: folder `sample-course` holds `COURSE.md` with `name: sample-course` | Course syntax | Accepted | `COURSE.md` exists and folder name equals `name` |
| <a id="case-folder-missing-course-rejected"></a>No entry file | Baseline with `COURSE.md` deleted | Course syntax | Rejected | A course is a directory with a `COURSE.md` at its root |
| <a id="case-folder-name-differs-rejected"></a>Name differs from folder | Baseline with `name: other-course` and the folder still `sample-course` | Course syntax | Rejected | `other-course` is not equal to `sample-course` |

### Names and ids <a id="names-and-ids"></a>

A *kebab id* is 1 to 64 characters, lowercase letters and digits only, with single hyphens between runs and no leading or trailing hyphen. In regular-expression form: `^[a-z0-9]+(-[a-z0-9]+)*$` and length at most 64. Course names, lesson ids, check ids, call ids and objective ids are all kebab ids. The word `explain-back` is reserved: it selects the explain-back as evidence in an objective, so no check id, lesson id, call id or objective id may be `explain-back`.

A lesson's id is its file name without `.md` and nothing else. A lesson file has no `id` key. A lesson `id` key is an unknown key, warned about and ignored, so it cannot change the id. A file that names a lesson by id, such as a rubric or quiz key, MUST use that file-name id.

#### Id cases <a id="example-ids"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-id-valid-accepted"></a>Valid ids | Baseline, with the folder and `name` renamed together, in turn, to `add-a-tool`, `a` and `a` followed by 63 `b` characters (64 in all) | Course syntax | Accepted | Folder name equals `name` in each, and each matches the pattern with length 1 to 64 |
| <a id="case-id-empty-rejected"></a>Empty | Baseline with the call `choose-tool` given `id: ""`; folder and `name` unchanged | Course syntax | Rejected | Length is 0, below 1. A call id is used here because no folder can be named by the empty string |
| <a id="case-id-uppercase-rejected"></a>Uppercase | Baseline with the folder and `name` both renamed `Add-A-Tool` | Course syntax | Rejected | The two names agree, so only the pattern fails: `A` is not a lowercase letter or digit |
| <a id="case-id-underscore-rejected"></a>Underscore | Baseline with the folder and `name` both renamed `add_a_tool` | Course syntax | Rejected | The two names agree; `_` is not a letter, digit or hyphen |
| <a id="case-id-doubled-hyphen-rejected"></a>Doubled hyphen | Baseline with the folder and `name` both renamed `add--tool` | Course syntax | Rejected | The two names agree; hyphens must be single between runs |
| <a id="case-id-edge-hyphen-rejected"></a>Leading or trailing hyphen | Baseline with the folder and `name` both renamed `-add` and, separately, `add-` | Course syntax | Rejected | The two names agree; neither end may be a hyphen |
| <a id="case-id-too-long-rejected"></a>65 characters | Baseline with the folder and `name` both renamed to `a` followed by 64 `b` characters | Course syntax | Rejected | The two names agree; length 65 exceeds 64 |
| <a id="case-id-reserved-check-rejected"></a>Reserved word as a command check id | Baseline the course `checks` list gains a complete command check `id: explain-back` with `run`, `verify`, `timeout` and `network`, plus `scripts/fixtures/explain-back/pass/agent.py` and `fail/agent.py` that give exit 0 and exit 1; no lesson lists it | Course syntax | Rejected | Declaration and fixtures are otherwise valid, so only the id decides: `explain-back` is reserved for every id kind |
| <a id="case-id-reserved-observe-rejected"></a>Reserved word as an observe check id | Baseline the course `checks` list gains `id: explain-back` with `kind: observe` and `verify`; no lesson lists it | Course syntax | Rejected | The reservation applies to observe checks as well |
| <a id="case-id-reserved-lesson-rejected"></a>Reserved word as a lesson id | Extended baseline with `lessons/make.md` renamed `lessons/explain-back.md` and its list link updated | Course syntax | Rejected | A lesson id is its file name, and that is reserved |
| <a id="case-id-reserved-call-rejected"></a>Reserved word as a call id | Baseline with the call `choose-tool` renamed `explain-back` | Course syntax | Rejected | The reservation applies to call ids |
| <a id="case-id-reserved-objective-rejected"></a>Reserved word as an objective id | Baseline with the objective `agent-explained` renamed `explain-back`; its `by` stays `explain-back` | Course syntax | Rejected | The reservation applies to objective ids |
| <a id="case-id-reserved-selector-accepted"></a>Reserved word only as a selector | Baseline, unchanged: objective `agent-explained` has `by: explain-back` and the command check is `final-check` | Course syntax | Accepted | `by: explain-back` selects the explain-back; no id uses the word |
| <a id="case-id-lesson-frontmatter-id-warning"></a>A claimed lesson id in frontmatter | Baseline `intro.md` frontmatter gains `id: setup` | Course syntax | Accepted with a warning | `id` is an unknown key and is ignored; the lesson id stays `intro` |
| <a id="case-id-rubric-claim-rejected"></a>A file that names a different lesson id | Baseline with the rubric renamed `tutor/wrap-up.rubric.md` | Course syntax | Rejected | The final lesson's id is `finish`, so `tutor/finish.rubric.md` is missing |

## COURSE.md <a id="course-file"></a>

`COURSE.md` has YAML frontmatter that identifies the course, then a Markdown page.
It begins with a line of three hyphens and ends the frontmatter with another such line. Frontmatter MUST be a YAML mapping.

### Frontmatter fields <a id="course-frontmatter"></a>

| Field | Required | Rule |
| --- | --- | --- |
| `format` | Yes | Exactly the YAML string `"1.0.0-rc.2"`. See [format identification](#format-identifier). |
| `checks` | No | A list of [typed checks](execution.md#check-declarations); omitted or empty means none. |
| `feedback` | No | A [feedback object](consent.md#feedback-hooks); omitted means no collection. |
| `name` | Yes | A kebab id equal to the folder name. Stable across versions. |
| `description` | Yes | A string of 1 to 1,024 characters. What the learner builds and who it is for. |
| `version` | Yes | A string holding a Semantic Versioning 2.0.0 version, such as `1.2.0` or `2.0.0-beta.1`. Build metadata after `+` is not allowed. It MUST be a YAML string, so quote it. |
| `license` | No | An SPDX identifier, or the name of a licence file in the course folder. |
| `compatibility` | No | A string of 1 to 500 characters naming the tools, hosts, accounts and costs the learner needs. |
| `project` | No | See [the project field](#project-field). Omitted means `own`. |
| `spec` | No | A string `major.minor`, such as `1.0`. Omitted means `1.0`. |
| `metadata` | No | A mapping from strings to strings. |

A runner MUST refuse a course whose `spec` major version it does not support. A runner that meets a later minor version of a supported major SHOULD run the course, ignore what it does not know and tell the learner. Runners recognise four metadata keys: `language` (a BCP 47 tag, default `en`), `author`, `homepage` and `handle`. A runner MUST NOT invent a homepage or handle that the metadata does not hold.

#### Frontmatter cases <a id="example-frontmatter"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-frontmatter-boundaries-accepted"></a>Boundaries and optional fields | Baseline with a 1-character `description`, then separately a 1,024-character one; `compatibility` of 1 and 500 characters; `license: MIT`; `project: own`; `spec: "1.0"`; `metadata: {language: en, author: Ana}` | Course syntax | Accepted | Every value is inside its declared length or type, and omitted fields take their defaults |
| <a id="case-frontmatter-name-missing-rejected"></a>`name` missing | Baseline without `name` | Course syntax | Rejected | `name` is required |
| <a id="case-frontmatter-description-missing-rejected"></a>`description` missing | Baseline without `description` | Course syntax | Rejected | `description` is required |
| <a id="case-frontmatter-version-missing-rejected"></a>`version` missing | Baseline without `version` | Course syntax | Rejected | `version` is required |
| <a id="case-frontmatter-description-empty-rejected"></a>Empty description | `description: ""` | Course syntax | Rejected | Length 0 is below 1 |
| <a id="case-frontmatter-description-long-rejected"></a>Over-long description | A 1,025-character `description` | Course syntax | Rejected | Length 1,025 exceeds 1,024 |
| <a id="case-frontmatter-description-type-rejected"></a>Wrong type | `description: 12` | Course syntax | Rejected | A known key with a non-string value |
| <a id="case-frontmatter-compatibility-rejected"></a>Compatibility limits | `compatibility: ""` and, separately, a 501-character string | Course syntax | Rejected | Length must be 1 to 500 |
| <a id="case-frontmatter-version-number-rejected"></a>Numeric version | `version: 1.2`, which YAML reads as a number | Course syntax | Rejected | `version` must be a string holding three parts |
| <a id="case-frontmatter-version-build-rejected"></a>Build metadata in a version | `version: "1.0.0+b1"` | Course syntax | Rejected | Build metadata after `+` is not allowed |
| <a id="case-frontmatter-version-string-accepted"></a>Quoted version | `version: "1.2.0"` | Course syntax | Accepted | A string with three parts |
| <a id="case-frontmatter-metadata-rejected"></a>Metadata that is not a string mapping | `metadata: [author, Ana]` and, separately, `metadata: {n: 1}` | Course syntax | Rejected | Metadata must map strings to strings |
| <a id="case-frontmatter-spec-major-rejected"></a>Unsupported major | `spec: "2.0"` on a runner that supports major 1 | Runner behaviour | Rejected | The runner MUST refuse an unsupported major version; the value is a string |
| <a id="case-frontmatter-spec-minor-accepted"></a>Later supported minor | `spec: "1.1"` and an extra optional key `difficulty: easy`, on a runner that supports 1.0 | Runner behaviour | Accepted with a warning | The major is supported, so the runner runs the course, ignores the key and tells the learner |
| <a id="case-frontmatter-spec-minor-refused"></a>Refusing a later minor | The same course, refused only because of the optional key | Runner behaviour | Rejected | A later minor of a supported major SHOULD run; refusing for an optional key is wrong |
| <a id="case-frontmatter-invalid-page-rejected"></a>Frontmatter that is not a mapping | `COURSE.md` whose frontmatter is the list `- sample-course` | Course syntax | Rejected | Frontmatter MUST be a YAML mapping |

### Unknown keys <a id="unknown-keys"></a>

A runner MUST ignore a key it does not know in `COURSE.md` frontmatter, lesson frontmatter, a check entry, a call entry, an objective entry and the `feedback` object. An authoring validator SHOULD report such a key as a warning, never an error, so a typo is caught and a course written for a later 1.x minor still runs. Schemas for these files MUST allow additional properties. A key that is known but has the wrong type or value is an error. Extensions belong in `metadata`.

#### Unknown-key cases <a id="example-unknown-keys"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-unknown-key-course-warning"></a>Unknown course key | Baseline with `difficulty: easy` added to `COURSE.md` | Course syntax | Accepted with a warning | The schema allows it, the runner ignores it and the author check warns |
| <a id="case-unknown-key-lesson-warning"></a>Unknown lesson key | Baseline `finish.md` with `pace: slow` added | Course syntax | Accepted with a warning | Same rule for lesson frontmatter |
| <a id="case-unknown-key-check-warning"></a>Unknown check key | Baseline `final-check` entry with `owner: team-a` added | Course syntax | Accepted with a warning | Same rule for a check entry |
| <a id="case-unknown-key-call-warning"></a>Unknown call key | Baseline call `choose-tool` with `hint: be brief` added | Course syntax | Accepted with a warning | Same rule for a call entry |
| <a id="case-unknown-key-objective-warning"></a>Unknown objective key | Baseline objective `agent-passes` with `weight: 2` added | Course syntax | Accepted with a warning | Same rule for an objective entry |
| <a id="case-unknown-key-rejected"></a>Rejecting an unknown key | The `difficulty: easy` course, rejected by a schema or refused by a runner because of that key | Course syntax | Rejected | Schemas MUST allow additional properties and runners MUST ignore unknown keys |
| <a id="case-unknown-key-known-wrong-type-rejected"></a>A known key with the wrong type | Baseline with `description: 12` | Course syntax | Rejected | Known-key type errors stay errors; only unknown keys warn |

### The page <a id="course-page"></a>

The body is Markdown. Headings are matched only at level two, with exactly the text shown, outside fenced code blocks. Each recognised heading appears at most once.

| Heading | Required | Use |
| --- | --- | --- |
| `## Lessons` | Yes | The ordered lesson list |
| `## Outcome` | Yes | The artefact the learner leaves with, said once |
| `## Before you start` | No | Tools, accounts and costs, shown before the first lesson |
| `## Project` | No | A sentence or two on where the learner works |

Any other heading is ordinary text. A course with a missing required heading, or a recognised heading twice, is invalid.

#### Page heading cases <a id="example-course-invalid"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-page-headings-accepted"></a>One of each | Baseline `COURSE.md`, unchanged | Course syntax | Accepted | Exactly one level-two `## Lessons` and one `## Outcome`, both outside fences |
| <a id="case-page-lessons-missing-rejected"></a>No Lessons | Baseline with the `## Lessons` heading and its list deleted | Course syntax | Rejected | `## Lessons` is required; the unlisted lesson files the deletion leaves are a consequence of the same change |
| <a id="case-page-outcome-missing-rejected"></a>No Outcome | Baseline with `## Outcome` and its text deleted | Course syntax | Rejected | `## Outcome` is required |
| <a id="case-page-lessons-duplicate-rejected"></a>Two Lessons | Baseline with a second `## Lessons` heading added at the end, with no list under it | Course syntax | Rejected | A recognised heading appears at most once; the empty second section is a consequence of the same change |
| <a id="case-page-outcome-duplicate-rejected"></a>Two Outcomes | Baseline with a second `## Outcome` heading added | Course syntax | Rejected | A recognised heading appears at most once |
| <a id="case-page-fenced-heading-rejected"></a>Heading inside a fence | Baseline with the real `## Lessons` heading and list moved inside a fenced code block | Course syntax | Rejected | Headings are matched outside fenced code blocks, so no `## Lessons` remains; the missing list is a consequence of the same change |
| <a id="case-page-level-three-rejected"></a>Wrong level | Baseline with `## Lessons` changed to `### Lessons` | Course syntax | Rejected | Headings are matched only at level two |
| <a id="case-page-other-heading-accepted"></a>Another heading | Baseline with `## Notes` added | Course syntax | Accepted | Any other heading is ordinary text |

### The lesson list <a id="lesson-list"></a>

The `## Lessons` section contains exactly one ordered list. Each item contains exactly one link, and the link target is `lessons/<id>.md` for a lesson file that exists. The list order is the course order and is written nowhere else. A lesson file MUST appear in the list once. A lesson file that is not listed, a listed file that does not exist, a link listed twice and a link outside `lessons/` are all invalid. A course has at least one lesson.

#### Example course page <a id="example-course-valid"></a>

A course-page fragment with a richer `project` list. Its starter choice assumes a non-empty `assets/starter/` folder. The lessons it links are not shown here; stages are shown in [the baseline course](#baseline-course) and in the [stage cases](#example-stages).

```markdown
---
format: "1.0.0-rc.2"
name: build-your-first-agent
description: Build a typed agent with one tool and structured output, in your
  own repository. For Python developers new to agent frameworks.
version: "1.2.0"
license: Apache-2.0
compatibility: Python 3.12 or later and uv. Tested in Claude Code and Codex.
project: [own, starter]
---

# Build your first agent

You'll build an agent that answers with a typed object, then explain how it works.

## Outcome

`agent.py`: a typed agent with one tool, passing every check.

## Lessons

1. [Install and run an agent](lessons/install.md)
2. [Add a tool your agent can call](lessons/add-a-tool.md)
3. [Explain what you built](lessons/explain-it.md)
```

The learner picks `own` or `starter` before lesson one.

#### Lesson list cases <a id="example-lesson-list"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-list-accepted"></a>Exact inventory | Baseline: the list names `intro.md` and `finish.md` once each, and exactly those two files are in `lessons/` | Course syntax | Accepted | The set of listed files equals the set of files, each once |
| <a id="case-list-duplicate-rejected"></a>Duplicate link | Baseline with a third item linking `lessons/intro.md` again | Course syntax | Rejected | `intro.md` is listed twice |
| <a id="case-list-missing-file-rejected"></a>Missing file | Baseline with a third item linking `lessons/extra.md`, which does not exist | Course syntax | Rejected | A listed file must exist |
| <a id="case-list-unlisted-rejected"></a>Unlisted file | Baseline plus a valid `lessons/extra.md` that no item links | Course syntax | Rejected | A lesson file must appear in the list |
| <a id="case-list-second-list-rejected"></a>Second ordered list | Baseline with a second ordered list added under `## Lessons`, after the first list and a paragraph; its one item links `lessons/intro.md` | Course syntax | Rejected | The section contains exactly one ordered list. That item also repeats `intro.md`; any item would break a per-item rule, so the list-count rule is the one under test |
| <a id="case-list-outside-target-rejected"></a>Target outside lessons | Baseline with a third item linking `assets/notes.md`, which exists | Course syntax | Rejected | The link target must be `lessons/<id>.md` |
| <a id="case-list-empty-rejected"></a>No lessons | Baseline with the ordered list removed from `## Lessons` | Course syntax | Rejected | A course has at least one lesson |

## Lessons <a id="lessons"></a>

Each lesson is one Markdown file in `lessons/`. Its file name without `.md` is its id, a kebab id that is unique in the course and stable across versions. Records point at ids, never positions, so reordering or inserting a lesson never breaks a learner's history.

### Stages <a id="stages"></a>

A lesson declares one of four stages. Stages tell a runner what kind of help fits.

| Stage | The learner | Lesson must have | Completes when |
| --- | --- | --- | --- |
| `understand` | Grasps an idea applied to their own project | `## Goal`; no checks | The learner asks to move on |
| `practise` | Does a short, bounded task | `## Goal`, `## Build`, at least one check | Every required check passes, or the learner chooses to move on |
| `build` | Makes a real part of the outcome | `## Goal`, `## Build`, at least one check | Every required check passes, or the learner chooses to move on |
| `demonstrate` | Proves it: checks pass and the learner explains it | `## Goal`, `## Explain back`, a rubric in `tutor/` | Required checks pass and the explain-back has been judged |

Moving on without passing is always allowed and is always recorded as skipped, never as passed. The last lesson in the list MUST have stage `demonstrate`, and it is the only `demonstrate` lesson. A course whose last lesson has another stage, or that has two `demonstrate` lessons, is invalid.

#### Stage cases <a id="example-stages"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-stages-names-accepted"></a>All four stage names | Baseline `intro.md` is `understand` and `finish.md` is `demonstrate`; the extended baseline's `make.md` is `build`, and, tried separately, `stage: practise` with the same content | Course syntax | Accepted | Each value is one of the four names |
| <a id="case-stage-name-rejected"></a>Not a stage name | Extended baseline with `make.md` set to `stage: practice` | Course syntax | Rejected | `practice` is not one of the four names |
| <a id="case-final-stage-accepted"></a>Final demonstrate | Baseline: list order is `intro.md`, `finish.md`; their stages are `understand` and `demonstrate`; the rubric is `tutor/finish.rubric.md` with `pass: 2 of 3` and three criteria | Course syntax | Accepted | The last listed lesson is `demonstrate`, and the count of `demonstrate` lessons is 1 |
| <a id="case-final-stage-not-demonstrate-rejected"></a>Final lesson is not demonstrate | Baseline with `finish.md` changed to `stage: build`, `checks: [final-check]`, its `## Explain back` replaced by `## Build`, its `by: explain-back` objective removed and the rubric removed | Course syntax | Rejected | The last listed lesson has stage `build`, not `demonstrate` |
| <a id="case-final-stage-two-demonstrate-rejected"></a>Two demonstrate lessons | Baseline with `intro.md` changed to `stage: demonstrate`, a `## Explain back` heading added and `tutor/intro.rubric.md` (`pass: 1 of 1`, one criterion) added; `finish.md` unchanged | Course syntax | Rejected | The count of `demonstrate` lessons is 2, and only the last may be `demonstrate` |
| <a id="case-final-stage-demonstrate-first-rejected"></a>Demonstrate not last | Extended baseline with `intro.md` and `finish.md` swapped in list order | Course syntax | Rejected | The last listed lesson is `understand` and the demonstrate lesson comes first |

### Lesson frontmatter <a id="lesson-frontmatter"></a>

| Field | Required | Rule |
| --- | --- | --- |
| `title` | Yes | A non-empty string. |
| `stage` | Yes | One of `understand`, `practise`, `build`, `demonstrate`. |
| `checks` | `practise` and `build`; optional in `demonstrate`; not allowed in `understand` | A list. In `practise` and `build` it has at least one item. In `understand` it MUST be omitted or empty. Each item is a check id from the course frontmatter `checks` list, or a mapping `{id: <check id>, required: false}`. An item is required unless it says `required: false`. No id appears twice. |
| `minutes` | No | A positive integer: an honest estimate for a first-time learner. |
| `calls` | No | A list of calls. See [calls](#calls). Omitted means none. |
| `objectives` | No | A list of objectives. See [objectives](#objectives). Omitted means none. |
| `starter` | No | A list of paths under `assets/starter/`. See [starter files](#starter-files). |

A `demonstrate` lesson MAY list checks; its required checks must pass before its explain-back is judged. An `understand` lesson declares no checks. Because an objective needs a check or an explain-back, an `understand` lesson can declare no objective, and it settles nothing. It may still declare calls.

#### Understand-stage cases <a id="example-understand"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-understand-accepted"></a>Understand with a call | Baseline `intro.md`: `stage: understand`, one declared call, no checks, no objectives; the learner answers the call and asks to move on | Course syntax, then runner behaviour | Accepted | No checks and no objectives are declared; the lesson completes when the learner asks to move on and settles nothing |
| <a id="case-understand-check-rejected"></a>Understand with a check | Baseline `intro.md` with `checks: [final-check]` added | Course syntax | Rejected | An understand lesson MUST omit checks |
| <a id="case-understand-objective-rejected"></a>Understand with an objective | Baseline `intro.md` with `objectives: [{id: intro-done, text: Knows tools, by: final-check}]` added | Course syntax | Rejected | An understand lesson declares no checks, so no check can support an objective |
| <a id="case-understand-settles-rejected"></a>Runner invents settlement | The accepted trace above, with the runner recording an objective `intro-done` as settled when the learner moves on | Runner behaviour | Rejected | Only a declared objective settles, and `intro.md` declares none |

#### Example lessons <a id="example-lesson-valid"></a>

An accepted `practise` lesson with a call, an objective and a hint.

```markdown
---
title: Add a tool your agent can call
stage: practise
minutes: 12
checks: [tool-is-registered, {id: tool-has-docstring, required: false}]
calls:
  - id: tool-name
    ask: What should the tool be called?
objectives:
  - id: register-a-tool
    text: The agent has a registered tool
    by: tool-is-registered
---

## Goal

Your agent can call a Python function you wrote, and you can see when it does.

## Build

Ask the learner to name the tool. Then register it on the agent and show the
change and why. Reread agent.py before every edit.

## Hints

1. Tools are registered on the agent object, not on the model.
```

Outcome: accepted.

#### Invalid lessons <a id="example-lesson-invalid"></a>

The cases that make a lesson invalid are in these rows. Each is a separate case with its own baseline.

| Violation | Case |
| --- | --- |
| Not a stage name | [Not a stage name](#case-stage-name-rejected) |
| `build` lesson with no checks | [Required checks missing](#case-lesson-checks-missing-rejected) |
| `## Task` instead of `## Build` | [Task replaces Build](#case-headings-task-for-build-rejected) |
| Two `## Goal` headings | [Goal twice](#case-headings-goal-duplicate-rejected) |
| `## Explain back` in a `build` lesson | [Explain back in a build lesson](#case-headings-explain-back-in-build-rejected) |
| `minutes: 0` | [Zero minutes](#case-lesson-minutes-zero-rejected) |
| Repeated check id | [Repeated check id](#case-lesson-check-repeated-rejected) |
| `understand` lesson with checks | [Understand with a check](#case-understand-check-rejected) |
| `understand` lesson with an objective | [Understand with an objective](#case-understand-objective-rejected) |
| Final lesson not `demonstrate` | [Final lesson is not demonstrate](#case-final-stage-not-demonstrate-rejected) |

#### Lesson field cases <a id="example-lesson-fields"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-lesson-fields-accepted"></a>Valid fields | Extended baseline `make.md` with `minutes: 12` added, `checks: [agent-runs]` kept, and no `calls` or `objectives` | Course syntax | Accepted | Minutes is a positive integer, the check id exists in the course `checks` list, and optional `calls` and `objectives` may be absent |
| <a id="case-lesson-optional-check-accepted"></a>Optional check mapping | Extended baseline `make.md` with `checks: [{id: agent-runs, required: false}]` | Course syntax | Accepted | A mapping with `required: false` is a valid item |
| <a id="case-lesson-minutes-zero-rejected"></a>Zero minutes | Extended baseline `make.md` with `minutes: 0` | Course syntax | Rejected | `minutes` must be positive |
| <a id="case-lesson-check-repeated-rejected"></a>Repeated check id | Extended baseline `make.md` with `checks: [agent-runs, agent-runs]` | Course syntax | Rejected | No id appears twice |
| <a id="case-lesson-check-unknown-rejected"></a>Unknown check id | Extended baseline `make.md` with `checks: [no-such-check]` | Course syntax | Rejected | Every id a lesson lists MUST exist in the course frontmatter `checks` list |
| <a id="case-lesson-field-type-rejected"></a>Wrong field types | Extended baseline `make.md` with `minutes: "12"`, separately `minutes: 1.5`, and separately `calls: choose-tool` | Course syntax | Rejected | `minutes` must be a whole number and `calls` must be a list |
| <a id="case-lesson-checks-missing-rejected"></a>Required checks missing | Extended baseline `make.md` with its `checks` line deleted | Course syntax | Rejected | A `build` lesson has at least one check |
| <a id="case-lesson-title-rejected"></a>No title | Extended baseline `make.md` without `title` | Course syntax | Rejected | `title` is required |

### Lesson headings <a id="lesson-headings"></a>

The body is Markdown written to the tutor. A runner looks for five level-two headings, with exactly these texts, outside fenced code blocks, and treats every other heading as teaching material.

| Heading | Cardinality | Use |
| --- | --- | --- |
| `## Goal` | Exactly once in every lesson | What the learner will be able to do. The runner says it as written. |
| `## Build` | Exactly once in `practise` and `build`; at most once in the other stages | What the tutor and learner make together. Instructions to the tutor. |
| `## Hints` | At most once | A numbered list, revealed one item per request |
| `## Quiz` | At most once | Misconception questions, asked one at a time |
| `## Explain back` | Exactly once in `demonstrate`; never in other stages | The prompt the learner answers in their own words |

A heading repeated, a required heading missing and `## Explain back` outside the final lesson are invalid. A heading spelled `## Task` is ordinary text: it does not satisfy the `## Build` requirement. A runner MUST say the `## Goal` text to the learner as written and MUST NOT say any other lesson section as written; it teaches from them in its own words.

#### Lesson heading cases <a id="example-lesson-headings"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-headings-accepted"></a>Required headings once | Extended baseline: `make.md` (build) has `## Goal` once and `## Build` once; `finish.md` (demonstrate) has `## Goal` once, `## Explain back` once and no `## Build`; `intro.md` has `## Goal` and no `## Build` | Course syntax | Accepted | Cardinalities match the table for each stage |
| <a id="case-headings-practise-build-accepted"></a>Practise has Build | Extended baseline with `make.md` as `stage: practise` | Course syntax | Accepted | `practise` requires `## Build` once, which is present |
| <a id="case-headings-goal-missing-rejected"></a>Goal missing | Extended baseline `make.md` without `## Goal` | Course syntax | Rejected | `## Goal` is required in every lesson |
| <a id="case-headings-goal-duplicate-rejected"></a>Goal twice | Extended baseline `make.md` with a second `## Goal` | Course syntax | Rejected | `## Goal` appears exactly once |
| <a id="case-headings-build-missing-rejected"></a>Build missing | Extended baseline `make.md` without `## Build` | Course syntax | Rejected | `build` requires `## Build` |
| <a id="case-headings-build-duplicate-rejected"></a>Build twice | Extended baseline `make.md` with a second `## Build` | Course syntax | Rejected | `## Build` appears exactly once in `build` |
| <a id="case-headings-task-for-build-rejected"></a>Task replaces Build | Extended baseline `make.md` as `stage: practise` with `## Build` renamed `## Task` | Course syntax | Rejected | `## Task` is ordinary text, so `## Build` is missing |
| <a id="case-headings-explain-back-in-build-rejected"></a>Explain back in a build lesson | Extended baseline `make.md` with `## Explain back` added | Course syntax | Rejected | `## Explain back` is never in other stages than `demonstrate` |
| <a id="case-headings-explain-back-missing-rejected"></a>Explain back missing | Baseline `finish.md` without `## Explain back` | Course syntax | Rejected | `demonstrate` requires `## Explain back` exactly once |

#### Tutor-addressed lesson cases <a id="example-tutor-addressed"></a>

These cases apply the rule that lessons address the tutor. The runner rules are in [Building together](execution.md#build-duties).

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-tutor-addressed-accepted"></a>Goal verbatim, Build adapted | Extended baseline; the runner says "Your agent runs." exactly, then teaches the `## Build` text in its own words; the practise form of `make.md` contains `## Build` | Runner behaviour | Accepted | Only `## Goal` is said as written; `## Build` is guidance to the tutor |
| <a id="case-tutor-addressed-build-verbatim-rejected"></a>Build recited | Same lesson; the runner reads the `## Build` text aloud to the learner word for word | Runner behaviour | Rejected | A runner MUST NOT say any other lesson section as written |

### Calls <a id="calls"></a>

A *call* is a decision only the learner may make. Each lesson lists its calls as a list of mappings, each with an `id` (a kebab id) and an `ask` (a non-empty string, the question the tutor puts to the learner). A call id MUST be unique across the whole course, not only within its lesson, so that a record can name a call by id alone. The duties a runner has for calls are in [the execution contract](execution.md#calls-duties).

#### Call cases <a id="example-calls"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-call-shape-accepted"></a>Declared call | Baseline `intro.md` with `calls: [{id: choose-tool, ask: Which tool will your agent call first?}]` | Course syntax | Accepted | An `id` that is a kebab id and a non-empty `ask` |
| <a id="case-call-ask-missing-rejected"></a>`ask` missing | Baseline `intro.md` with `calls: [{id: choose-tool}]` | Course syntax | Rejected | `ask` is required |
| <a id="case-call-ids-unique-accepted"></a>Distinct call ids | Baseline: `intro.md` declares `choose-tool` and `finish.md` declares `choose-check` | Course syntax | Accepted | The set of call ids across both files has no repeat |
| <a id="case-call-ids-duplicate-rejected"></a>Same call id in two lessons | Baseline `finish.md` call renamed to `choose-tool`; both snippets together: `intro.md` has `id: choose-tool` and `finish.md` has `id: choose-tool` | Course syntax | Rejected | `choose-tool` appears twice across the course |

### Objectives <a id="objectives"></a>

An *objective* is a finer-grained outcome a lesson can settle. Each is a mapping with an `id` (a kebab id), `text` (a non-empty string) and `by`: either the id of one check listed in the same lesson, or the word `explain-back`. `explain-back` is allowed only in a `demonstrate` lesson. The kind of evidence follows from `by`: a command check gives `checked`, an observe check gives `observed` and `explain-back` gives `explained`.

`by` has one meaning. The word `explain-back` is reserved (see [names and ids](#names-and-ids)), so it can never be a check id, and `by: explain-back` always selects the explain-back. Any other value is a check id.

An objective id MUST be unique across the whole course, not only within its lesson. A lesson without `objectives` declares nothing that can settle. It can be passed or skipped, but it settles no objective.

#### Objective cases <a id="example-objectives"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-objectives-accepted"></a>Distinct objectives with valid selectors | Baseline `finish.md`: `agent-passes` has `by: final-check`, which the lesson lists; `agent-explained` has `by: explain-back` in the demonstrate lesson | Course syntax | Accepted | Ids differ; each `by` is a same-lesson check or the final explain-back |
| <a id="case-objectives-mixed-evidence-accepted"></a>Evidence kinds follow `by` | Baseline `finish.md` | Course syntax | Accepted | `agent-passes` is `checked`, because `final-check` is a command check; `agent-explained` is `explained` |
| <a id="case-objectives-duplicate-rejected"></a>Same objective id in two lessons | Extended baseline with `make.md` gaining `objectives: [{id: agent-passes, text: Runs, by: agent-runs}]` | Course syntax | Rejected | `agent-passes` is declared in `make.md` and in `finish.md` |
| <a id="case-objectives-check-elsewhere-rejected"></a>Check not in the same lesson | Extended baseline `finish.md` objective `agent-passes` changed to `by: agent-runs`; `agent-runs` is listed only in `make.md` | Course syntax | Rejected | `agent-runs` is not in `finish.md`'s `checks` |
| <a id="case-objectives-explain-back-in-build-rejected"></a>Explain-back selector in a build lesson | Extended baseline `make.md` with `objectives: [{id: made, text: Made, by: explain-back}]` | Course syntax | Rejected | `by: explain-back` is allowed only in a `demonstrate` lesson |
| <a id="case-objectives-none-accepted"></a>Lesson without objectives | Extended baseline `make.md` declares checks and no `objectives`; the learner passes `agent-runs` | Course syntax, then runner behaviour | Accepted | The lesson passes and nothing settles, because it declares no objective |
| <a id="case-objectives-invented-rejected"></a>Undeclared objective settled | The same trace, with the runner recording an objective `agent-built` as settled | Runner behaviour | Rejected | `agent-built` is declared nowhere, so nothing can settle it |
| <a id="case-objectives-check-with-reserved-id-rejected"></a>Check named like the selector | `finish.md` lists a check `explain-back`, declared completely with `run`, `verify` and `pass/` and `fail/` fixtures, and keeps the objective with `by: explain-back` | Course syntax | Rejected | The declaration is otherwise valid; the check id is reserved, so it cannot be declared and `by` stays unambiguous |
| <a id="case-objectives-second-evidence-accepted"></a>Explained and checked in one lesson | Baseline `finish.md`, where a command check and the explain-back each support one objective | Course syntax | Accepted | `by: explain-back` and `by: final-check` are each unambiguous |

### Starter files <a id="starter-files"></a>

A lesson's `starter` list names files under `assets/starter/` that the lesson adds to an `own` or reference project, never over an existing file. Each path is relative to `assets/starter/`, uses `/`, and has no empty, `.` or `..` segment. A path that does not exist is invalid. A starter project receives all of `assets/starter/` at the start, so these entries add nothing to it. Validate all selected sources and targets before writing. If any target exists, refuse the whole copy and ask for another destination or selection. Never overwrite an existing file.

#### Starter cases <a id="example-starter-links"></a>

These cases start from the extended baseline with `assets/starter/plan/README.md` added and `make.md` declaring `starter: [plan/README.md]`.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-starter-accepted"></a>Existing source, absent destination | The course above; the learner's project has no `plan/README.md`; the runner adds it | Course syntax, then runner behaviour | Accepted | `assets/starter/plan/README.md` exists and the destination is absent, so the file is added |
| <a id="case-starter-missing-rejected"></a>Missing source | `starter: [plan/MISSING.md]`, which does not exist | Course syntax | Rejected | A path that does not exist is invalid |
| <a id="case-starter-traversal-rejected"></a>Traversing source | `starter: [../outside.md]` | Course syntax | Rejected | A `..` segment is not allowed |
| <a id="case-starter-absolute-rejected"></a>Absolute source | `starter: [/etc/hosts]` | Course syntax | Rejected | A leading slash makes an empty first segment |
| <a id="case-starter-empty-segment-rejected"></a>Empty segment | `starter: [plan//README.md]` | Course syntax | Rejected | No empty segment is allowed |
| <a id="case-starter-collision-accepted"></a>Existing destination | The learner's project already has `plan/README.md`; the runner asks and keeps it | Runner behaviour | Accepted | The runner asks the learner and does not overwrite |
| <a id="case-starter-collision-overwrite-rejected"></a>Overwrite | The same project; the runner replaces `plan/README.md` with the starter file | Runner behaviour | Rejected | A runner never overwrites an existing target |

#### Starter answer cases <a id="example-starter-answer"></a>

These cases use the extended baseline. `make.md` asks the learner to write `plan/README.md` listing three steps: install, add a tool, run the check.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-starter-answer-accepted"></a>Starter holds only a skeleton | `assets/starter/plan/README.md` reads "# Plan" and "TODO: list your three steps"; `make.md` lists `plan/README.md` in `starter` | Course syntax | Accepted | The starter file is a skeleton; the three steps the lesson asks the learner to write are absent |
| <a id="case-starter-answer-finished-rejected"></a>Starter holds the finished answer | `assets/starter/plan/README.md` reads "# Plan", "1. Install", "2. Add a tool" and "3. Run the check"; nothing else changes | Course syntax | Rejected | The file already contains the three steps the lesson asks the learner to write, so it is a finished answer, and a course MUST NOT place one in `assets/starter/` |

## Links inside a course <a id="links"></a>

A link inside `COURSE.md` or a lesson is one of three kinds:

- A relative path to a file inside the course folder. **Proposed:** every such path is written from the course root, the folder holding `COURSE.md`, whichever file contains the link. A lesson links `assets/notes.md`, not `../assets/notes.md`. After resolving `.` and `..` the path MUST stay inside the course folder. Absolute paths, backslashes and links that leave the folder are invalid.
- A `project:` link to a file in the learner's project. See [project links](#project-links).
- An `https:` URL.

Links to `tutor/` files are not allowed in `COURSE.md` or in `## Goal`. A lesson link whose target does not exist is invalid. A `tutor/` link in a section addressed to the tutor, such as `## Build`, is allowed.

Course links use the course root as their base, even when written in a lesson. Authoring tools must apply this base explicitly. The same base applies to the lesson list, to `starter` paths (relative to `assets/starter/`) and to rubric and quiz names. It does not apply to `project:` links, which are relative to the project root, or to local project references, which are relative to the installed course root ([local project folders](#local-projects)).

#### Link cases <a id="example-links"></a>

These cases use the extended baseline with `assets/notes.md`, `assets/flow.png` and `tutor/finish.rubric.md` present.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-link-course-file-accepted"></a>Existing course file | `make.md` links `[Notes](assets/notes.md)`; from the course root that is `assets/notes.md`, which exists | Course syntax | Accepted | The path is read from the course root, the target exists and it stays inside the course folder |
| <a id="case-link-next-lesson-accepted"></a>Lesson link in the page | `COURSE.md` links `[Next](lessons/make.md)` | Course syntax | Accepted | The target `lessons/make.md` exists from the course root |
| <a id="case-link-asset-accepted"></a>Asset | `make.md` links `[Diagram](assets/flow.png)` | Course syntax | Accepted | `assets/flow.png` exists from the course root |
| <a id="case-link-file-relative-rejected"></a>Written from the linking file | `make.md` links `[Notes](../assets/notes.md)`, the form ordinary Markdown tools resolve from `lessons/` | Course syntax | Rejected | From the course root, `..` leaves the course folder, so the rule rejects it even though `assets/notes.md` exists |
| <a id="case-link-https-accepted"></a>HTTPS URL | `make.md` links `[Docs](https://example.com/guide)` | Course syntax | Accepted | `https:` URLs are allowed |
| <a id="case-link-http-rejected"></a>HTTP URL | `make.md` links `[Doc](http://example.com/guide)` | Course syntax | Rejected | Only `https:` URLs are allowed |
| <a id="case-link-tutor-in-build-accepted"></a>Tutor file from Build | `make.md` `## Build` links `[Rubric](tutor/finish.rubric.md)` | Course syntax | Accepted | The target exists from the course root, and `## Build` is addressed to the tutor |
| <a id="case-link-tutor-in-page-rejected"></a>Tutor file from the page | `COURSE.md` links `[Rubric](tutor/finish.rubric.md)` | Course syntax | Rejected | The target exists, and `tutor/` is not linked from `COURSE.md` |
| <a id="case-link-tutor-in-goal-rejected"></a>Tutor file from Goal | `make.md` `## Goal` links `[Rubric](tutor/finish.rubric.md)` | Course syntax | Rejected | The target exists, and `tutor/` is not linked from `## Goal` |
| <a id="case-link-missing-rejected"></a>Missing target | `make.md` links `[Missing](lessons/nope.md)`; no `lessons/nope.md` exists | Course syntax | Rejected | A lesson link whose target does not exist is invalid |
| <a id="case-link-escape-rejected"></a>Leaves the course | `make.md` links `[Up](../other-course/COURSE.md)` | Course syntax | Rejected | From the course root, `..` leaves the course folder. The cause is the escape, not a missing file, because the rule rejects it before looking for the target |
| <a id="case-link-project-prefix-accepted"></a>A project link is not a course link | `make.md` `## Build` links `[Model](project:src/ledger/model.py)` | Course syntax | Accepted | The `project:` prefix selects the project-root rule, so the course-root rule does not apply and no course file is needed |

## Projects <a id="projects"></a>

Every check runs against one directory, the *project root*. The `project` field says where that directory comes from.

### The project field <a id="project-field"></a>

The value is one *option* or a list of options. An option is `own`, `starter` or a [reference](#reference-grammar). Options are case-sensitive.

| Option | The learner works in |
| --- | --- |
| `own` | The project they already have open |
| `starter` | A new folder the runner creates from `assets/starter/` |
| A Git reference (`gh:` or `git+https://`) | A checkout of that repository at its pinned commit |
| A local folder (`./path`) | **Proposed:** an editable copy, made in the workspace, of a folder inside the installed course. See [local project folders](#local-projects) |

A scalar value is a list of one. An omitted field is the list `[own]`. A list MUST hold at least one option, MUST NOT repeat an option, and MAY mix kinds and hold several references. `starter` is valid only when `assets/starter/` exists and holds at least one file. A mapping, an empty string, an empty list or a value that is not an option is invalid.

#### Option shape cases <a id="example-project-options"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-options-omitted-accepted"></a>Omitted | Baseline, with no `project` key | Course syntax | Accepted | An omitted field means `[own]` |
| <a id="case-options-scalar-starter-accepted"></a>Scalar starter | Baseline with `project: starter` and `assets/starter/README.md` present | Course syntax | Accepted | A scalar is a list of one, and `assets/starter/` exists with a file |
| <a id="case-options-mixed-accepted"></a>Mixed list | Baseline with `assets/starter/README.md` and `project: [own, starter, gh:example-co/payments@v3.4.0, ./examples/app]`, with `examples/app` present | Course syntax | Accepted | The list is non-empty, repeats nothing and may mix kinds |
| <a id="case-options-empty-rejected"></a>Empty list | `project: []` | Course syntax | Rejected | A list MUST hold at least one option |
| <a id="case-options-duplicate-rejected"></a>Repeated option | `project: [own, own]` | Course syntax | Rejected | A list MUST NOT repeat an option |
| <a id="case-options-mapping-rejected"></a>Mapping | `project: {kind: own}` | Course syntax | Rejected | A mapping is not an option |
| <a id="case-options-unknown-rejected"></a>Not an option | `project: Own` | Course syntax | Rejected | Options are case-sensitive, and `Own` is not `own` |
| <a id="case-options-starter-empty-rejected"></a>Starter without files | `project: starter` and no `assets/starter/` folder | Course syntax | Rejected | `starter` needs `assets/starter/` holding at least one file |

### Selecting a project <a id="project-selection"></a>

If the list has one option, that option is used and nothing is asked. If it has two or more, the learner chooses before the first lesson. List order is presentation order and carries no default. A runner MAY recommend an option with its trade-off and MUST NOT choose for the learner.

- **No choice.** If the learner gives no choice, or the runner cannot ask, the course does not start. A runner MUST NOT pick a default and MUST NOT guess.
- **Invalid choice.** A choice that is not in the list is rejected and the learner is asked again. It is never replaced by another option and never recorded.

#### Project selection cases <a id="example-project-selection"></a>

These cases use the baseline with `assets/starter/README.md` present.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-selection-single-accepted"></a>One option | `project` omitted; no input | Project start | Accepted | A single option is used and nothing is asked; kind `own`, path `.` |
| <a id="case-selection-starter-accepted"></a>Learner chooses starter | `project: [own, starter]`; the learner answers `starter` and names the folder `work/app` | Project start | Accepted | A choice in the list was made by the learner; the runner then prepares `work/app`, which is the recorded path |
| <a id="case-selection-waiting-accepted"></a>Runner waits | `project: [own, starter]`; the runner asks and shows a recommendation; no answer has come | Project start | Accepted | Waiting is allowed; the course has not started |
| <a id="case-selection-silence-rejected"></a>Silence selects the first option | `project: [own, starter]`; no answer; the runner starts with `own` | Project start | Rejected | A runner MUST NOT pick a default |
| <a id="case-selection-cannot-ask-rejected"></a>Cannot ask yet starts | The same list; the runner cannot ask and starts with `starter` | Project start | Rejected | If the runner cannot ask, the course does not start |
| <a id="case-selection-invalid-rejected"></a>Invalid choice substituted | `project: [own, starter]`; the learner answers `gh:example-co/app`; the runner uses `own` | Project start | Rejected | A choice outside the list is rejected and asked again, never replaced |
| <a id="case-selection-invalid-reasked-accepted"></a>Invalid choice re-asked | The same answer; the runner says it is not offered and asks again, recording nothing | Project start | Accepted | The choice is rejected and the learner is asked again |
| <a id="case-selection-not-listed-rejected"></a>Choice not in a one-option list | `project: own`; the learner answers `starter` | Project start | Rejected | `starter` is not in the list, and nothing is started with it |

### The recorded project path <a id="project-path"></a>

The runner records the chosen *kind* and a *path*. The path is the project root written relative to a base, with `/` separators, no leading slash, no drive letter, no `..` segment and no trailing slash. The single value `.` means the base itself. The base depends on the kind:

| Kind | Base | Path |
| --- | --- | --- |
| `own` | The workspace root, where the learner started the runner | `.`, or the sub-folder the learner chose as their project, such as `services/api` |
| `starter` | The workspace root | The new folder the runner created from `assets/starter/`, such as `work/app`. Its name is the course name unless the learner chooses another. An existing non-empty folder is never reused; the runner asks for another name. |
| A Git reference | The root of the checkout | The folder after `#`, or `.` when there is none |
| A local folder (**proposed**) | The workspace root | The editable destination folder the copy was made in, such as `work/local-app`. It is never the source folder, such as `examples/app`. |

The exact field names and shape of a record belong to the record contract; this section defines only what the path means. A path that contains `..`, starts with `/` or ends with `/` is invalid.

#### Project path cases <a id="example-project-path"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-path-own-accepted"></a>Own, workspace root | `own`; the learner started the runner in their project | Project start | Accepted | Base is the workspace root and the project root is the base, so the path is `.` |
| <a id="case-path-own-sub-accepted"></a>Own, sub-folder | `own`; the learner chose `services/api` | Project start | Accepted | Base is the workspace root, and the root is the sub-folder `services/api` |
| <a id="case-path-starter-accepted"></a>Starter | `starter`; the learner chose `work/app`, which is new | Project start | Accepted | Base is the workspace root and the new folder is `work/app` |
| <a id="case-path-starter-default-accepted"></a>Starter default name | `starter` for the course `build-your-first-agent` with no name given | Project start | Accepted | The default is the course name |
| <a id="case-path-starter-nonempty-accepted"></a>Starter folder in use | `starter`; the chosen folder `plan` exists and is not empty | Project start | Accepted | An existing non-empty folder is never reused; the runner asks for another name and records nothing until one is chosen |
| <a id="case-path-git-subfolder-accepted"></a>Git subfolder | `gh:example-co/payments@v3.4.0#services/api` | Source resolution | Accepted | Base is the checkout root and the folder after `#` is `services/api` |
| <a id="case-path-git-root-accepted"></a>Git without a folder | `gh:example-co/payments@v3.4.0` | Source resolution | Accepted | No `#` folder, so the path is `.` |
| <a id="case-path-local-accepted"></a>Local destination | `./examples/app` copied to `work/local-app` in the workspace | Project start | Accepted | Base is the workspace root and the destination is `work/local-app`; the source `examples/app` is not the root |
| <a id="case-path-local-source-recorded-rejected"></a>Source recorded as destination | The same copy, with `examples/app` recorded as the path | Project start | Rejected | The recorded path is the editable destination, never the source folder |
| <a id="case-path-local-dot-rejected"></a>Local recorded as dot | The same copy, with `.` recorded | Project start | Rejected | A local destination is a child path, not `.` |
| <a id="case-path-trailing-slash-rejected"></a>Trailing slash | Any kind, with `plan/` | Project start | Rejected | A trailing slash is not allowed |
| <a id="case-path-traversal-rejected"></a>Traversal | Any kind, with `../other` | Project start | Rejected | A `..` segment is not allowed |
| <a id="case-path-absolute-rejected"></a>Absolute | Any kind, with `/home/learner/app` | Project start | Rejected | A leading slash is not allowed |
| <a id="case-path-drive-rejected"></a>Drive letter | Any kind, with `C:/app` | Project start | Rejected | A drive letter is not allowed |

### Local project folders (proposed) <a id="local-projects"></a>

A local folder is any ordinary directory inside the installed course, with no Git metadata needed. It is source material, never the place the learner works.

1. A local `project` reference resolves relative to the installed course root, never the shell's current directory or an enclosing Git checkout. A local course-install reference still resolves relative to the directory the runner was run from, and installing creates its own read-only course snapshot.
2. The source MUST be a present, non-empty directory inside the installed course snapshot. No Git repository, remote or commit is required, and a runner MUST NOT fabricate one.
3. Before copying, the runner resolves the source and every entry inside that subtree. It MUST refuse a link that leaves the subtree, a link cycle, an unreadable entry and a special file such as a device or pipe. Nothing is copied when it refuses.
4. The runner materialises the copy after the project is selected and the source is validated, and before the first lesson. It copies regular file contents and directories and MUST NOT run project code.
5. The learner, or the embedding application, supplies an editable destination inside the workspace root and outside the installed course tree. The destination is a fresh folder, or an existing empty folder. A non-empty destination is refused and another is asked for; existing files are kept.
6. The runner checks destination containment after resolving symbolic links. It MUST NOT place the copy inside its source or any installed course directory. A permitted link inside the source is copied as an ordinary file or directory, never as a link back into the source.
7. Checks and tutor edits use the destination as the project root. `AGENT_COURSE_PROJECT` names it. `AGENT_COURSE_DIR` keeps naming the read-only installed course.
8. The recorded path is the destination relative to the workspace root, such as `work/local-app`, under the [path rules](#project-path).
9. The source is fixed by the installed course snapshot. There is no separate Git pin and no lookup of enclosing Git history. Changing the author's original folder later cannot change the installed snapshot or touch an existing learner workspace.
10. Resume uses the existing workspace and the original snapshot, and MUST NOT copy the source again. Taking a newer snapshot requires an explicit upgrade by the learner. The [record contract](records.md#upgrade-projection) defines upgrade preparation and recovery. An upgrade MUST NOT overwrite the learner's workspace.
11. Representing the source identity, comparing payloads and storing the workspace binding are record work. These rules choose no field and no hash.

Source and destination for the cases below: the installed snapshot holds `examples/app/README.md` (40 lines) and `examples/app/src/main.py`, and has no `.git`. The workspace root holds no `work/` folder.

#### Local project cases <a id="example-local-projects"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-local-start-accepted"></a>Start from a non-Git folder | Course with `project: ./examples/app`; the learner supplies `work/local-app`; the runner validates the source, copies it and starts lesson one | Project start | Accepted | The source is a non-empty directory with no escaping links; the destination is fresh; the copy is made before the first lesson; the project root is `work/local-app` in the workspace; the recorded path is `work/local-app` |
| <a id="case-local-git-required-rejected"></a>Refused for missing Git | The same course; the runner refuses because `examples/app` has no `.git` or fabricates a commit for it | Project start | Rejected | No Git repository, remote or commit is required or fabricated |
| <a id="case-local-edit-copy-accepted"></a>Edit lands in the copy | The tutor edits `work/local-app/src/main.py` at the learner's request | Runner behaviour | Accepted | Edits use the destination as the project root; the installed `examples/app/src/main.py` is unchanged |
| <a id="case-local-edit-source-rejected"></a>Edit lands in the source | The tutor edits `examples/app/src/main.py` in the installed course | Runner behaviour | Rejected | The installed course is read-only and the learner works in the copy |
| <a id="case-local-empty-destination-accepted"></a>Empty existing destination | The learner supplies `work/local-app`, which exists and is empty | Project start | Accepted | An existing empty folder is allowed |
| <a id="case-local-nonempty-destination-accepted"></a>Non-empty destination is refused | The learner supplies `work/local-app`, which holds `notes.txt`; the runner refuses and asks for another; `notes.txt` is kept | Project start | Accepted | A non-empty destination is refused and existing files are preserved |
| <a id="case-local-nonempty-destination-rejected"></a>Copy into a non-empty destination | The same destination; the runner copies the source into it, merging with `notes.txt` | Project start | Rejected | A non-empty destination MUST be refused |
| <a id="case-local-destination-in-course-rejected"></a>Destination inside the course | The learner supplies `examples/app/copy`, inside the installed course and inside the source | Project start | Rejected | The destination must be outside the installed course tree and outside the source |
| <a id="case-local-destination-escape-rejected"></a>Destination escapes the workspace | The learner supplies `../elsewhere`, or a `work/` that is a link resolving outside the workspace | Project start | Rejected | Containment is checked after resolving links, and the destination must be inside the workspace |
| <a id="case-local-source-missing-rejected"></a>Source missing or empty | `project: ./examples/missing`, or an `examples/app` with no files | Project start | Rejected | The source MUST be a present, non-empty directory |
| <a id="case-local-inner-link-accepted"></a>Link inside the source | The source holds `src/alias.py` linking to `src/main.py` inside the subtree; the copy holds `work/local-app/src/alias.py` as an ordinary file with the same contents | Project start | Accepted | A permitted link is copied as an ordinary file, not as a link into the source |
| <a id="case-local-escaping-link-rejected"></a>Link leaves the source | The source holds `src/secret.txt` linking to a file outside `examples/app`; the runner refuses before copying anything | Project start | Rejected | A link that leaves the subtree MUST be refused, and `work/local-app` is not created |
| <a id="case-local-cycle-rejected"></a>Link cycle | The source holds `loop` linking to its own parent folder | Project start | Rejected | A link cycle MUST be refused |
| <a id="case-local-special-file-rejected"></a>Special file | The source holds a named pipe `src/feed` | Project start | Rejected | A special file MUST be refused |
| <a id="case-local-unreadable-rejected"></a>Unreadable entry | The source holds `src/locked.txt` that the runner cannot read | Project start | Rejected | An unreadable entry MUST be refused |
| <a id="case-local-snapshot-stable-accepted"></a>Source changes later | After install the author edits their original `examples/app/README.md`; the learner resumes; the installed snapshot and `work/local-app` are used | Runner behaviour | Accepted | The source is fixed by the installed snapshot, and resume uses the existing workspace |
| <a id="case-local-recopy-rejected"></a>Resume recopies | The same resume; the runner copies the source over `work/local-app`, losing the learner's edits | Runner behaviour | Rejected | Resume MUST NOT copy the source again and the original workspace is not overwritten |
| <a id="case-local-fabricated-pin-rejected"></a>Requires a fabricated commit | The same course; the runner records a made-up commit to pin the folder | Runner behaviour | Rejected | There is no separate Git pin for a local folder |
| <a id="case-local-install-relative-accepted"></a>Install source and project source differ | A learner runs the runner from `~/work` and installs `./courses/sample-course`; the course's `project: ./examples/app` is read inside the installed course | Source resolution | Accepted | The install reference is relative to the invocation directory; the project reference is relative to the installed course root |
| <a id="case-local-cwd-rejected"></a>Project resolved against the shell directory | The same learner; the runner looks for `~/work/examples/app` | Source resolution | Rejected | A local project reference is never relative to the shell's current directory |

#### Explicit upgrade cases <a id="example-upgrade"></a>

These cases use the local-folder course installed with workspace `work/local-app`, where the learner has edited `src/main.py`. The author has since published a newer snapshot. The [record contract](records.md#upgrade-projection) defines compatibility, progress archives and durable transitions.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-upgrade-preserved-accepted"></a>Upgrade leaves the workspace alone | The learner explicitly asks to upgrade; the runner takes the newer snapshot as the installed course and leaves every file of `work/local-app`, including the edited `src/main.py`, byte for byte as it was | Runner behaviour | Accepted | The upgrade was explicit, and the workspace was not overwritten |
| <a id="case-upgrade-permission-accepted"></a>Upgrade asks first | The learner explicitly asks to upgrade; the runner explains that the course upgrade keeps the editable workspace unchanged, and changes no workspace files | Runner behaviour | Accepted | The learner requested the content upgrade; the editable workspace stays unchanged |
| <a id="case-upgrade-silent-overwrite-rejected"></a>Upgrade overwrites silently | The learner explicitly asks to upgrade; the runner copies the newer snapshot over `work/local-app` without asking, replacing the edited `src/main.py` | Runner behaviour | Rejected | An upgrade MUST NOT overwrite the workspace |
| <a id="case-upgrade-unrequested-rejected"></a>Snapshot changes without a request | The learner has not asked to upgrade; the runner takes the newer snapshot as the installed course on resume and changes no workspace file | Runner behaviour | Rejected | Taking a newer snapshot requires an explicit upgrade by the learner |

### The reference grammar <a id="reference-grammar"></a>

One grammar names a course to install and a project to work in.

```text
reference  = gh-ref | git-ref | local-ref
gh-ref     = "gh:" owner "/" repo [ "@" revision ] [ "#" folder ]
git-ref    = "git+https://" host "/" repopath [ "@" revision ] [ "#" folder ]
local-ref  = "./" relpath
host       = label { "." label } [ ":" port ]
label      = 1 to 63 of letter, digit or "-", not starting or ending with "-"
port       = 1 to 5 digits with a value from 1 to 65535
repopath   = segment { "/" segment }
folder     = segment { "/" segment }
relpath    = segment { "/" segment }
segment    = 1 to 100 of letter, digit, ".", "_", "-", "+" or "~", other than "." and ".."
revision   = tag | commit
commit     = 40 or 64 lowercase hexadecimal characters
tag        = see the tag rule below
```

| Form | Meaning |
| --- | --- |
| `gh:owner/repo` | The repository's default branch, resolved once and pinned |
| `gh:owner/repo@v1.2.0` | A tag |
| `gh:owner/repo@<40 or 64 hex characters>` | A full commit, the strongest pin |
| `gh:owner/repo@v1.2.0#path/to/folder` | A folder inside the repository |
| `git+https://git.example.com/team/repo.git@v1.2.0#path` | Any Git host over HTTPS, same `@` and `#` |
| `./relative/path` | A local folder, copied for a project (see [local project folders](#local-projects)) |
| `git+https://git.example.com/team/repo.git@v1` | Repository path `team/repo.git`, tag `v1` |

Rules:

- `owner` is 1 to 39 characters of letters, digits and hyphens, starting with a letter or digit. `repo` is 1 to 100 characters of letters, digits, `.`, `_` and `-`, and does not end in `.git`.
- A *tag* is 1 to 128 characters of letters, digits, `.`, `_`, `-` and `/`. It does not start with `-` or `/`, does not end with `/` or `.`, and contains neither `..` nor `//`. A revision of 40 or 64 lowercase hexadecimal characters is a commit; every other revision is a tag. An abbreviated commit is therefore read as a tag name, and if no such tag exists the reference fails. A branch is never named after `@`.
- Omitting `@` selects the default branch once; the runner then pins the commit it found.
- `folder` and `relpath` are paths of segments separated by single `/`. No segment is empty, `.` or `..`, the path does not start or end with `/`, and it holds no backslash.
- `host` is a DNS name with an optional port, as the grammar shows. A `git+https` reference MUST NOT contain a user, a password, a token or a query string. Because `@` and `#` are not segment characters, the first `@` after the repository path always starts the revision and the first `#` always starts the folder. An `@` before the host's `/` is therefore a credential and makes the reference invalid, and a runner MUST NOT record it.
- `repopath` has one or more segments separated by single `/`. It may end in `.git`. It has no empty segment, no `.` or `..` segment and no trailing `/`. It holds no `@`, `#`, `?` or `:`.
- `@` and `#` each appear at most once, `@` before `#`, and neither may be followed by nothing: an empty revision or an empty folder is invalid.
- A `local-ref` starts with `./`. It has no `@` and no `#`, and no segment of its path is empty or `..`. It is never a Git reference and has no revision. As a `project` option it is relative to the installed course root. As an install source it is relative to the directory the learner ran the runner from. A symbolic link that leaves its base is refused.
- No part of a reference may contain a space, control character or backslash.

#### Valid reference cases <a id="example-reference-valid"></a>

| Case | Reference | Judged as | Outcome | One parse |
| --- | --- | --- | --- | --- |
| <a id="case-ref-default-accepted"></a>Default branch | `gh:example-co/payments` | Source resolution | Accepted | gh, owner `example-co`, repo `payments`, no revision (default branch pinned when first resolved), no folder; project path `.` |
| <a id="case-ref-tag-accepted"></a>Tag | `gh:example-co/payments@v3.4.0` | Source resolution | Accepted | revision `v3.4.0` is not 40 or 64 hex characters, so it is a tag |
| <a id="case-ref-branch-name-accepted"></a>Branch-like name | `gh:example-co/payments@main` | Source resolution | Accepted | Parses as a tag named `main`; it is never read as a branch, so a runner that finds no such tag refuses the reference |
| <a id="case-ref-short-commit-accepted"></a>Abbreviated commit | `gh:example-co/payments@9f3c2e1` | Source resolution | Accepted | Seven hex characters are not a commit, so it parses as a tag named `9f3c2e1` |
| <a id="case-ref-commit-accepted"></a>Full commit | `gh:example-co/payments@9f3c2e1a4b5d6c7e8f90a1b2c3d4e5f607182930` | Source resolution | Accepted | 40 lowercase hex characters make a commit |
| <a id="case-ref-subfolder-accepted"></a>Git subfolder | `gh:example-co/payments@v3.4.0#services/ledger` | Source resolution | Accepted | tag `v3.4.0`, folder `services/ledger`; project path `services/ledger` |
| <a id="case-ref-generic-accepted"></a>Generic HTTPS host | `git+https://git.example.com/team/repo.git@v1.2.0#docs` | Source resolution | Accepted | host `git.example.com`, repopath `team/repo.git`, tag `v1.2.0`, folder `docs` |
| <a id="case-ref-local-accepted"></a>Local folder | `./examples/app` | Source resolution | Accepted | local-ref with relpath `examples/app`; no revision and no folder |

#### Invalid reference cases <a id="example-reference-invalid"></a>

Each case is judged as source resolution and is rejected for the one reason shown.

| Case | Reference | Outcome | Deciding rule |
| --- | --- | --- | --- |
| <a id="case-ref-folder-traversal-rejected"></a>Folder traversal | `gh:example-co/payments#../secrets` | Rejected | `..` is not a segment |
| <a id="case-ref-folder-absolute-rejected"></a>Folder absolute | `gh:example-co/payments#/etc` | Rejected | The folder must not start with `/` |
| <a id="case-ref-credentials-rejected"></a>Credentials | `git+https://user:token@git.example.com/team/repo.git` | Rejected | A `git+https` reference MUST NOT contain a user, password or token |
| <a id="case-ref-ssh-rejected"></a>Unsupported scheme | `git+ssh://git.example.com/team/repo.git` | Rejected | Only `git+https://` is a Git form |
| <a id="case-ref-local-traversal-rejected"></a>Local traversal | `./../outside` | Rejected | No `..` segment |
| <a id="case-ref-absolute-rejected"></a>Absolute local path | `/home/learner/app` | Rejected | Not a reference form; a local reference starts with `./` |
| <a id="case-ref-local-revision-rejected"></a>Local with a revision | `./app@v1` | Rejected | A local reference has no `@` |
| <a id="case-ref-no-repopath-rejected"></a>No repository path | `git+https://git.example.com` | Rejected | `repopath` is required |
| <a id="case-ref-empty-repopath-rejected"></a>Empty repository path | `git+https://git.example.com/@v1` | Rejected | `repopath` has no segment |
| <a id="case-ref-empty-segment-rejected"></a>Empty segment | `git+https://git.example.com/team//repo` | Rejected | No empty segment |
| <a id="case-ref-dotdot-segment-rejected"></a>Dot-dot segment | `git+https://git.example.com/team/../repo` | Rejected | No `..` segment |
| <a id="case-ref-trailing-slash-rejected"></a>Trailing slash | `git+https://git.example.com/team/repo/` | Rejected | `repopath` has no trailing `/` |
| <a id="case-ref-port-rejected"></a>Port out of range | `git+https://git.example.com:0/team/repo` | Rejected | A port is 1 to 65535 |
| <a id="case-ref-host-rejected"></a>Malformed host | `git+https://-git.example.com/team/repo` | Rejected | A label may not start with `-` |
| <a id="case-ref-empty-revision-rejected"></a>Empty revision | `git+https://git.example.com/team/repo@` | Rejected | `@` may not be followed by nothing |
| <a id="case-ref-empty-folder-rejected"></a>Empty folder | `gh:example-co/payments#` | Rejected | `#` may not be followed by nothing |
| <a id="case-ref-repeated-at-rejected"></a>Repeated delimiter | `gh:example-co/payments@v1@v2` | Rejected | `@` appears at most once |

#### Reference length and range cases <a id="example-reference-lengths"></a>

Each case starts from `gh:example-co/payments@v3.4.0` or `git+https://git.example.com/team/repo.git@v1.2.0` and changes one part.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-ref-lengths-accepted"></a>Largest allowed parts | An owner of 39 characters, a repo of 100, a tag of 128, a folder segment of 100, a host label of 63 and, separately, ports 1 and 65535 | Source resolution | Accepted | Each part is at its maximum or inside its range |
| <a id="case-ref-owner-long-rejected"></a>Owner of 40 characters | `gh:` with a 40-character owner, repo `payments` | Source resolution | Rejected | An owner is 1 to 39 characters |
| <a id="case-ref-repo-long-rejected"></a>Repo of 101 characters | `gh:example-co/` with a 101-character repo | Source resolution | Rejected | A repo is 1 to 100 characters |
| <a id="case-ref-repo-git-suffix-rejected"></a>`.git` on a `gh:` repo | `gh:example-co/payments.git` | Source resolution | Rejected | A `gh:` repo does not end in `.git` |
| <a id="case-ref-tag-long-rejected"></a>Tag of 129 characters | `gh:example-co/payments@` followed by 129 letters `v` | Source resolution | Rejected | A tag is 1 to 128 characters |
| <a id="case-ref-segment-long-rejected"></a>Segment of 101 characters | `gh:example-co/payments#` followed by one 101-character folder segment | Source resolution | Rejected | A segment is 1 to 100 characters |
| <a id="case-ref-label-long-rejected"></a>Host label of 64 characters | `git+https://` with a 64-character first label, then `.example.com/team/repo` | Source resolution | Rejected | A label is 1 to 63 characters |
| <a id="case-ref-port-high-rejected"></a>Port 65536 | `git+https://git.example.com:65536/team/repo` | Source resolution | Rejected | A port is at most 65535 |

#### Reference boundary cases <a id="example-reference-boundaries"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-ref-boundary-accepted"></a>Credential-free reference | `gh:example-co/payments@v3.4.0#services/ledger`; the runner clones with the learner's own Git credentials | Source resolution | Accepted | The reference holds no credential, and the runner supplies the learner's own |
| <a id="case-ref-boundary-credentials-recorded-rejected"></a>Credentials recorded | `git+https://user:token@git.example.com/team/repo.git`; the runner records it | Source resolution | Rejected | A reference MUST NOT contain a credential and a runner MUST NOT record one |
| <a id="case-ref-boundary-local-escape-rejected"></a>Source link escapes | The local source `examples/app` holds `src/secret.txt` linking outside it | Source resolution | Rejected | A symbolic link that leaves the source's base is refused |

#### Query string cases <a id="example-reference-query"></a>

Both cases start from `git+https://git.example.com/team/repo.git@v1.2.0#docs`, which is accepted.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-ref-query-accepted"></a>No query string | `git+https://git.example.com/team/repo.git@v1.2.0#docs` | Source resolution | Accepted | Host, repository path, tag `v1.2.0` and folder `docs` parse and there is no `?` |
| <a id="case-ref-query-after-path-rejected"></a>Query after the repository path | `git+https://git.example.com/team/repo.git?ref=main@v1.2.0#docs`; no credential and nothing else changes | Source resolution | Rejected | A `git+https` reference MUST NOT contain a query string |
| <a id="case-ref-query-after-folder-rejected"></a>Query after the folder | `git+https://git.example.com/team/repo.git@v1.2.0#docs?x=1`; no credential and nothing else changes | Source resolution | Rejected | A `git+https` reference MUST NOT contain a query string |

### Links into the project <a id="project-links"></a>

A lesson links to a file in the learner's project with the `project:` prefix, followed by a relative path and an optional line fragment: `project:<path>` or `project:<path>#L<start>` or `project:<path>#L<start>-L<end>`. The path is relative to the project root, uses `/`, has no empty, `.` or `..` segment, does not start with `/` and has no query. A space or other special character in the path is percent-encoded and decoded once.

### Line ranges <a id="line-ranges"></a>

Line ranges are allowed. `#L10` names one line and `#L10-L40` names lines 10 to 40 inclusive. Lines are counted from 1, `<start>` and `<end>` are positive integers without a leading zero or a sign, and `<start>` is at most `<end>`. No other fragment, no column and no multi-range form is allowed.

### When a project link is checked <a id="link-validation-timing"></a>

Syntax is checked for every kind before teaching. Whether a target exists and holds its lines is checked at two moments.

| Project kind | Baseline check before the selected project starts | Check at every open |
| --- | --- | --- |
| Git reference | Against the immutable pinned checkout: the file exists and the range lies inside it | Against the learner's editable project root |
| Local folder (**proposed**) | Against the selected subtree of the installed course snapshot, before it is copied | Against the learner's editable project root |
| `own`, `starter` | None; the learner's project decides the target | Against the learner's editable project root |

- A missing file or out-of-bounds range in a Git or local baseline rejects that project's start. It is never a verified link.
- An offline authoring check may report a Git source as unavailable. It MUST NOT claim the targets passed, and starting waits for validation.
- At every open, the runner resolves the link against the actual editable project root, rechecking containment, existence and line bounds. A link it cannot resolve is shown as unresolved, with a warning. The tutor MUST NOT guess the missing content and MUST NOT open the immutable source instead.
- A learner edit that removes a formerly valid target therefore produces an unresolved-link warning, not a change to the baseline.

#### Project link syntax cases <a id="example-project-links"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-link-syntax-valid-accepted"></a>Path, line and range | `project:src/ledger/model.py`, `project:src/ledger/model.py#L10` and `project:src/ledger/model.py#L10-L40` in turn | Course syntax | Accepted | Each has a relative path and, at most, one `L<start>` or `L<start>-L<end>` fragment |
| <a id="case-link-range-reversed-rejected"></a>Start after end | `project:src/ledger/model.py#L40-L10` | Course syntax | Rejected | `<start>` must be at most `<end>` |
| <a id="case-link-range-zero-rejected"></a>Line zero | `project:src/ledger/model.py#L0` | Course syntax | Rejected | Lines count from 1 |
| <a id="case-link-range-open-rejected"></a>Open range | `project:src/ledger/model.py#L10-` | Course syntax | Rejected | `<end>` is required in a range |
| <a id="case-link-range-multiple-rejected"></a>Several ranges | `project:src/ledger/model.py#L10,L20` | Course syntax | Rejected | No multi-range form |
| <a id="case-link-range-leading-zero-rejected"></a>Leading zero | `project:src/ledger/model.py#L010` | Course syntax | Rejected | Integers have no leading zero |
| <a id="case-link-project-traversal-rejected"></a>Traversal | `project:../secret.txt` | Course syntax | Rejected | No `..` segment |
| <a id="case-link-project-absolute-rejected"></a>Absolute | `project:/etc/passwd` | Course syntax | Rejected | The path must not start with `/` |
| <a id="case-link-project-fragment-rejected"></a>Not a line fragment | `project:src/model.py#section` | Course syntax | Rejected | Only line fragments are allowed |

#### Project link timing cases <a id="example-link-timing"></a>

These cases use the local-folder course with `examples/app/README.md` of 40 lines, and a lesson `## Build` that links `project:README.md#L10-L40`.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-link-baseline-accepted"></a>Range inside the source | The source `README.md` has 40 lines | Project start | Accepted | The file exists and lines 10 to 40 lie inside the 40 lines, so the baseline check passes before copying |
| <a id="case-link-baseline-out-of-bounds-rejected"></a>Range outside the source | The source `README.md` has 9 lines; the link is `#L10-L40` and, separately, `#L10` | Project start | Rejected | Line 10 does not exist in the baseline, so the project does not start and the link is not verified |
| <a id="case-link-baseline-missing-file-rejected"></a>Target file missing in the source | The source has no `README.md` and the link is `project:README.md#L10` | Project start | Rejected | A missing file in the baseline rejects the start |
| <a id="case-link-single-line-accepted"></a>Single line inside the source | The link is `project:README.md#L10` and the file has 40 lines | Project start | Accepted | Line 10 exists |
| <a id="case-link-git-pin-accepted"></a>Git baseline | The reference is `gh:example-co/payments@v3.4.0` and the pinned checkout holds `README.md` with 40 lines | Project start | Accepted | The range is checked against the pinned checkout before the project starts |
| <a id="case-link-git-offline-accepted"></a>Offline author check | An authoring check runs with no network for a Git reference | Advisory lint | Accepted with a warning | The check reports the source as unavailable and does not claim the targets passed |
| <a id="case-link-git-offline-claimed-rejected"></a>Offline check claims success | The same offline run reports every target verified | Advisory lint | Rejected | An unavailable source cannot be reported as validated |
| <a id="case-link-live-deleted-warning"></a>Learner deletes the lines | After the copy the learner trims `work/local-app/README.md` to 12 lines; the lesson opens `#L10-L40` | Runner behaviour | Accepted with a warning | The open resolves against the editable root, finds lines 13 to 40 missing, and shows an unresolved-link warning without guessing |
| <a id="case-link-live-fallback-rejected"></a>Falls back to the source | The same open; the runner shows lines 10 to 40 of the installed source | Runner behaviour | Rejected | The tutor MUST NOT open the immutable source instead |
| <a id="case-link-live-guessed-rejected"></a>Guesses the lines | The same open; the runner recites what lines 13 to 40 used to say | Runner behaviour | Rejected | The tutor MUST NOT guess content it cannot read |
| <a id="case-link-own-teaching-time-accepted"></a>Own project | `own`; the lesson opens `project:src/app.py#L5` in the learner's project at teaching time | Runner behaviour | Accepted | No baseline exists; the learner's project decides the target |

## Authored counts <a id="authored-counts"></a>

Counts are derived, never written. Learner-facing text, meaning the description, the page and any `## Goal`, SHOULD NOT contain a lesson count, an objective count, a total duration, a percentage of progress, the form `lesson N` or `lesson N of M`, or a number word in those positions such as `lesson three`. Because lessons are reordered by id, a number in `lesson 3` is wrong the moment the list changes. This is **Advice**: a lint check warns, and a course containing a count is still valid. The public lint implementation is later work.

#### Count cases <a id="example-counts"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-count-none-accepted"></a>No count | Baseline with the goal "Add a tool your agent can call." | Advisory lint | Accepted | No count form appears |
| <a id="case-count-lesson-n-warning"></a>"Lesson 3" | Baseline `## Goal` reads "Lesson 3 adds a tool." | Advisory lint | Accepted with a warning | The form `lesson N` is flagged; lessons are reordered by id |
| <a id="case-count-lesson-word-warning"></a>"lesson three" | Baseline `## Goal` reads "In lesson three you add a tool." | Advisory lint | Accepted with a warning | A number word in the `lesson N` position is flagged |
| <a id="case-count-lesson-of-warning"></a>"lesson 2 of 5" | Baseline description ends "Read lesson 2 of 5 first." | Advisory lint | Accepted with a warning | The form `lesson N of M` is flagged |
| <a id="case-count-lessons-warning"></a>A lesson count | Baseline description reads "Five lessons build the agent." | Advisory lint | Accepted with a warning | A lesson count is flagged; nothing else is changed |
| <a id="case-count-objectives-warning"></a>An objective count | Baseline `## Goal` of `finish.md` reads "You will reach 2 objectives." | Advisory lint | Accepted with a warning | An objective count is flagged; nothing else is changed |
| <a id="case-count-percent-warning"></a>A progress percentage | Baseline description reads "You will be 40% done after the first lesson." | Advisory lint | Accepted with a warning | A percentage of progress is flagged; nothing else is changed |
| <a id="case-count-total-warning"></a>A total duration | Baseline description reads "About 45 minutes in total." | Advisory lint | Accepted with a warning | A total duration is flagged; nothing else is changed |
| <a id="case-count-duration-rejected"></a>Rejecting for a total duration | The total-duration course, refused by a validator because "About 45 minutes in total" is advice it did not follow | Advisory lint | Rejected | A total duration is advice, so a validator may only warn |
| <a id="case-count-rejected"></a>Rejecting for a count | The "lesson 3" course, refused by a validator because of the count | Advisory lint | Rejected | Advice never makes a course invalid; a validator may only warn |

## Course versions <a id="course-versions"></a>

| Change to a course | Version bump |
| --- | --- |
| Wording, typos, examples, hints | Patch |
| A new lesson anywhere, a new optional check, a new reference | Minor |
| Removing or renaming a lesson id, a new required check, or anything that makes a previously passing project fail, including a new project pin | Major |

This table is **Advice** for authors. No version choice makes a course rejected. The specification itself follows the same rule: a 1.x minor only adds optional fields, headings and capabilities, so every 1.0 course stays valid.

#### Version cases <a id="example-versions"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-version-typo-accepted"></a>Typo fixed | A hint typo corrected; version `1.2.0` becomes `1.2.1` | Advisory lint | Accepted | A typo is a patch change |
| <a id="case-version-lesson-added-accepted"></a>Optional lesson added | A new optional lesson added; `1.2.1` becomes `1.3.0` | Advisory lint | Accepted | A new lesson is a minor change |
| <a id="case-version-rename-accepted"></a>Lesson renamed with a major bump | Lesson id `install` renamed `setup`; `1.3.0` becomes `2.0.0` | Advisory lint | Accepted | A renamed lesson id is a major change |
| <a id="case-version-rename-patch-warning"></a>Lesson renamed, patch bump | Lesson id `install` renamed `setup`; version `1.3.0` becomes `1.3.1`, and both versions are available to compare | Advisory lint | Accepted with a warning | The bump is too small for a rename; advice only, never a rejection |
| <a id="case-version-rename-patch-rejected"></a>Rejecting the mismatch | The same pair, refused by a validator because of the bump | Advisory lint | Rejected | No version choice makes a course invalid |

## Constraints a schema cannot check <a id="markdown-only-constraints"></a>

A schema validates one file's structure. The rules below need the Markdown body or several files, so a Markdown validator or a runner must enforce them. Each is listed with its home in the requirement register.

- Folder name equals `name` ([course folder](#course-shape)).
- Recognised headings appear with the required cardinality and only at level two, outside code fences ([the page](#course-page), [lesson headings](#lesson-headings)).
- The lesson list matches the files in `lessons/` exactly, with no repeats ([lesson list](#lesson-list)).
- The last listed lesson is the only `demonstrate` lesson ([stages](#stages)).
- A lesson id equals its file name, and files that name a lesson use that id ([names and ids](#names-and-ids), [lessons](#lessons)).
- Call ids and objective ids are unique across all lessons ([calls](#calls), [objectives](#objectives)).
- An objective's `by` names a check in the same lesson, or `explain-back` in the final lesson ([objectives](#objectives)).
- Every check id in a lesson exists in the course frontmatter `checks` list ([execution contract](execution.md#check-declarations)).
- A rubric exists for the final lesson and its criteria count equals its pass denominator ([rubric grammar](execution.md#rubric-grammar)).
- Every relative link, written from the course root, stays in the course folder, `tutor/` is not linked from learner-visible text and `project:` links follow the line-range grammar ([links](#links), [line ranges](#line-ranges)).
- A `starter` project requires a non-empty `assets/starter/` ([project field](#project-field)).
- A local folder reference names a present, non-empty directory with no escaping link, cycle or special file ([local project folders](#local-projects)).

#### File-shape versus whole-course cases <a id="example-markdown-only"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-markdown-only-accepted"></a>Each file passes, and the whole course passes | Extended baseline; each file is checked alone against its schema, then the whole course by the Markdown validator | Course syntax | Accepted | Each file is well formed, the lesson list matches the files, and every call and objective id is unique across files |
| <a id="case-markdown-only-duplicate-rejected"></a>Each file passes, the whole course does not | The same course with `make.md` and `finish.md` both declaring objective `agent-passes`; every file still passes its single-file shape | Course syntax | Rejected | The single-file schema check passes, and the later Markdown check fails because `agent-passes` is declared twice across files |
