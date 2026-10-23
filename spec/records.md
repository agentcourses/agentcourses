# Agent Courses 1.0: learner record contract

This page defines what a runner writes down about a learner's progress, and how anyone can rebuild that picture from its protected history and verified authored course folders. A learner's progress lives in two files: an append-only list of events and a small record derived from it. A third file, the course lock, pins which course was installed. Every progress claim derives from those inputs, and no learner's answer, conversation, code or file contents ever enters either file. The page also fixes the file shapes, the replay and recovery rules, and the names, schema addresses and status words that the candidate uses. Course identity, the digest the lock stores, is defined in [the identity contract](identity.md).

This is a pre-release specification. No runner or host is qualified by these rules or their internal proofs. Qualified learner confirmation requires the protected capability described in [the receipt boundary](#receipt-boundary).

## Retained snapshot provenance <a id="candidate-provenance"></a>

Retained authored metadata MUST be interpreted under its original installation context.
Supply that context from trusted installation provenance outside authored snapshots and published record payloads.
Identity and protected transition bindings prove which bytes the history retained; they cannot prove how those bytes were originally interpreted.
Never infer provenance from an authored field, folder label, lock, event, digest or current schema manifest.

Before reading retained metadata, require supported installation context for each referenced snapshot.
Missing context stops with only `req-record-replay-data: missing retained candidate provenance for <identity>; supply the original installation candidate`.
Unsupported context stops with only `req-record-replay-data: unsupported retained candidate provenance for <identity>; supply the original installation candidate`.
The diagnostic identifies the snapshot and the context the caller must recover.
A synthetic context used in an internal proof does not authenticate an arbitrary real snapshot.

After context selection, apply safe capture, containment, stable-byte, identity and protected-transition checks.
Use the same context for whole-course checking, metadata, declarations and resource resolution.
Current input requires `format: "1.0.0-rc.2"` before declarations are read.
An invalid discriminator stops replay with only `req-record-replay-data: invalid rc.2 format identifier for <identity>`.
Separate declaration files stop replay with only `req-record-replay-data: mixed declarations for <identity>`.
No stopped replay publishes a projection or applies the transition.

Direct metadata, catalogue and resource readers use the same early boundary and report the [format contract's exact finding](format.md#format-identifier).
This adds no format field to lock, event, record or receipt payloads.
Receipt verification, learner ownership, generation, settlement and consent apply independently of the declaration location.

### Retained provenance cases <a id="candidate-provenance-cases"></a>

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-provenance-retained-context-missing"></a>Missing context | Pass only a retained path without installation context | Retained interpretation | Rejected | Only the missing-provenance diagnostic; zero metadata reads |
| <a id="case-provenance-retained-context-unknown"></a>Unsupported context | Supply unsupported installation context | Retained interpretation | Rejected | Only the unsupported-provenance diagnostic; zero metadata reads |
| <a id="case-provenance-retained-known-accepted"></a>Known context | Supply the trace tree with trusted context, matching digest and valid source | Retained interpretation | Accepted | Valid source derives the expected projection |
| <a id="case-provenance-retained-tamper-rejected"></a>Tampered source | Change retained authored bytes without changing the referenced digest | Retained interpretation | Rejected | Identity mismatch; no projection |
| <a id="case-provenance-retained-label-rejected"></a>Label used as provenance | A retained folder has a format label but trusted installation context is missing | Retained interpretation | Rejected | Only missing-provenance refusal |
| <a id="case-provenance-retained-new-invalid-rejected"></a>Invalid discriminator | Current trace without format, with identity recomputed and transition rebound | Retained interpretation | Rejected | Only invalid-format refusal; no projection |
| <a id="case-provenance-retained-new-mixed-rejected"></a>Separate declarations | Current trace plus a separate root feedback declaration file, with identity recomputed and transition rebound | Retained interpretation | Rejected | Only mixed-declarations refusal; no projection |

## Reading this page <a id="reading"></a>

The words MUST, MUST NOT, SHOULD and MAY are used as in [the format contract](format.md#rules-and-advice). Cases are rows in tables built as [the format contract's case tables](format.md#case-tables) describe, with three extra subjects. *Record structure* judges whether one file or line has the right shape. *Record replay* judges what a reader derives from a log: *Accepted* means the line is applied as written, *Accepted with a warning* means it is applied and a recovery note is reported, and *Rejected* means the line is invalid or not applied and leaves no trace in the record except a report. *Candidate wording* judges a statement the candidate itself makes.

An *identifier* is a kebab id of 1 to 64 characters, as [names and ids](format.md#names-and-ids) defines. A *time* is a UTC timestamp written `YYYY-MM-DDTHH:MM:SSZ`, with no fractions and no offset. An *identity* is the string [the identity contract](identity.md#purpose) defines. A *snapshot* is the installed course folder, named by its identity.

## Files and where they live <a id="files"></a>

All learner state sits under `.agents/` in the workspace root, beside the installed course.

| Path | What it is | Who may change it | Shared with a team |
| --- | --- | --- | --- |
| `.agents/courses.lock` | The pin for each installed course ([the lock](#lock-file)) | The runner, atomically | Yes, committed |
| `.agents/records/<course>/events.jsonl` | The history ([the event log](#event-log)) | The runner appends lines; nothing edits or reorders one | No |
| `.agents/records/<course>/record.json` | The current picture, derived from the events ([the record](#record)) | The runner replaces the whole file ([atomic replacement](#atomic-record)) | No |
| `.agents/course-snapshots/<digits>/<course>/` | The immutable authored folder for one applied snapshot ([retained sources](#replay-data)); `<digits>` is the 64 lowercase digest digits | The protected runner publishes a complete verified folder before committing its transition | No |

`<course>` is the course name. A runner working in a Git repository MUST list `.agents/records/` and `.agents/course-snapshots/` in `.git/info/exclude`, never in the shared `.gitignore`, so one learner's history is never committed. It MUST NOT list the lock. A workspace that is not a Git repository needs no exclusion.

No lock, event or record holds an answer to a call, a conversation, code, file contents, a credential, a learner identifier or a machine identifier. [Privacy](#privacy) states this as a duty on every field, known or unknown.

## The receipt boundary <a id="receipt-boundary"></a>

A call counts as the learner's only when a runner can show the learner made it. The owner approved the [capability contract for learner-decision receipts](../docs/delivery/call-receipts.md#approved-capability-contract--19-october-2026) on 19 October 2026. Its limits shape this page. A *verifier* trusts a learner-controlled confirmation path that tutor tools cannot alter or invoke. The verifier, its configuration, its transport and its replay protection stay outside tutor authority. A confirmation binds the course snapshot, the lesson, the call and one input occurrence, and cannot be used twice. No answer text, conversation or answer hash may enter a receipt. Each host must qualify its boundary separately, and this specification qualifies none. Unsupported hosts, missing provenance and unqualified boundaries stay **unverified**, and unverified calls cannot settle objectives.

The receipt boundary requires a capability; it specifies no signing scheme or secret format. This page therefore chooses only what the log must hold, and selects no signature or secret format. A verified decision carries a *receipt* of exactly two values.

- `occurrence`: an opaque identifier chosen by the verifier, 22 to 128 characters from `A-Z`, `a-z`, `0-9`, `-` and `_`. It is random, at least 128 bits, and never derived from anything the learner typed, so it cannot reveal or confirm an answer.
- `verifier`: an opaque name for the qualified verifier that issued it, 1 to 128 printable ASCII characters without spaces.

The challenge that the verifier set, and anything it signs, stay inside the verifier and never enter the log. The log holds only what a reader needs to enforce the binding and the one-use rule: the event's own snapshot, lesson and call, and the occurrence. Even these identifiers can correlate activity, so [privacy](#privacy) keeps the records local.

A reader cannot authenticate `verified` from JSON. Qualified replay needs the original protected history and verifier context, including the [durable issuance binding](#operation-admission). An untrusted imported view stays unverified. A qualified host MUST also keep the log's writer out of tutor authority, so that only the runner and verifier can append a learner's decision. On every other host the runner MUST write `unverified` for every learner decision, and a tutor with file access could forge a `verified` line, which is why it never counts.

## Three kinds of validity <a id="validity"></a>

The contract keeps three questions apart. Passing one never answers the next.

| Question | Asked of | Answered by | Failing means |
| --- | --- | --- | --- |
| *Structural validity*: has the line the right shape? | One log line, the record or the lock | The field tables below; a schema can check it | The line is invalid and skipped, or the file is refused |
| *Provenance validity*: was the call the learner's, and verified? | One decision line | `by`, `provenance`, the receipt and the replay rules; the host's qualification | The call stays unverified and cannot settle an objective |
| *Sufficient for settlement*: does everything an objective needs hold? | One objective in one lesson | [Settling objectives](#settling) | The lesson may still pass, but the objective is not settled |

A decision can be structurally valid and unverified. A completed lesson can be valid and settle nothing. An objective settles only when all three questions pass for it.

## The event log <a id="event-log"></a>

### Line format <a id="line-format"></a>

`events.jsonl` is a UTF-8 text file. Each event is one line: a single JSON object, then one line feed (LF, byte `0A`). A line is at most 4096 bytes and has no repeated key. A line that does not follow these rules is invalid. Every line has these two fields.

- `at`: a time, set by the runner when it writes the line.
- `kind`: one of the kinds below, or a name this version does not define.

Events are applied in file order. The `at` value is information, never an ordering: a clock that moves backwards does not reorder the log. A reader MUST ignore a field it does not know. A reader MUST treat a kind it does not know as a valid line that changes nothing, and it never deletes the line. Unknown kinds and fields can never create progress, ownership or settlement.

### Event kinds <a id="event-kinds"></a>

Fields named `lesson`, `call`, `check` are identifiers. Listed fields are required when their condition holds. Unknown fields are ignored, except expressly forbidden fields remain invalid. Every lesson-progress kind also requires the shared fields in the following table; these are not optional abbreviations.

| Kind | Fields | Written when |
| --- | --- | --- |
| `course-started` | `course` (identifier), `version` (the course's version string), `snapshot` (an identity), `source`, Git-only `commit` | The learner begins the course for the first time |
| `project-chosen` | `project` (an object, see [Project](#project-record)) | The project is chosen and prepared |
| `lesson-started` | `lesson` | A lesson begins |
| `step-entered` | `lesson`, `step`: `goal`, `build`, `calls`, `check`, `review` or `explain-back` | The loop moves to a step |
| `call-put` | `lesson`, `call` | A call is put to the learner, including when it is put again |
| `call-decided` | `lesson`, `call`, `by` (`learner` or `tutor`), `snapshot` (an identity); for `by: learner` also `provenance` (`verified` or `unverified`); when `verified`, `receipt` | The call has an answer |
| `check-run` | `lesson`, `check`, `result`: `pass`, `fail`, `error` or `not-run`; when the result is `pass` or `fail`, `evidence`: `checked` or `observed` | A check ran, or could not |
| `hint-given` | `lesson` | The learner is shown a hint |
| `explain-judged` | `lesson`, `met` (integer from 0), `of` (integer from 1, not below `met`) | An explain-back attempt was judged against the rubric |
| `lesson-completed` | `lesson` | The learner moves on from a lesson that passed |
| `lesson-skipped` | `lesson` | The learner moves on without passing |
| `course-upgraded` | `from` (an identity), `to` (an identity), `version`, `source`, Git-only `commit` | The learner explicitly upgraded the course |
| `consent-changed` | `destination` (1 to 253 characters, no spaces), `state`: `granted`, `declined` or `withdrawn`; for `declined`, also `hook` (`rating`, `stuck` or `questions`) and `lesson`; for the other states, neither | The learner answered or withdrew consent |

### Shared field constraints <a id="event-fields"></a>

These constraints complete the event table. Each scalar occurs exactly once when required. Missing required fields, wrong JSON types and forbidden branch fields invalidate the line; they never receive guessed defaults. JSON booleans are not integers.

| Field | Type, limit and presence | Source and failure |
| --- | --- | --- |
| `at`, `kind` | Required strings on every line; `at` is the exact UTC time grammar above; `kind` is non-empty | Runner append time and event kind; the 4096-byte line bound applies to all fields |
| `course`, `lesson`, `call`, `check` | Required identifiers where the kind lists them; 1–64 characters | Verified course declarations; a well-shaped undeclared id is not applied |
| `version` | Required string on both transitions; the [course version grammar](format.md#course-versions) | Verified target `COURSE.md`; mismatch stops the committed transition before output |
| Transition `source` | Required string, at most 2048 characters; exactly `local` or a credential-free Git reference under the [reference grammar](format.md#reference-grammar) | Verified install request; a local path, credential or malformed reference invalidates the line |
| Transition `commit` | Required for a Git source: 40 or 64 lowercase hexadecimal characters; forbidden for `local` | Commit resolved by that install, never invented |
| Transition identity | Start requires `snapshot`; upgrade requires `from` and `to`; each is `sha256:` followed by 64 lowercase hexadecimal digits | Verified source identity; malformed identity invalidates the line before path construction |
| Lesson `snapshot`, `generation` | Required on `lesson-started`, `step-entered`, `call-put`, `call-decided`, `check-run`, `hint-given`, `explain-judged`, `lesson-completed`, `lesson-skipped`; identity and integer ≥ 1 | Protected operation admission, never caller-selected; wrong-current values are not applied before lookup or verification |
| `generation` on a transition or lock | Forbidden; neither carries this field | Derived by counting applied transitions, never supplied by these files |
| `step`, `by`, `provenance`, `result`, `evidence`, `state`, `hook` | Required strings in the exact enumerations and conditional branches above | Protected runner action or qualified verifier result; an unknown enumeration value invalidates the line |
| `met`, `of` | Required integers on `explain-judged`; `0 ≤ met ≤ of`, `of ≥ 1`; no fixed maximum beyond the line size | Admitted judge result; replay additionally checks the verified rubric denominator |
| `receipt` | Exactly `{occurrence, verifier}` on a verified learner decision; both strings with the [receipt limits](#receipt-boundary); forbidden on tutor or unverified decisions | Protected confirmation controller; no additional member or answer payload |
| `project` | Exactly one object on `project-chosen`, with the [project branches](#project-record) | Learner choice and prepared project; no embedded project content |
| `destination` | Required string on consent changes; 1–253 characters, no whitespace | Declared feedback destination; consent grants or withdrawals forbid `hook` and `lesson` |

The exact-integer generation has no fixed maximum and MUST never wrap or be reused. Line size still limits an event's representation. Unknown fields are never copied into the projection; [privacy](#privacy) forbids private payloads even in ignored fields.

Three shape rules apply to `call-decided`, `check-run` and `explain-judged`.

- A tutor decision carries no `provenance` and no `receipt`. A learner decision with `provenance: unverified` carries no `receipt`. A learner decision with `provenance: verified` MUST carry one. A line that breaks these rules is invalid.
- A `check-run` with the result `error` or `not-run` judged nothing, so it carries no `evidence`. `error` means the check itself broke, and `not-run` means it was declined, refused or impossible without a capability.
- `met` is the number of rubric criteria the judge found met, and `of` is the rubric's denominator. The log never holds a verdict. A reader works out whether the attempt passed from the rubric. A runner without the `judge` capability cannot judge an attempt, so it writes no `explain-judged` line. The attempt shows only as the `step-entered` line for `explain-back`.

### Calls and receipts <a id="call-events"></a>

A call has two events. The runner writes `call-put` when it puts the call to the learner, and `call-decided` when the call has an answer. The log records who decided and, for the learner, whether the decision was verified. It never records the answer.

- When the learner decides, `by` is `learner`. The runner writes `provenance: verified` with a receipt only when the [receipt boundary](#receipt-boundary) holds, and otherwise `provenance: unverified`.
- When the learner asks the tutor to choose, `by` is `tutor`, as [the execution contract](execution.md#calls-duties) says. A tutor decision never counts as the learner's.
- A call never put has no `call-put` line, and a call put but not answered has no `call-decided` line after it. Both leave the call unsettled. The first has no entry in the record, and the second is shown as open.
- A call put again after it was decided is open again, and its earlier decision no longer counts. It needs a new decision.

### The recommendation field <a id="followed-field"></a>

The golden course's example record carried a field saying whether the learner followed the tutor's recommendation. No adopted amendment includes it. version 1.0 does not define it. A line that carries a `followed` field, or any other unknown field, is valid, and the field is ignored. It never affects ownership or settlement, and it is not copied into the record. A tutor's recommendation is not a learner decision, and what a recommendation said is part of the conversation, which the record never holds. A later version can add the field without breaking this one, because readers ignore unknown fields.

## The record <a id="record"></a>

`record.json` is the current picture. It is a deterministic function of complete protected history, required verified retained folders and original verifier authority. Missing required inputs stop authoritative reconstruction; no partial record is published. The record holds fixed course metadata and mutable learner progress, kept apart in the table below.

### Fields and where they come from <a id="record-fields"></a>

| Field | Type | Cardinality | Comes from | If missing or malformed |
| --- | --- | --- | --- | --- |
| `spec` | the string `1.0` | exactly one | **Fixed metadata:** the version of this contract | The record is rebuilt |
| `course` | identifier or `null` | exactly one | **Fixed metadata:** `course-started`; `null` until it applies | The record is rebuilt |
| `version` | string or `null` | exactly one | **Fixed metadata:** `course-started`, then `course-upgraded` | The record is rebuilt |
| `snapshot` | identity or `null` | exactly one | **Fixed metadata:** `course-started`, then `course-upgraded` | The record is rebuilt |
| `generation` | integer ≥ 0, no fixed maximum | exactly one | **Derived metadata:** zero before start, one at start, plus one per applied upgrade | The record is rebuilt; never wrap or reuse |
| `history` | list of archived active projections | zero or more entries; list required | **History:** one entry per applied upgrade, in upgrade order | The record is rebuilt |
| `project` | object or `null` | exactly one | **Progress:** the first applied `project-chosen` | The record is rebuilt |
| `position` | `{lesson, step}` or `null` | exactly one | **Progress:** the latest applied `lesson-started` (step `goal`) or `step-entered` | The record is rebuilt |
| `lessons` | object keyed by lesson identifier | zero or more entries | **Progress:** an entry appears only when a `lesson-started` line applies | The record is rebuilt |
| `calls` | list | zero or more entries | **Progress:** `call-put` and `call-decided`, in the order calls were first put | The record is rebuilt |
| `objectives` | list | zero or more entries | **Progress:** only objectives that settled, in the order of their completions and, within one completion, in the lesson's declaration order | The record is rebuilt |
| `consent` | list | zero or more entries | **Progress:** the latest `granted` or `withdrawn` per destination | The record is rebuilt |
| `declined` | list | zero or more entries | **Progress:** each `declined` consent change | The record is rebuilt |

All fields in the table are required, including empty objects and lists. Each entry has these parts. A part not listed does not exist. No record collection has a fixed maximum; each must reflect the entire applied history.

- `lessons.<id>`: `status` (`started`, `passed` or `skipped`), `at` (a time, only for `passed` and `skipped`), `checks` (only if a check event applied; keyed by check identifier, each `{last, runs}`) and `explain` (only after an applied `explain-judged`; the latest applied attempt as `{met, of, passed}`). A lesson with no entry is not started, and no line other than `lesson-started` can give it one.
- `calls[]`: `id`, `lesson`, `state` (`open` or `decided`) and, once decided, `by`; for a learner decision also `provenance`.
- `objectives[]`: `id`, `lesson`, `evidence` (`checked`, `observed` or `explained`), `by` (the check identifier, or `explain-back`), `at` and `snapshot`, the identity the objective settled under.
- `consent[]`: `destination` and `state` (`granted` or `withdrawn`), sorted by destination bytes. `declined[]`: `destination`, `hook` and `lesson`, without repeats.
- `history[]`: exactly `{version, snapshot, generation, position, lessons, calls, objectives}`. These have the active fields' types and cardinalities, with non-null version and snapshot and positive generation. Each is a deep copy immediately before an applied upgrade; no nested history, project or consent copy exists. Objective identities, evidence, declaration order and first completion times remain unchanged.
- `checks.<id>.last` is the most recent result of any kind. `runs` counts the results `pass` and `fail`. A hint, an `error` and a `not-run` are never attempts, so help is never counted as one.

The record has no learner identifier, no percentage and no count of lessons or objectives. Counts, percentages and "lesson 2 of 5" are derived by whoever shows them, never stored. A runner that wants the number of consecutive failures of a check, for the stuck hook, counts the `fail` results since the last `pass` for that check; an `error` or `not-run` neither counts nor resets it. That agrees with [the consent contract](consent.md#payload-fields), where only failures count and a pass resets the count.

The active course is *complete* when its final lesson, the only `demonstrate` lesson, has status `passed`. Completion is derived from the current segment, not stored; an archived final pass does not complete a new generation. Skipped lessons before it do not prevent completion, and they settle nothing.

### Nested field shapes <a id="nested-fields"></a>

The entry descriptions above are closed shapes. The following table supplies their scalar types and conditional presence. A malformed entry requires rebuilding the whole record from trusted inputs.

| Entry | Required parts and limits | Optional or forbidden parts; ordering |
| --- | --- | --- |
| `position` | Exactly `lesson` (identifier), `step` (event step enumeration), or the whole value `null` | Null before a lesson starts and immediately after an upgrade |
| `lessons.<id>` | `status` string from `started`, `passed`, `skipped` | `at` is required exactly for passed/skipped; `checks` and `explain` exist only after their applied events |
| `checks.<id>` | `last` string from the four check results; `runs` non-negative integer without fixed maximum | No other parts; runs counts pass/fail events only |
| `explain` | `met`, `of` integers with event bounds; `passed` boolean derived from the rubric | Exactly the latest applied attempt, including a later failure |
| `calls[]` | `id`, `lesson` identifiers; `state` string, `open` or `decided` | `by` required exactly when decided; `provenance` required exactly for learner decisions; no receipt copied; unique `(lesson,id)`, first-put order |
| `objectives[]` | `id`, `lesson` identifiers; `evidence` from checked/observed/explained; `by` identifier or `explain-back`; `at` time; `snapshot` identity | All required; unique `(lesson,id)` in each segment; completion order then declaration order |
| `consent[]` | `destination` string with event bounds; `state` granted/withdrawn | Unique destination, unsigned UTF-8 destination order |
| `declined[]` | `destination` with event bounds, `hook` rating/stuck/questions, `lesson` identifier | Unique tuple, first-applied order; survives upgrades |

### The project <a id="project-record"></a>

The `project` object records what the learner chose and where it lives, as [the recorded path](format.md#project-path) defines. It never embeds the project's content.

| Field | Present for | Meaning |
| --- | --- | --- |
| `kind` | all | Required string: `own`, `starter`, `git` or `local` |
| `path` | all | Required string: the project root, relative to its base, under the format contract's path rules. A `local` path is never `.` |
| `source` | `git` and `local` | Required string, at most 2048 characters; forbidden otherwise. The reference as the course wrote it. It never holds a credential, as [the reference grammar](format.md#reference-grammar) requires |
| `commit` | `git` only | Required string; forbidden otherwise. The commit the runner resolved once and reuses: 40 or 64 lowercase hexadecimal digits |

All four project branches are closed shapes. A line whose `project` breaks a row above is invalid. Paths follow the linked grammar without an additional maximum here. The selected option MUST exist in verified course metadata; a mismatch is not applied. For a `local` project the source is fixed by the installed snapshot, so no commit is recorded, as [local project folders](format.md#local-projects) say. A second `project-chosen` after the first applied is not applied, because a project does not change during a course.

### Consent <a id="consent-record"></a>

Consent is stored so a refusal survives a closed session. A `granted` change is a yes for one named destination, and a `withdrawn` change ends it. A `declined` change records that a hook was skipped or refused for a lesson, so a runner that resumes mid-lesson does not ask again, as [the consent contract](consent.md#consent-rules) requires. No destination, payload or answer is stored beyond these names, and silence writes nothing, because silence is a no. Withdrawal also discards unsent payloads, which this file never holds.

## The course lock <a id="lock-file"></a>

`.agents/courses.lock` is one JSON object. A team commits it, so it holds no learner data.

```json
{
  "spec": "1.0",
  "courses": [
    {
      "name": "sample-course",
      "version": "1.0.0",
      "source": "gh:example-co/courses@v1.0.0#sample-course",
      "commit": "9f3c2e1a4b5d6c7e8f90a1b2c3d4e5f607182930",
      "identity": "sha256:<64 hexadecimal digits>"
    }
  ]
}
```

Each entry has `name` (the course name, which is also its folder name), `version`, `source` (see below), `identity` and, for a Git source only, `commit`. Names are unique, and entries are sorted by the bytes of the name. `source` is the string `local` when the learner installed a local folder, and otherwise the Git or HTTPS reference as the learner gave it, at most 2048 characters and credential-free as [the reference grammar](format.md#reference-grammar) requires. A local path is never stored: it would put a user name or home folder into a committed file, and a teammate cannot use it. The installed copy and its identity are what resume needs. A learner who wants to reinstall a local folder names the folder again, and its identity is checked as [pinning](identity.md#pinning) says. The lock holds no timestamp, so installing the same course twice writes the same bytes. The runner replaces it atomically, as [atomic replacement](#atomic-record) describes. A reader ignores unknown fields. The identity duties are in [pinning](identity.md#pinning).

### Lock field shapes <a id="lock-fields"></a>

| Field | Required shape | Source and malformed outcome |
| --- | --- | --- |
| Root `spec` | Exactly string `1.0` | Fixed contract version; any other value refuses the file |
| Root `courses` | Required list, possibly empty; no fixed maximum | One entry per installed course; duplicated names or wrong ordering refuse the file |
| Entry `name` | Required identifier, matching retained directory and course name | Verified authored metadata |
| Entry `version` | Required string under the course version grammar | Verified authored metadata |
| Entry `source` | Required string with transition-source constraints | Last committed transition, or the verified install before first start |
| Entry `commit` | Git-only required hexadecimal string with transition-commit constraints; otherwise forbidden | Resolved install commit preserved by the transition |
| Entry `identity` | Required identity string | Recomputed retained target identity; never accepted from a folder label alone |

Malformed locks do not authorise teaching. Recovery may replace the affected entry from complete committed history and verified authored sources. Other courses' entries MUST remain intact; if they cannot be preserved trustworthily, stop rather than guess. Unknown non-private fields are ignored, except the explicitly forbidden `generation` field.

## Replay <a id="replay"></a>

Replay processes complete protected history in file order. It loads authored folders only for transitions that pass the preliminary predicates below. The same complete inputs and original attestation decisions give one projection. A missing required source or authority stops replay without publishing any part of that projection.

### Retained sources <a id="replay-data"></a>

The runner MUST retain each applied start/upgrade folder under `.agents/course-snapshots/<digits>/<course>/` for its event history's lifetime. It copies only identity-included entries, preserving original file bytes, literal link text and empty directories without following links. It excludes Git metadata, generated output, runner state and any learner workspace or private answers. These are authored course files outside `.agents/records/`, not a record payload.

Before constructing a path, require `sha256:` and exactly 64 lowercase hex digits; remove only that prefix for `<digits>`. Require the validated course identifier as the final directory component. Refuse symlink archive components, traversal and any path escaping the retained store. A correctly labelled folder is not proof of its contents.

Before use, recompute the [existing identity](identity.md#identity-digest) and require equality with the transition. Then validate the complete course and its relationships under the [format](format.md) and [execution](execution.md) contracts for its [trusted original candidate](#candidate-provenance), including directory name, course name and version. Hashing and metadata interpretation MUST read the same stable bytes under the protected runner's write boundary. A concurrent change aborts the operation. Read-only permission bits alone are insufficient; tutor control of the log, source verification or verifier cannot establish qualified provenance.

Metadata links MUST resolve wholly within the verified, identity-included tree. Escaping, excluded, cyclic or missing targets make the required source unusable. Identity itself still hashes literal link text without following it. Interpret verified text with the identity text rule once; copying retained folders never rewrites source bytes.

| Transient view | Exact source, type and cardinality | Malformed outcome |
| --- | --- | --- |
| Course name, version, lesson order, project choices | One valid `COURSE.md`; name/version strings; at least one unique ordered lesson id; omitted project means `[own]` | Stop required-source replay |
| Stage, checks, calls, objectives | One valid listed lesson file per id; stage enumeration; check references with default-true boolean `required`; unique call ids; ordered objective `{id, by}` pairs; omitted calls/objectives mean empty | Stop required-source replay |
| Check kind and command | Unique declarations in `COURSE.md` frontmatter `checks`; default `command` or `observe`; command-only required `run` string; every referenced id resolves | Stop required-source replay |
| Explain-back threshold | Exactly the final lesson's rubric; integers `K`, `N` from `K of N`, `1 ≤ K ≤ N`; N equals top-level criteria count | Stop required-source replay |

These views are transient, never persisted independent authorities. Unknown author fields retain the ignore-and-warn policy and cannot change derived fields. There is no replay JSON cache, replay manifest or ninth schema. An [explicit content upgrade](#upgrade-projection) selects a separate authored snapshot, never a metadata cache. A locally restored exact folder may be reused only after identity and structural verification; never fetch or substitute latest content automatically.

### Applying events <a id="applying-events"></a>

Parse each line's structure first. Invalid lines are skipped and reported under [damage](#damage). For structurally valid lines, evaluate these predicates in order; a refused predicate changes no projection field. A report distinguishes invalid, not applied, and a stopped replay.

1. An unknown kind does nothing, and ignored fields never trigger lookup. Remember occurrences on structurally valid verified decision lines for the existing one-use rule, even when a later predicate refuses that line. This requires no folder or receipt verification.
2. A first `course-started` requires its retained folder, verified name and version. Apply it with generation one. A later start is not applied and does not look up its snapshot. Before an applied start, every other known kind is not applied.
3. For `course-upgraded`, compare `from` with the active identity and require `to != from`. Failure is not applied without target lookup. A line passing these predicates is a committed transition: require its verified target, unchanged course name, matching version and compatible selected project option. Failure to load or validate that commitment stops replay, never converts it into a refused live request.
4. For every lesson-progress event, compare both `snapshot` and `generation` with current state before lookup or receipt verification. Either mismatch is not applied. Generation derives only from applied transitions: zero before start, one after start, then one more for each applied upgrade. Lost or truncated committed history stops authoritative resume; it never resets this counter.
5. A named lesson, call or check must be declared by the current verified course and named lesson. Every lesson event except `lesson-started` also needs an already-started entry. No other kind creates that entry. Consent decline requires a declared lesson but does not create or require progress in it.
6. A `call-decided` needs an open call. A verified occurrence seen on an earlier structurally valid verified line is not applied, even if that earlier line was not applied. For an otherwise applicable learner decision, use the [verification contract](#replay-interface); a rejected result leaves the call open, and unverified never settles anything.
7. A passing/failing `check-run` needs the kind's evidence: checked for command, observed for observe. `explain-judged` needs the final lesson and the verified rubric denominator. A different kind or denominator is not applied.
8. A project can be chosen only once and must match a verified offered option. Completion and skip obey their specific rules below. Other applicable kinds update only the fields assigned to them.

An applied `lesson-started` sets status started unless already passed, removes an earlier skip time, and sets position to that lesson at goal. Checks replace `last` and increment `runs` only for pass/fail. Explain-back replaces the latest attempt, including a miss. Hints, invalid lines and unknown kinds never create attempts. An applied upgrade archives and resets exactly as [upgrades](#upgrades) states. A missing, unreadable, changed or malformed required snapshot stops with its identity and reason: no partial projection, lock update, teaching or settlement follows.

### Protected admission and restart <a id="operation-admission"></a>

Before dispatching a check, requesting an explain-back judgement or presenting a call, the protected runner captures current snapshot and generation. It binds them to that operation, its lesson and declared check/call or explain attempt. Callers MUST NOT choose or replace this binding. When the result arrives, compare its original binding with current state under the writer lock used by upgrades, before appending progress. Require the current snapshot/generation and the existing lesson-start, declared-id and attempt rules. Refuse stale results without appending new progress; never relabel them with current values.

The durable upgrade commit invalidates all earlier admissions, even if their processes continue or the same snapshot returns later. After restart, cancel unfinished check/explain operations and require fresh dispatch. Reconstruct no admission from an arriving result. Already-committed results replay from their protected history with their original times. No public operation id or admission journal is added.

The protected confirmation controller MUST durably bind each issued occurrence to its admission generation and the approved snapshot, lesson, call and occurrence bindings before issuing confirmation. Preserve that binding and original attestation for the event history's lifetime, independently of public event fields. An event append cannot qualify an occurrence whose issuance binding is unavailable. An unused occurrence issued in an earlier generation is rejected, including after a return to identical content or a forged current-generation label.

After restart an outstanding confirmation is eligible only if its protected issuance binding is recoverable and current; otherwise request fresh confirmation. Missing provenance is unverified; a known mismatch is rejected. Neither settles an objective. Admission and issuance evidence contain no answer, answer hash or conversation. These generation duties are proposed record policy, not an approval of a receipt format, signing scheme or host.

### Internal replay handoff <a id="replay-interface"></a>

A replay implementation needs complete events, verified retained authored folders, trusted installation context and original receipt authority.
Missing context stops before metadata reads, as [retained provenance](#candidate-provenance) requires.
No public replay library is released. The repository harness exercises controlled fixtures; current-format reader support is still being implemented.

For an otherwise applicable learner decision, the receipt verifier receives the event's zero-based index, the event and replay's derived generation.
It checks the protected issuance generation and original receipt bindings, never treating a public generation label as proof.

The result is exactly `verified`, `unverified` or `rejected`; any other result raises `ContractError`. Missing authority supplies unverified. Known mismatches are rejected. A line already labelled unverified cannot be promoted, even by a verified callback result. Replay checks the original durable attestation without redeeming the occurrence again; identical inputs must reproduce identical outcomes. Loss of previously required verifier authority stops authoritative resume. An untrusted imported view remains unverified and cannot replace authoritative history.

A controlled callback represents an explicitly assumed synthetic authority. It proves neither human provenance nor host qualification. Schemas check event generation shape and record history shape; replay checks equality, derivation and verified sources. Authored-file schemas describe course, lesson, check and rubric shapes. Their structural validity alone does not establish cross-file validity or evidence provenance.

### Completing a lesson <a id="completing"></a>

A `lesson-completed` line applies only when the lesson is not already `passed` and it really passed. A lesson passes when every required check it lists has a latest result of `pass`. A lesson with no required checks, such as an `understand` lesson, passes this check predicate at once. Optional checks do not gate passing. The final lesson also needs its latest applied `explain-judged` to reach the rubric's pass mark: an earlier attempt that met the bar does not count after a later one that did not, and a later one that meets it replaces an earlier miss. A required check that was `not-run` or `error`, or a latest attempt below the bar, means the lesson did not pass, and the completion line is not applied. A runner without a capability a lesson needs cannot record that lesson as passed. It can still teach it, and the learner moving on is recorded as skipped.

The first applied completion sets the status to `passed` and `at` to that line's time. Every later `lesson-completed` for the same lesson is not applied, so a repeated completion neither counts twice nor moves the first time.

### Settling objectives <a id="settling"></a>

Settlement is derived at the moment a completion applies, and it is never an event, so no runner can assert it. Each objective the lesson declares settles when:

1. its own evidence passed: the named check's latest result is pass with its declared evidence kind, even when optional; or the latest explain-back meets the rubric; and
2. every call the lesson declares has state `decided` with `by: learner` and `provenance: verified`; and
3. the lesson was not skipped, which is the case because it is being completed.

A settled objective is added to `objectives` with `at` the completion's time and `snapshot` the current snapshot. One completion can settle several objectives at once. They are added in the order the lesson file declares them, not by name or by the order of their evidence, and a later completion's objectives follow every earlier one. A lesson that declares no calls has nothing to satisfy in the second condition, and zero declared calls is not a missing call. A declared call that is open, absent, decided by the tutor or unverified leaves every objective of that lesson unsettled, while the lesson still passes. A receipt alone never settles anything, because all three conditions are needed, as [the execution contract](execution.md#settlement) says. A settled objective is never discarded: an upgrade moves it unchanged into history. Idempotence and declaration ordering apply separately within each active generation. A later failing check does not unsettle it, because it records what held at completion.

### Skipping <a id="skipping-record"></a>

A `lesson-skipped` line applies only when the lesson is not `passed` and not already `skipped`. It sets the status to `skipped` and `at` to its time. A skipped lesson settles nothing, and it is never shown as passed. A learner who returns to it starts it again, and it then follows the ordinary rules, including passing later. Moving on from a lesson that has passed is not a skip, so a `lesson-skipped` line for a passed lesson is not applied.

## Writing and recovery <a id="recovery"></a>

### Appending <a id="appending"></a>

The protected runner serialises writers per course and for the shared course lock. It checks operation admissions under that same lock. A runner appends each event as one write of the JSON text and its LF to `events.jsonl`, then waits until the operating system confirms the bytes are stored before it acts on the event. If the file does not end with LF, the runner first writes LF so a valid unterminated final line is completed and never merged with the next one. The runner appends before it replaces the record, so a crash between the two leaves history ahead of the record, which replay repairs.

### A partial append and an invalid line <a id="damage"></a>

Two different faults can appear in a log. They are told apart so a crash is not mistaken for damage.

| | Partial append | Invalid historical line |
| --- | --- | --- |
| What it is | The last line has no LF and is not a valid event: a write was interrupted | A line that has an LF, or is not the last line, and is not a valid event |
| Cause | A crash or a full disk during an append | Corruption, an edit or a runner bug |
| How a reader treats it | It is not an event. The reader reports an interrupted write | It is skipped and reported as damage, and the rest of the log still applies |
| What the runner does with the bytes | Moves them unchanged to the end of `events.partial` in the same folder, then cuts the log back to its last LF | Nothing. The line stays where it is and is never edited or removed |
| Effect on the record | None | The line contributes nothing, so a lost decision stays open and a lost completion stays unrecorded; nothing is guessed |

A final line without an LF that is a valid event counts as an event, and the runner completes it with an LF before the next append. A reader never repairs history by guessing a missing event. Silently discarding history is forbidden: partial bytes are set aside, never dropped, and damage is always reported. A runner reports an interrupted write once and damage at every resume.

### Replacing the record <a id="atomic-record"></a>

The runner writes the whole new content to a temporary file in the same folder, waits until it is stored, renames it over `record.json` in one step, then confirms the folder entry is stored. It never edits `record.json` in place, so a reader sees either the whole old file or the whole new one. A leftover temporary file is ignored and may be deleted. The lock is replaced the same way.

### Resuming <a id="resume-record"></a>

When a learner returns, the runner first verifies complete protected history and replays committed transitions from retained sources. If a committed transition left install, lock or record behind, [transition recovery](#transition-durability) completes it. The runner then verifies the installed course against the repaired lock by [pinning duty two](identity.md#pinning), and compares replay with `record.json`. If the file is missing, damaged or different, the replay result replaces it, and the learner is told it was rebuilt. The events win over the record.

- A `record.json` with no `events.jsonl` is not evidence of an empty history. Preserve it as `record.orphaned.json` and stop authoritative resume if committed history is missing. Never reset generation from that loss. A genuinely new course with no prior commitment has empty history; an untrusted imported view cannot authorise new progress.
- With genuinely empty history the result is the initial record, which `record.json` need not exist for: `course`, `version`, `snapshot`, `project` and `position` are `null`, `generation` is zero, `lessons` is empty, and every list, including `history`, is empty.
- The runner resumes at the position's lesson and step. If that lesson is `passed` or `skipped`, it resumes at the first lesson after it, in lesson order, that is neither; with none left, the course has ended. A call that is `open` is put again, and the runner never infers an answer, as [the execution contract](execution.md#resuming) says. A help request after resuming is a `hint-given` line and never an attempt.

## Upgrades and changed content <a id="upgrades"></a>

An unrequested content change is refused without an event. An explicit upgrade is a committed transition only after the target, prior history and project compatibility have been verified. The learner's editable workspace is never replaced. Same-current and refused requests change no install, lock, record or admission.

### Durable transition and recovery <a id="transition-durability"></a>

1. Under the protected writer boundary, verify old history and the complete target. Require unchanged course name and that the selected project option remains offered. Refuse a change of project binding; a retained local source may change while the editable copy remains untouched.
2. Prepare a complete sibling temporary snapshot, preserving included bytes, links and empty directories. Validate it, durably store every file and directory entry, then atomically publish its retained directory. Verify an existing final folder before reuse; never overwrite a conflicting folder or treat a temporary folder as published.
3. Obtain the learner's explicit instruction and durably append the complete start/upgrade event before changing active install, lock or projection. This append is the commit point. It advances the derived generation and invalidates old admissions; result appends cannot bypass that admission check.
4. Materialise the installed copy from the verified retained target. Atomically replace this course's lock entry using transition source/commit and verified metadata, preserving every other entry. Then atomically replace the complete record. Confirm directory writes and teach only when install, lock and last committed transition agree.

A crash before commitment leaves old state authoritative; an orphan published target is unused. A crash after commitment completes the committed target on recovery, without another event, generation increment or history entry. It never overwrites the learner's workspace or changes historical timestamps. Replay derives the counter exactly once, regardless of which replacements finished. Restart also applies the admission and confirmation rules above.

If required bytes, authority or a trustworthy lock cannot be recovered, stop visibly and preserve damaged material. Never publish a partial record, infer a missing transition from a newer lock or silently roll back. An invalid historical line is still reported; evidence of lost committed history additionally blocks authoritative resume. Complete-tail and partial-append handling remains as [damage](#damage) specifies. Atomic replacement states the required durability contract; synthetic cut-point tests do not prove any real filesystem meets it.

### Progress after upgrade <a id="upgrade-projection"></a>

Each applied upgrade appends exactly the previous `{version, snapshot, generation, position, lessons, calls, objectives}` to `history`. It then changes version/snapshot, increments generation, clears lessons/calls/objectives and sets position to null. Keep project, consent and declined-hook records unchanged. Preserve every event and archived outcome, including skipped and unfinished work. Historical achievements keep their original evidence, identity, order and first completion time.

Only the fresh active segment can complete lessons or settle objectives under the new content. Every new check, explain-back and call needs new evidence. Previously passed lessons receive no automatic credit; matching ids imply no equivalence. The first new lesson waits for its normal learner gate. Null position neither starts it nor creates an attempt. Used occurrences remain used; unused ones keep their original issuance generation.

Returning from old to new to old creates generations one, two and three with two ordered history entries. It never restores generation-one admissions. Asking for the already-current identity is a no-op: no transition, history entry or reset, and otherwise valid current admissions survive. An unavailable, invalid or incompatible target is likewise refused before commitment, without changing active files or workspace. A broken target named by a committed transition instead stops recovery.

Changed `run` strings MUST be disclosed again under the [execution contract](execution.md#command-display). Old check results never substitute for a new run. Required checks gate passing; each objective still needs its own passing evidence, including an optional check it names. Zero declared calls, latest explain-back, declaration-order settlement and completion idempotence retain their meanings within each active segment.

## Privacy <a id="privacy"></a>

A runner MUST NOT put any of these in any field of the lock, the record, operation/issuance evidence or an event, whether the field is defined here or not: an answer to a call, text of a conversation, project code or file contents, a hash or other digest of any of those, a credential, a learner identifier, or a machine identifier. The only digests allowed are course identities, which hash course files, and a receipt's `occurrence` is random, not a digest. A hash of a short private answer is easy to guess, so it is no substitute for leaving the answer out.

The records still hold timing and the learner's choices of lesson and project, and receipt identifiers can correlate activity. They stay local, are excluded from Git history, and are never sent anywhere by this contract. A host may keep prompt histories of its own, which no runner can remove. Feedback hooks send their own closed payload, as [the consent contract](consent.md#payload-fields) defines, and never a record.

## Schemas, names and status <a id="status"></a>

### Schema addresses <a id="schema-addresses"></a>

The candidate defines eight machine-readable types for later publication: `course`, `lesson`, `checks`, `feedback`, `lock`, `record`, `event` and `rubric`. The lock, the record and one event line are described by the `lock`, `record` and `event` schemas. One `event` schema covers every kind, and `kind` selects the rules. It covers transition source/commit and lesson snapshot/generation; `record` covers derived generation and history. No generation field belongs to a transition or lock. Retained folders use existing authored-file schemas, not an additional replay schema.

Each type has the address `https://agentcourses.io/schemas/<candidate>/<type>.schema.json`, where `<candidate>` is the candidate label. The current format label is `1.0.0-rc.2`. The schema and consumer implementation for this format is not yet available. The repository manifest lists the schema bytes that actually exist; it does not establish support for these declarations. An address, once published, never changes its bytes, and changed bytes need a new candidate label and a new address. A schema address is available only when its exact bytes appear in the published inventory. Do not infer availability from the address pattern.

### Names <a id="names"></a>

The contract names only what a reader needs to follow its rules.

| Thing | Name | Status |
| --- | --- | --- |
| The specification | Agent Courses | Named here |
| Its version | `1.0`, in `spec` fields; the candidate label is `1.0.0-rc.2` | Named here |
| The home and schema host | `agentcourses.io` | Decided by the owner |
| The repository | `agentcourses/agentcourses` | Existing |
| Files and folders | `COURSE.md`, `.agents/courses/`, `.agents/courses.lock`, `.agents/records/<course>/`, `.agents/course-snapshots/` | Named here and in [the format contract](format.md#folder-layout) |
| A command, library or package | None | Not part of this contract; chosen at release, after a check that the names are free ⚠️ unverified |

### Candidate and stable <a id="candidate-and-stable"></a>

This specification is a *candidate* when the owner accepts the published snapshot and its manifest after independent review. The candidate bar is that no contract question is unassigned, the rules have cases, the internal checks pass, and the text makes no claim about hosts, packages or stability. Accepting it qualifies no host and no runner.

A *stable* 1.0.0 is a later step. It belongs to a launch qualification that follows this candidate: a host whose confirmation boundary is qualified, a beginner pilot with real learners and published packages. This candidate sets no pass mark for that step. Until it is met, no runner, course or document may claim stability or conformance.

## Worked traces <a id="traces"></a>

These traces use the current format with explicitly assumed trusted installation provenance. They illustrate learner progress, protected confirmations and deliberate course-content upgrades. Synthetic authority qualifies no host.

Each trace gives a log and the record a reader derives from it. They use one *trace course*: the extended baseline from [the format contract](format.md#baseline-course), where `make.md` also declares the objective `agent-runs-ok` by the check `agent-runs`. The rubric is `pass: 2 of 3`.

| Lesson | Stage | Checks | Calls | Objectives |
| --- | --- | --- | --- | --- |
| `intro` | understand | none | `choose-tool` | none |
| `make` | build | `agent-runs` (observe) | none | `agent-runs-ok` by `agent-runs` |
| `finish` | demonstrate | `final-check` (command) | `choose-check` | `agent-passes` by `final-check`, `agent-explained` by `explain-back` |

In a trace table each line is a JSON object with `at` and `kind` first, written `2026-10-21T<time>Z`. Where a field's value is long, a name stands for it: `S1` and `S2` are the verified identities of the complete trace trees defined below, `O1` is `q7Zk2mR9xT4vB1nC8dLw5A`, and `O2` is `Hs3Fp0yU6eJg2KtN7oVb1Q`. A receipt is `{occurrence, verifier: example-verifier}`. Every lesson-progress line explicitly expands to `snapshot=S1 generation=1` unless stated otherwise. Every transition expands to `source=local` and has no `commit` or `generation`; these defaults are part of the complete input, not permission to omit required fields. Every other field is written `name=value`. Verified examples assume a protected synthetic issuance binding for the stated generation and original receipt; they qualify no host.

### Complete trace inputs <a id="trace-inputs"></a>

The complete authored tree below fixes every input byte for the worked traces. Each fenced file ends in one LF. It is the accepted extended format baseline with a declared make objective and concrete check fixtures; it is not the identity-vector toy tree. The initial course identity is `sha256:90ff48e14065e76a9458f4c3bf1e55d7ec8939a3149c59b0bf3b5187cd2bdabb`. Its content upgrade identity is `sha256:ba134c024eb47ba99bf6396de60dab35dee52ef189c63275e6d74e3634446182`.

`S1` names this tree. `S2` is a copy with exactly two replacements: `COURSE.md` version `"1.0.0"` becomes `"1.1.0"`, and the central check command in `COURSE.md` changes from `python "$AGENT_COURSE_DIR/scripts/final_check.py"` to `python "$AGENT_COURSE_DIR/scripts/final_check.py" --strict`. The check implementation still accepts that argument; the changed command must nevertheless be disclosed. All other bytes remain identical. Variant trees state their precise edit and must use their own recomputed identities, never S1 or S2's folder labels.

<details><summary>Exact authored files for sample-course</summary>

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
  - id: agent-runs
    kind: observe
    verify: agent.py exists and defines an agent
---

# Sample course

You'll build a small agent.

## Outcome

`agent.py`: an agent that passes `final-check`.

## Lessons

1. [Meet the agent](lessons/intro.md)
2. [Make the agent](lessons/make.md)
3. [Finish and explain](lessons/finish.md)
```

`scripts/final_check.py`:

```python
from pathlib import Path
raise SystemExit(0 if "agent" in Path("agent.py").read_text() else 1)
```

`scripts/fixtures/final-check/fail/agent.py`:

```python
value = None
```

`scripts/fixtures/final-check/pass/agent.py`:

```python
agent = object()
```

`lessons/finish.md`:

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

`lessons/intro.md`:

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

`lessons/make.md`:

```markdown
---
title: Make the agent
stage: build
checks: [agent-runs]
objectives:
  - id: agent-runs-ok
    text: The agent runs
    by: agent-runs
---

## Goal

Your agent runs.

## Build

Ask the learner how to start the agent, then create `agent.py` with them.
```

`tutor/finish.rubric.md`:

```markdown
---
pass: 2 of 3
---
- **Names the output type** and says why a typed result is safer than prose
- **Describes the tool call**: what triggers it and what it returns
- **Names one failure mode** and how the checks would catch it
```

</details>

### The shared opening <a id="trace-opening"></a>

| Line | Time | Event |
| --- | --- | --- |
| 1 | 09:00:00 | `course-started` course=sample-course version=1.0.0 snapshot=S1 |
| 2 | 09:00:05 | `project-chosen` project={kind: own, path: .} |
| 3 | 09:01:00 | `lesson-started` lesson=intro |
| 4 | 09:01:05 | `step-entered` lesson=intro step=goal |
| 5 | 09:02:00 | `call-put` lesson=intro call=choose-tool |
| 6 | 09:03:00 | `call-decided` lesson=intro call=choose-tool by=learner provenance=verified receipt={O1} snapshot=S1 |
| 7 | 09:04:00 | `lesson-completed` lesson=intro |
| 8 | 09:05:00 | `lesson-started` lesson=make |
| 9 | 09:06:00 | `check-run` lesson=make check=agent-runs result=fail evidence=observed |
| 10 | 09:08:00 | `check-run` lesson=make check=agent-runs result=pass evidence=observed |
| 11 | 09:09:00 | `lesson-completed` lesson=make |

The record after line 11, where `<S1>` stands for `S1`:

```json
{
  "spec": "1.0",
  "course": "sample-course",
  "version": "1.0.0",
  "snapshot": "<S1>",
  "generation": 1,
  "history": [],
  "project": { "kind": "own", "path": "." },
  "position": { "lesson": "make", "step": "goal" },
  "lessons": {
    "intro": { "status": "passed", "at": "2026-10-21T09:04:00Z" },
    "make": {
      "status": "passed",
      "checks": { "agent-runs": { "last": "pass", "runs": 2 } },
      "at": "2026-10-21T09:09:00Z"
    }
  },
  "calls": [
    { "id": "choose-tool", "lesson": "intro", "state": "decided", "by": "learner", "provenance": "verified" }
  ],
  "objectives": [
    { "id": "agent-runs-ok", "lesson": "make", "evidence": "observed", "by": "agent-runs",
      "at": "2026-10-21T09:09:00Z", "snapshot": "<S1>" }
  ],
  "consent": [],
  "declined": []
}
```

Line 1 sets the course and snapshot. Line 2 sets the project. Lines 3 to 6 start `intro` and record its call as decided by the learner and verified, and line 7 passes it because it lists no checks. Lines 8 to 11 run the check twice, so `runs` is 2 and `last` is `pass`, and pass `make`. `make` declares no calls, so its objective settles at line 11. The position is the latest `lesson-started`, which is `make` at step `goal`. The time of the passed lessons is the completion line's time.

### The finishing lesson <a id="trace-finish"></a>

These lines follow the opening. Each variant changes line 14 only, except *Never put*, which also removes line 13.

| Line | Time | Event |
| --- | --- | --- |
| 12 | 09:10:00 | `lesson-started` lesson=finish |
| 13 | 09:11:00 | `call-put` lesson=finish call=choose-check |
| 14 | 09:12:00 | the call line, which each variant below sets |
| 15 | 09:15:00 | `check-run` lesson=finish check=final-check result=pass evidence=checked |
| 16 | 09:16:00 | `step-entered` lesson=finish step=explain-back |
| 17 | 09:18:00 | `explain-judged` lesson=finish met=2 of=3 |
| 18 | 09:19:00 | `lesson-completed` lesson=finish |

The base result for the finishing lesson is the opening record with these changes: `position` is `finish` at `explain-back`; `lessons.finish` is `{status: passed, checks: {final-check: {last: pass, runs: 1}}, explain: {met: 2, of: 3, passed: true}, at: 2026-10-21T09:19:00Z}`; and a call entry for `choose-check` is added. The objectives change in each variant.

| Variant of line 14 | `choose-check` entry | Objectives after line 18 |
| --- | --- | --- |
| <a id="trace-learner-verified"></a>**Learner, verified.** `call-decided` lesson=finish call=choose-check by=learner provenance=verified receipt={O2} snapshot=S1 | decided, learner, verified | `agent-runs-ok`, `agent-passes` and `agent-explained`, the last two at 09:19:00 with evidence `checked` and `explained` |
| <a id="trace-tutor-call"></a>**Tutor decided.** `call-decided` lesson=finish call=choose-check by=tutor snapshot=S1 | decided, tutor | `agent-runs-ok` only |
| <a id="trace-unverified-call"></a>**Learner, unverified.** `call-decided` lesson=finish call=choose-check by=learner provenance=unverified snapshot=S1 | decided, learner, unverified | `agent-runs-ok` only |
| <a id="trace-open-call"></a>**Put, never answered.** Line 14 is absent | open | `agent-runs-ok` only |
| <a id="trace-missing-call"></a>**Never put.** Lines 13 and 14 are both absent | no entry | `agent-runs-ok` only |
| <a id="trace-replayed-receipt"></a>**Repeated receipt.** `call-decided` lesson=finish call=choose-check by=learner provenance=verified receipt={O1} snapshot=S1 | open: line 14 is not applied because `O1` was used at line 6 | `agent-runs-ok` only |
| <a id="trace-binding-snapshot"></a>**Wrong snapshot.** The learner decision with receipt={O2} and snapshot=S2 | open: line 14 is not applied because it names another snapshot | `agent-runs-ok` only |
| <a id="trace-binding-lesson"></a>**Wrong lesson.** The learner decision with receipt={O2} but lesson=make | open: line 14 is not applied because `make` does not declare `choose-check` | `agent-runs-ok` only |

In *Learner, verified*, `agent-passes` is added before `agent-explained`, the order `finish.md` declares them. Name order would put `agent-explained` first, and neither the order of the evidence nor name order is used.

In every variant the lesson `finish` passes, because its check passed and the explain-back met 2 of 3. Calls decide only settlement. In the last three variants the line is reported as not applied, and nothing in the record shows it. If a call is missing, `agent-passes` and `agent-explained` stay unsettled, and `agent-runs-ok` stays settled because `make` declares no calls.

### Other traces <a id="trace-others"></a>

Each trace below starts again from the stated line. Lines are numbered continuing from there.

| Trace | Lines | What a reader derives |
| --- | --- | --- |
| <a id="trace-empty"></a>**Empty history** | The log is empty or absent | The initial record: `course`, `version`, `snapshot`, `project` and `position` are `null`, `lessons` is `{}`, `generation` is zero, and `history`, `calls`, `objectives`, `consent` and `declined` are empty lists. No attempt, completion or objective exists |
| <a id="trace-skip"></a>**Skip** | Lines 1 to 7, then 08 `lesson-started` make, 09 `check-run` make agent-runs fail observed, 10 `lesson-skipped` make (09:07:00) | `make` is `skipped` at 09:07:00 with `agent-runs` last `fail`, runs 1. `objectives` is empty. It is never `passed` |
| <a id="trace-skip-return"></a>**Skip, then pass** | The skip trace, then 11 `lesson-started` make (09:30:00), 12 `check-run` make agent-runs pass observed (09:31:00), 13 `lesson-completed` make (09:32:00) | `make` is `passed` at 09:32:00 with runs 2, and `agent-runs-ok` settles at 09:32:00. The earlier skip leaves no mark |
| <a id="trace-skip-after-pass"></a>**Skip a passed lesson** | The opening, then 12 `lesson-skipped` make | Line 12 is not applied. `make` stays `passed` at 09:09:00 |
| <a id="trace-repeated-completion"></a>**Repeated completion** | The opening, then 12 `lesson-completed` make (09:09:30), 13 `lesson-completed` make (09:40:00) | Both lines are not applied. `make` stays `passed` at 09:09:00 and `agent-runs-ok` is listed once, at 09:09:00 |
| <a id="trace-no-evidence"></a>**Completion without evidence** | Lines 1 and 2, then 03 `lesson-started` make, 04 `check-run` make agent-runs fail observed, 05 `lesson-completed` make | Line 5 is not applied. `make` is `started` with runs 1. The runner should have written `lesson-skipped` |
| <a id="trace-not-run"></a>**Check not run** | Lines 1 and 2, then 03 `lesson-started` make, 04 `check-run` make agent-runs result=not-run (no evidence), 05 `lesson-completed` make, 06 `lesson-skipped` make (09:08:00) | Line 5 is not applied. `make` is `skipped` at 09:08:00, with `agent-runs` last `not-run` and runs 0. Nothing settles |
| <a id="trace-hints"></a>**Help is not an attempt** | Lines 1 and 2, then 03 `lesson-started` make, 04 `check-run` fail, 05 `hint-given`, 06 `hint-given`, 07 `check-run` fail | `make` is `started` with `agent-runs` last `fail`, runs 2. The hints changed nothing |
| <a id="trace-interrupted-write"></a>**Interrupted write** | The opening lines, then the bytes `{"at":"2026-10-21T09:10:0` with no LF | The reader derives the opening record and reports an interrupted write. The runner moves those bytes to `events.partial`, cuts the log back to line 11 and appends the next line cleanly |
| <a id="trace-complete-tail"></a>**Valid tail without LF** | The opening lines, where line 11 is complete JSON but lacks its LF | Line 11 counts, so the result is the opening record. The runner writes an LF before it appends |
| <a id="trace-invalid-line"></a>**Invalid historical line** | The opening, with line 6 replaced by a terminated line whose `call-decided` lacks `by` | The result is the opening record except that `choose-tool` is `open`, because the decision was lost and nothing guesses it. `intro` still passes, because calls do not gate passing. The damage is reported at every resume |
| <a id="trace-unknown-kind"></a>**Unknown kind and unknown field** | The opening, then 12 a line of kind `mood-noted`, 13 a `hint-given` line for `make` with an extra field `extra` | Both lines are valid. Neither changes the record, and the extra field is not copied |
| <a id="trace-rebuild"></a>**Damaged record** | The opening lines, and a `record.json` that says `finish` is `passed` and lists all three objectives | The replay result is the opening record, with `finish` absent and one objective. It replaces the file, and the learner is told. The events win |
| <a id="trace-upgrade"></a>**Explicit upgrade** | The opening, then 12 `course-upgraded` from=S1 to=S2 version=1.1.0 (10:00:00) | `version` is `1.1.0`, `snapshot` is `S2`, generation is 2, position is null, and active lessons/calls/objectives are empty. History contains the opening segment at generation 1, including `agent-runs-ok` with its original `S1` and 09:09:00 time. Project and consent remain unchanged |
| <a id="trace-changed-content"></a>**Changed content** | The opening log. The installed folder was edited, so its identity is not `S1`; the lock still says `S1` | No line is written and the record is unchanged. The runner refuses to teach and tells the learner |
| <a id="trace-consent"></a>**Consent** | Lines 1 and 2, then 03 `consent-changed` destination=feedback.example.com state=granted, 04 the same destination state=withdrawn, 05 `consent-changed` destination=other.example.net state=declined hook=rating lesson=make | `consent` is one entry, `{destination: feedback.example.com, state: withdrawn}`. `declined` is one entry, `{destination: other.example.net, hook: rating, lesson: make}` |
| <a id="trace-not-started"></a>**Lines before `lesson-started`** | Lines 1 and 2, then 03 `check-run` make agent-runs pass observed, 04 `lesson-completed` make, 05 `step-entered` make step=build, 06 `explain-judged` finish met=3 of=3, then 07 `lesson-started` make, 08 `check-run` make agent-runs pass observed (09:06:00), 09 `lesson-completed` make (09:07:00) | Lines 3 to 6 are not applied, because no `lesson-started` has applied for their lessons, and they leave no trace. The result has one lesson, `make`, `passed` at 09:07:00 with `agent-runs` last `pass`, runs 1 (not 2), position `make` at `goal`, and `agent-runs-ok` settled |
| <a id="trace-explain-latest-miss"></a>**Two attempts, the later one misses** | The opening, then 12 `lesson-started` finish, 13 `call-put` choose-check, 14 the learner-verified `call-decided` with receipt={O2}, 15 `check-run` final-check pass checked, 16 `step-entered` explain-back, 17 `explain-judged` met=2 of=3 (09:18:00), 18 `explain-judged` met=1 of=3 (09:19:00), 19 `lesson-completed` finish (09:20:00) | Line 19 is not applied, because the latest attempt, 1 of 3, is below the bar of 2. `finish` is `started`, `explain` is `{met: 1, of: 3, passed: false}`, and no objective settles beyond `agent-runs-ok` |
| <a id="trace-explain-latest-pass"></a>**Two attempts, the later one passes** | The same lines, with line 17 `met=1 of=3` and line 18 `met=2 of=3` | Line 19 is applied. `finish` is `passed` at 09:20:00 and `explain` is `{met: 2, of: 3, passed: true}`. `objectives` is `agent-runs-ok` (09:09:00), then `agent-passes` and `agent-explained` (both 09:20:00), in the order `finish.md` declares them |
| <a id="trace-upgrade-resume"></a>**Resume after an upgrade** | Opening, then `course-upgraded` from=S1 to=S2 version=1.1.0 source=local at 10:00:00. Then `check-run` make agent-runs pass observed snapshot=S1 generation=1 at 10:01:00, and `lesson-started` finish snapshot=S2 generation=2 at 10:02:00. Both retained folders are present | The stale check is not applied before lookup. The active record is generation 2, position finish/goal, lessons `{finish: {status: started}}`, no active calls/objectives. History holds exactly the generation-one opening segment; old make evidence and 09:09:00 time remain unchanged |
| <a id="trace-missing-replay"></a>**Missing retained source** | Same log, but remove the retained S1 folder | Replay stops at the first commitment, names S1 and its missing source, writes no record/lock, and permits no teaching or settlement. Restore the exact authored folder and verify it before replay; then the preceding trace reproduces |

## Record cases <a id="example-records"></a>

These cases use the trace course. Where a case names a trace, its result is the one that trace states.

| Case | Baseline and change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-receipt-verified-accepted"></a>Verified decision on a qualified host | A host whose boundary is qualified; the runner writes `by=learner provenance=verified receipt={O2}` and the receipt holds only `occurrence` and `verifier` | Record structure | Accepted | A verified decision carries a receipt of exactly two values |
| <a id="case-receipt-unqualified-accepted"></a>Unqualified host | The same call on a host with no qualified boundary; the runner writes `provenance=unverified` and no receipt | Record structure | Accepted | Without a shown boundary every learner decision is unverified |
| <a id="case-receipt-unqualified-verified-rejected"></a>Unqualified host claims verified | The same host; the runner writes `provenance=verified` | Runner behaviour | Rejected | A runner MUST write `unverified` unless the boundary is qualified |
| <a id="case-receipt-answer-rejected"></a>Receipt holds the answer | The receipt has a third value holding the learner's typed answer | Runner behaviour | Rejected | No answer text may enter a receipt or any field |
| <a id="case-receipt-answer-hash-rejected"></a>Occurrence is an answer hash | The `occurrence` is the SHA-256 of the typed answer | Runner behaviour | Rejected | An occurrence is random and never derived from anything the learner typed |
| <a id="case-receipt-unverified-with-receipt-rejected"></a>Unverified with a receipt | `by=learner provenance=unverified` with a receipt | Record structure | Rejected | Only A verified decision carries a receipt |
| <a id="case-receipt-verified-without-rejected"></a>Verified without a receipt | `by=learner provenance=verified` and no receipt | Record structure | Rejected | A verified decision MUST carry a receipt |
| <a id="case-receipt-tutor-provenance-rejected"></a>Tutor decision with provenance | `by=tutor provenance=verified` | Record structure | Rejected | A tutor decision carries no provenance and no receipt |
| <a id="case-receipt-short-occurrence-rejected"></a>Short occurrence | A receipt whose `occurrence` has 8 characters | Record structure | Rejected | An occurrence has 22 to 128 characters |
| <a id="case-receipt-repeated-rejected"></a>Receipt used twice | See [Repeated receipt](#trace-replayed-receipt) | Record replay | Rejected | A seen `occurrence` makes the later line not applied |
| <a id="case-receipt-binding-rejected"></a>Receipt bound elsewhere | See [Wrong snapshot](#trace-binding-snapshot) and [Wrong lesson](#trace-binding-lesson) | Record replay | Rejected | A decision for another snapshot or lesson is not applied |
| <a id="case-files-placement-accepted"></a>Records excluded, lock shared | A Git workspace; the runner lists `.agents/records/` in `.git/info/exclude` and leaves the lock committed | Runner behaviour | Accepted | Records are personal and the lock is shared |
| <a id="case-files-gitignore-rejected"></a>Records ignored for everyone | The runner adds `.agents/records/` to the shared `.gitignore` | Runner behaviour | Rejected | Exclusion uses `.git/info/exclude`, never the shared file |
| <a id="case-files-lock-excluded-rejected"></a>Lock excluded | The runner lists `.agents/courses.lock` in `.git/info/exclude` | Runner behaviour | Rejected | The lock MUST NOT be excluded |
| <a id="case-line-valid-accepted"></a>A valid line | `{"at":"2026-10-21T09:00:00Z","kind":"lesson-started","lesson":"intro","snapshot":"sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","generation":1}` followed by LF | Record structure | Accepted | One object, a time, a kind and the kind's fields |
| <a id="case-line-time-rejected"></a>Time with a fraction | The same line with `"at":"2026-10-21T09:00:00.5Z"` | Record structure | Rejected | A time has no fractions |
| <a id="case-line-duplicate-key-rejected"></a>Repeated key | The same line with `"lesson"` written twice | Record structure | Rejected | A line has no repeated key |
| <a id="case-line-long-rejected"></a>Line over 4096 bytes | The same line padded with an unknown field to 5000 bytes | Record structure | Rejected | A line is at most 4096 bytes |
| <a id="case-line-unknown-kind-accepted"></a>Unknown kind | See [Unknown kind and unknown field](#trace-unknown-kind) | Record replay | Accepted | A reader keeps an unknown kind and it changes nothing |
| <a id="case-line-unknown-progress-rejected"></a>Unknown kind creates progress | A line of kind `lesson-finished` makes `make` passed | Record replay | Rejected | An unknown kind never creates progress |
| <a id="case-line-unknown-field-copied-rejected"></a>Unknown field copied | The reader copies `extra` into the record | Record replay | Rejected | Unknown fields are ignored and not copied |
| <a id="case-followed-ignored-accepted"></a>Followed field ignored | A `call-decided` line with `followed=recommendation` | Record replay | Accepted | The field is not defined, so it is ignored and the call is judged without it |
| <a id="case-followed-settles-rejected"></a>Followed field affects settlement | A runner treats `followed=recommendation` as making the call verified | Runner behaviour | Rejected | An unknown field never affects ownership or settlement |
| <a id="case-project-own-accepted"></a>Own project | `project={kind: own, path: .}` | Record structure | Accepted | An own project records its base path |
| <a id="case-project-git-accepted"></a>Git project | `project={kind: git, path: services/api, source: gh:example-co/payments@v3.4.0#services/api, commit: 9f3c2e1a4b5d6c7e8f90a1b2c3d4e5f607182930}` | Record structure | Accepted | A Git project records its source and resolved commit |
| <a id="case-project-local-accepted"></a>Local project | `project={kind: local, path: work/local-app, source: ./examples/app}` | Record structure | Accepted | The copy is recorded and no commit is invented |
| <a id="case-project-git-no-commit-rejected"></a>Git project without a commit | The Git project without `commit` | Record structure | Rejected | A Git project needs its resolved commit |
| <a id="case-project-own-commit-rejected"></a>Own project with a commit | `project={kind: own, path: ., commit: 9f3c2e1a4b5d6c7e8f90a1b2c3d4e5f607182930}` | Record structure | Rejected | Only a Git project records a commit |
| <a id="case-project-local-dot-rejected"></a>Local project at the base | `project={kind: local, path: ., source: ./examples/app}` | Record structure | Rejected | A local destination is a child path, not the base |
| <a id="case-project-credential-rejected"></a>Credential in the source | `project={kind: git, ..., source: git+https://user:token@git.example.com/team/repo.git}` | Record structure | Rejected | A source never holds a credential |
| <a id="case-lock-git-accepted"></a>Lock entry for a Git source | An entry with `name`, `version`, `source`, `commit` and `identity` | Record structure | Accepted | A Git source records its commit and identity |
| <a id="case-lock-local-accepted"></a>Lock entry for a local source | An entry with `source: local`, an `identity` and no `commit` | Record structure | Accepted | A local install stores the word `local`, never a path, and has no commit |
| <a id="case-lock-local-absolute-rejected"></a>Absolute home path as the source | An entry with `source: /Users/ada/courses/sample-course` | Record structure | Rejected | A local path is never stored, because it would put a user name into a committed file |
| <a id="case-lock-local-relative-rejected"></a>Relative or home-relative path as the source | An entry with `source: ./courses/sample-course`, another with `../courses/sample-course` and another with `~/courses/sample-course` | Record structure | Rejected | The only local `source` is `local`; any path is refused |
| <a id="case-lock-local-reinstall-accepted"></a>Local reinstall | A learner reinstalls a local folder: the lock still says `local`, the learner names the folder again, and its identity is compared with the entry | Runner behaviour | Accepted | The lock needs no path, and identity still decides whether the folder is the pinned course |
| <a id="case-lock-duplicate-rejected"></a>Two entries for one course | Two entries named `sample-course` | Record structure | Rejected | Names are unique in the lock |
| <a id="case-lock-identity-rejected"></a>Short identity | An entry whose `identity` is `sha256:1234` | Record structure | Rejected | An identity is `sha256:` and 64 hexadecimal digits |
| <a id="case-record-counts-accepted"></a>No stored counts | The opening record, which holds statuses only | Record structure | Accepted | Counts and percentages are derived, never stored |
| <a id="case-record-counts-rejected"></a>Counts stored | The record also holds `"lessons_passed": 2` and `"percent": 66` | Record structure | Rejected | Counts and percentages are never stored |
| <a id="case-record-learner-id-rejected"></a>Learner identifier stored | The record holds an opaque `learner` value | Record structure | Rejected | The record holds no learner identifier |
| <a id="case-record-complete-accepted"></a>Complete after the final lesson | The base finishing result, with `finish` passed | Record replay | Accepted | A course is complete when its final lesson has passed |
| <a id="case-record-complete-rejected"></a>Complete with the final lesson skipped | The opening with `finish` skipped | Record replay | Rejected | A skipped final lesson does not complete the course |
| <a id="case-settle-all-accepted"></a>Settled with everything verified | See [Learner, verified](#trace-learner-verified) | Record replay | Accepted | Passed evidence, verified learner calls and no skip settle every objective |
| <a id="case-settle-tutor-rejected"></a>Tutor call settles | See [Tutor decided](#trace-tutor-call) | Record replay | Rejected | A tutor decision leaves the lesson's objectives unsettled |
| <a id="case-settle-unverified-rejected"></a>Unverified call settles | See [Learner, unverified](#trace-unverified-call) | Record replay | Rejected | An unverified decision leaves them unsettled |
| <a id="case-settle-open-rejected"></a>Open call settles | See [Put, never answered](#trace-open-call) | Record replay | Rejected | A call put but not answered leaves them unsettled |
| <a id="case-settle-missing-rejected"></a>Missing call settles | See [Never put](#trace-missing-call) | Record replay | Rejected | A call never put leaves them unsettled |
| <a id="case-settle-zero-calls-accepted"></a>Zero declared calls | The opening record, where `make` declares no calls | Record replay | Accepted | A lesson that declares no calls has nothing to satisfy, so its objective settles |
| <a id="case-settle-event-rejected"></a>Settlement written as an event | A line of kind `objective-settled` for `agent-passes` | Record replay | Rejected | Settlement is derived; no event creates it |
| <a id="case-settle-later-failure-accepted"></a>A later failure | After the learner-verified trace, a later `check-run` of `final-check` fails | Record replay | Accepted | The settled objectives stay, because they record what held at completion |
| <a id="case-complete-repeat-rejected"></a>Repeated completion | See [Repeated completion](#trace-repeated-completion) | Record replay | Rejected | A later completion is not applied and the first time stays |
| <a id="case-complete-unproven-rejected"></a>Completion without evidence | See [Completion without evidence](#trace-no-evidence) | Record replay | Rejected | A lesson passes only when its checks passed |
| <a id="case-complete-capability-accepted"></a>Check could not run | See [Check not run](#trace-not-run) | Record replay | Accepted | The lesson is recorded as skipped, never as passed |
| <a id="case-skip-recorded-accepted"></a>Skip recorded as skipped | See [Skip](#trace-skip) | Record replay | Accepted | A skip remains a skip and settles nothing |
| <a id="case-skip-passed-rejected"></a>Skip recorded as passed | Line 10 of the skip trace is `lesson-completed` and a reader treats the lesson as passed | Record replay | Rejected | A completion without passing evidence is not applied |
| <a id="case-skip-return-accepted"></a>Skipped lesson passed later | See [Skip, then pass](#trace-skip-return) | Record replay | Accepted | A returning learner passes by the ordinary rules |
| <a id="case-skip-passed-lesson-rejected"></a>Skipping a passed lesson | See [Skip a passed lesson](#trace-skip-after-pass) | Record replay | Rejected | Moving on from a passed lesson is not a skip |
| <a id="case-help-not-attempt-accepted"></a>Hints are not attempts | See [Help is not an attempt](#trace-hints) | Record replay | Accepted | Help never adds to `runs` |
| <a id="case-empty-initial-accepted"></a>Empty history | See [Empty history](#trace-empty) | Record replay | Accepted | An empty log gives the initial record |
| <a id="case-empty-invented-rejected"></a>Invented progress from nothing | A runner answers an empty log with a first lesson `started` and a settled objective | Record replay | Rejected | An empty history has no attempt, completion or objective |
| <a id="case-recovery-partial-accepted"></a>Interrupted write | See [Interrupted write](#trace-interrupted-write) | Record replay | Accepted with a warning | The fragment is set aside, never dropped, and the interrupted write is reported |
| <a id="case-recovery-partial-dropped-rejected"></a>Fragment discarded | The runner cuts the log back to line 11 and deletes the fragment | Runner behaviour | Rejected | Silently discarding history is forbidden |
| <a id="case-recovery-tail-accepted"></a>Valid tail without LF | See [Valid tail without LF](#trace-complete-tail) | Record replay | Accepted | A complete event counts and the runner completes its line |
| <a id="case-recovery-invalid-rejected"></a>Invalid historical line | See [Invalid historical line](#trace-invalid-line) | Record replay | Rejected | The line is skipped, kept in the file and reported |
| <a id="case-recovery-invalid-guessed-rejected"></a>Lost decision guessed | A reader rebuilds the lost decision as `by=learner provenance=verified` from the project files | Record replay | Rejected | A reader never repairs history by guessing |
| <a id="case-recovery-invalid-edited-rejected"></a>Damaged line deleted | The runner removes the invalid line from the file | Runner behaviour | Rejected | A line in the log is never edited or removed |
| <a id="case-recovery-rebuild-accepted"></a>Damaged record rebuilt | See [Damaged record](#trace-rebuild) | Runner behaviour | Accepted | The events win over the record |
| <a id="case-recovery-record-trusted-rejected"></a>Damaged record trusted | The runner resumes from the `record.json` that says `finish` passed | Runner behaviour | Rejected | A record that disagrees with the log is replaced |
| <a id="case-recovery-orphan-accepted"></a>Record without a log | A record at generation 1 but no events; preserve it as `record.orphaned.json` and stop authoritative resume | Runner behaviour | Accepted | Missing committed history cannot authorise generation zero or new progress |
| <a id="case-recovery-atomic-accepted"></a>Atomic replacement | The runner writes a temporary file, stores it and renames it over `record.json` | Runner behaviour | Accepted | A reader sees the whole old file or the whole new one |
| <a id="case-recovery-inplace-rejected"></a>Edited in place | The runner rewrites `record.json` in place and crashes half way | Runner behaviour | Rejected | The runner replaces the whole file, never edits it in place |
| <a id="case-resume-open-call-accepted"></a>Open call put again | The opening, then a log that ends with `call-put` for `choose-check` and no answer; the runner puts it again and writes a new `call-put` | Runner behaviour | Accepted | An open call is put again and never inferred |
| <a id="case-resume-passed-lesson-accepted"></a>Resume after a passed lesson | The opening record, whose position lesson `make` has passed | Runner behaviour | Accepted | The runner resumes at `finish`, the first lesson that is neither passed nor skipped |
| <a id="case-replay-data-kept-accepted"></a>Authored folders kept per identity | See [Resume after an upgrade](#trace-upgrade-resume) | Record replay | Accepted | Each applied transition loads its verified retained folder, so an upgrade does not change the past |
| <a id="case-replay-data-installed-rejected"></a>Old lines replayed with the installed course | The same trace, but replay reads the installed `S2` course for lines 1 to 11 | Record replay | Rejected | Replay never reads the installed course, so old `make` evidence is verified against S1 before being archived |
| <a id="case-replay-data-latest-rejected"></a>Latest snapshot substituted | A runner finds no retained folder for `S1` and replays lines 1 to 11 with the `S2` data | Record replay | Rejected | Replay never substitutes another snapshot |
| <a id="case-replay-data-missing-accepted"></a>Missing data stops replay | See [Missing replay data](#trace-missing-replay) | Runner behaviour | Accepted | The runner stops, tells the learner and writes nothing |
| <a id="case-replay-data-missing-overwritten-rejected"></a>Partial result written | The same log; the runner writes the record it could derive from lines 12 onward over `record.json` | Runner behaviour | Rejected | A partial replay never replaces the record |
| <a id="case-replay-data-learner-rejected"></a>Learner data copied into retained source | The runner copies a learner workspace into the retained authored folder | Record structure | Rejected | Only authored identity-included source is retained |
| <a id="case-start-unstarted-rejected"></a>Lines before `lesson-started` | See [Lines before `lesson-started`](#trace-not-started) | Record replay | Rejected | A line naming a lesson with no applied `lesson-started` is not applied |
| <a id="case-start-then-run-accepted"></a>Same lines after `lesson-started` | The same `check-run` and `lesson-completed` written after line 07 | Record replay | Accepted | Once the lesson has started, they apply in order |
| <a id="case-explain-latest-miss-rejected"></a>Latest attempt misses | See [Two attempts, the later one misses](#trace-explain-latest-miss) | Record replay | Rejected | An earlier passing attempt does not count after a later miss |
| <a id="case-explain-latest-pass-accepted"></a>Latest attempt passes | See [Two attempts, the later one passes](#trace-explain-latest-pass) | Record replay | Accepted | A later attempt that meets the bar replaces an earlier miss |
| <a id="case-settle-order-accepted"></a>Settlement in declaration order | See [Two attempts, the later one passes](#trace-explain-latest-pass) | Record replay | Accepted | One completion adds `agent-passes` then `agent-explained`, as `finish.md` declares them |
| <a id="case-settle-order-name-rejected"></a>Settlement in name order | The same completion adds `agent-explained` first because it sorts first | Record replay | Rejected | The order is declaration order, never name order or evidence order |
| <a id="case-upgrade-explicit-accepted"></a>Explicit upgrade | See [Explicit upgrade](#trace-upgrade) | Record replay | Accepted | History is kept and settled objectives keep their snapshot |
| <a id="case-upgrade-resettled-rejected"></a>Upgrade re-settles | After the upgrade, the reader moves `agent-runs-ok` to `S2` | Record replay | Rejected | Nothing is re-settled by an upgrade |
| <a id="case-upgrade-changed-refused-accepted"></a>Changed content refused | See [Changed content](#trace-changed-content) | Runner behaviour | Accepted | An unrequested change is refused and writes nothing |
| <a id="case-consent-stored-accepted"></a>Consent stored | See [Consent](#trace-consent) | Record replay | Accepted | A withdrawal and a skip survive a closed session |
| <a id="case-consent-silence-stored-rejected"></a>Silence written as consent | The runner writes `granted` because the learner did not answer | Runner behaviour | Rejected | Silence is a no and writes nothing |
| <a id="case-privacy-answer-rejected"></a>Answer in an unknown field | A `call-decided` line carries the typed answer in a field called `answer` | Runner behaviour | Rejected | No field, known or unknown, holds an answer |
| <a id="case-privacy-hash-rejected"></a>Hash of an answer | A line carries a SHA-256 of the typed answer | Runner behaviour | Rejected | A hash of free text is never stored |
| <a id="case-privacy-conversation-rejected"></a>Conversation text | An event holds the tutor's recommendation text | Runner behaviour | Rejected | No field holds conversation text |
| <a id="case-privacy-identifier-rejected"></a>Machine identifier | An event holds the host's machine name | Runner behaviour | Rejected | No field holds a machine identifier |
| <a id="case-schema-address-accepted"></a>Schema address | The `record` type in candidate `1.0.0-rc.2` is `https://agentcourses.io/schemas/1.0.0-rc.2/record.schema.json` | Candidate wording | Accepted | The address follows the pattern |
| <a id="case-schema-address-reused-rejected"></a>Address reused for new bytes | A published address serves changed bytes | Candidate wording | Rejected | A published address never changes its bytes |
| <a id="case-schema-address-live-rejected"></a>Address claimed live early | The text says the schema addresses are live before publication | Candidate wording | Rejected | No address is live until it has been published and checked |
| <a id="case-names-accepted"></a>Names | The candidate names the specification, its version, the home and the file paths, and no command or package | Candidate wording | Accepted | Only what the rules need is named |
| <a id="case-names-package-rejected"></a>Package name claimed | The candidate names a command and says its package name is free | Candidate wording | Rejected | Availability is a release-time check and unverified |
| <a id="case-status-candidate-accepted"></a>Candidate wording | The candidate says it is a candidate, that no host is qualified and that stability is later | Candidate wording | Accepted | Candidate status claims no host, package or stability |
| <a id="case-status-stable-rejected"></a>Stable or conformant claimed | The candidate or a runner says it is stable or conforming | Candidate wording | Rejected | No stability or conformance claim is allowed yet |
| <a id="case-status-approved-rejected"></a>Fields called owner-approved | The candidate says the owner approved the event and field names | Candidate wording | Rejected | Plan acceptance, a link check or a review is not the owner's approval of a choice |

## Transition and admission cases <a id="transition-cases"></a>

These cases use the complete trace inputs and opening above. Every case is independent unless it explicitly names another trace. Start and upgrade events use source local with no commit unless the case changes it. Runner behaviour cases describe protected operations; replay cases describe durable input, so a refused live request never masquerades as a broken commitment.

| Case | Complete baseline and decisive change | Judged as | Outcome | Expected result and normative clause |
| --- | --- | --- | --- | --- |
| <a id="case-lookup-current"></a>Current decision applies | Opening plus finishing learner-verified variant; S1 retained and O2 issuance bound to generation 1 | Record replay | Accepted | Finish passes and adds agent-passes then agent-explained at 09:19:00; generation 1 and empty history remain. [Rule](#applying-events) |
| <a id="case-lookup-unknown"></a>Wrong snapshot never loads its folder | Change only line 14 snapshot to an otherwise unknown valid identity; its retained folder is absent | Record replay | Accepted | Line 14 is not applied before lookup; finish passes but only agent-runs-ok remains settled. [Rule](#applying-events) |
| <a id="case-lookup-wrong-from"></a>Wrong from never loads target | Opening, then upgrade from=S2 to an unknown valid identity, version=1.2.0 source=local | Record replay | Accepted | No target lookup; whole opening record remains generation 1. [Rule](#applying-events) |
| <a id="case-lookup-committed-missing"></a>Missing committed target stops | Opening, then upgrade from=S1 to=S2 version=1.1.0 source=local; delete retained S2 | Runner behaviour | Accepted | Stop naming S2; no partial record or lock write, teaching or settlement. [Rule](#replay-data) |
| <a id="case-lookup-later-start"></a>Later start needs no target | Opening then a structurally valid course-started for unknown snapshot, matching name/version and source=local | Record replay | Accepted | No lookup; opening projection unchanged. [Rule](#applying-events) |
| <a id="case-lookup-unknown-kind"></a>Unknown kind needs no source | Opening then kind=future-event with snapshot set to unknown identity and an extra unknown field | Record replay | Accepted | No lookup or field copied; opening projection unchanged. [Rule](#applying-events) |
| <a id="case-retained-tamper-content"></a>Tampered content | Append a byte to retained COURSE.md without renaming the S1 directory; replay learner-verified finishing history | Record replay | Rejected | Identity verification fails before settlement; stop with S1 and no output. [Rule](#replay-data) |
| <a id="case-retained-tamper-call"></a>Tampered call | Remove choose-check from retained finish.md without renaming the S1 directory; replay learner-verified finishing history | Record replay | Rejected | Identity verification fails before settlement; stop with S1 and no output. [Rule](#replay-data) |
| <a id="case-retained-tamper-rubric"></a>Tampered rubric | Change retained rubric from 2 of 3 to 1 of 3 without renaming the S1 directory; replay learner-verified finishing history | Record replay | Rejected | Identity verification fails before settlement; stop with S1 and no output. [Rule](#replay-data) |
| <a id="case-retained-restore"></a>Exact restoration | Delete S1, observe stopped replay, then restore all exact S1 bytes and replay the same complete finishing history | Runner behaviour | Accepted | After identity and structure verification, every original field and timestamp reproduces. [Rule](#replay-data) |
| <a id="case-structure-course"></a>Correct hash, invalid course | Replace COURSE.md with plain text missing frontmatter; compute its new identity and name a first transition with that identity | Record replay | Rejected | Digest matches but course validation stops before progress; never reuse the invalid metadata. [Rule](#replay-data) |
| <a id="case-structure-call"></a>Correct hash, invalid call | Duplicate choose-check in finish.md calls; compute its new identity and name a first transition with that identity | Record replay | Rejected | Digest matches but course validation stops before progress; never reuse the invalid metadata. [Rule](#replay-data) |
| <a id="case-structure-rubric"></a>Correct hash, invalid rubric | Change rubric pass to 4 of 3; compute its new identity and name a first transition with that identity | Record replay | Rejected | Digest matches but course validation stops before progress; never reuse the invalid metadata. [Rule](#replay-data) |
| <a id="case-retained-valid"></a>Verified authored tree | Use S1 at its exact retained key, valid sample-course folder/name/version and complete opening history | Record replay | Accepted | Identity and cross-file validation pass; opening record derives. [Rule](#replay-data) |
| <a id="case-path-traversal"></a>Invalid identity traversal | First transition snapshot=sha256:../outside | Record replay | Rejected | Invalid line before path construction; no source lookup or progress. [Rule](#event-fields) |
| <a id="case-path-uppercase"></a>Invalid identity uppercase | First transition snapshot=sha256: followed by 64 uppercase A digits | Record replay | Rejected | Invalid line before path construction; no source lookup or progress. [Rule](#event-fields) |
| <a id="case-path-short"></a>Invalid identity short | First transition snapshot=sha256:1234 | Record replay | Rejected | Invalid line before path construction; no source lookup or progress. [Rule](#event-fields) |
| <a id="case-path-prefix"></a>Invalid identity prefix | First transition snapshot=SHA256: followed by 64 lowercase a digits | Record replay | Rejected | Invalid line before path construction; no source lookup or progress. [Rule](#event-fields) |
| <a id="case-path-root-link"></a>Retained path root-link | Make the retained sample-course component a symlink to the original source and replay the S1 opening | Record replay | Rejected | Required source refuses; no output; labels and links cannot prove identity. [Rule](#replay-data) |
| <a id="case-path-digest-link"></a>Retained path digest-link | Make its digest directory a symlink outside the store and replay the S1 opening | Record replay | Rejected | Required source refuses; no output; labels and links cannot prove identity. [Rule](#replay-data) |
| <a id="case-path-wrong-label"></a>Retained path wrong-label | Place S2 bytes under the S1 directory name and replay the S1 opening | Record replay | Rejected | Required source refuses; no output; labels and links cannot prove identity. [Rule](#replay-data) |
| <a id="case-stable-read"></a>Unchanged protected read | Hash S1 and derive metadata from the same captured bytes under the protected writer boundary | Record replay | Accepted | Opening record derives; no second unverified metadata source is consulted. [Rule](#replay-data) |
| <a id="case-stable-swap"></a>Metadata swap after hash | Swap finish.md after hashing S1 and before metadata interpretation | Record replay | Rejected | Abort without evidence or projection; never accept the swapped metadata. [Rule](#replay-data) |
| <a id="case-metadata-link-escape"></a>Metadata link escape | Replace lessons/finish.md with a symlink to ../../outside.md; compute the changed tree identity and use it in the start event | Record replay | Rejected | Identity may compute, but metadata resolution fails; no source use or evidence. [Rule](#replay-data) |
| <a id="case-metadata-link-excluded"></a>Metadata link excluded | Replace lessons/finish.md with a symlink to ../.agents/private.md; compute the changed tree identity and use it in the start event | Record replay | Rejected | Identity may compute, but metadata resolution fails; no source use or evidence. [Rule](#replay-data) |
| <a id="case-metadata-link-cycle"></a>Metadata link cycle | Replace lessons/finish.md with a symlink to finish.md; compute the changed tree identity and use it in the start event | Record replay | Rejected | Identity may compute, but metadata resolution fails; no source use or evidence. [Rule](#replay-data) |
| <a id="case-metadata-link-missing"></a>Metadata link missing | Replace lessons/finish.md with a symlink to absent.md; compute the changed tree identity and use it in the start event | Record replay | Rejected | Identity may compute, but metadata resolution fails; no source use or evidence. [Rule](#replay-data) |
| <a id="case-metadata-link-inside"></a>Included metadata link | Start from the complete S1 tree. Move lessons/finish.md bytes unchanged to assets/finish-body.md; replace lessons/finish.md with a symlink whose target is ../assets/finish-body.md. The variant identity is sha256:df6ae32cbea4046f264ab39c9c1e517a3074a8d13fa97314f77c82a0428970d9. Replay only a course-started event naming this identity, sample-course, version 1.0.0 and source=local | Record replay | Accepted | Identity and course validation pass; the included target supplies the same lesson metadata. The record has spec=1.0, course=sample-course, version=1.0.0, the variant snapshot, generation=1, project=null, position=null, lessons={}, and empty history, calls, objectives, consent and declined arrays. No outside bytes are read. [Rule](#replay-data) |
| <a id="case-live-unavailable"></a>Live request unavailable | Opening state; explicit upgrade request; S2 cannot be loaded | Runner behaviour | Accepted | No transition appended; install, lock, record, generation, history, workspace and otherwise valid pending admissions stay unchanged. [Rule](#upgrade-projection) |
| <a id="case-live-invalid"></a>Live request invalid | Opening state; explicit upgrade request; The fetched target has a malformed rubric | Runner behaviour | Accepted | No transition appended; install, lock, record, generation, history, workspace and otherwise valid pending admissions stay unchanged. [Rule](#upgrade-projection) |
| <a id="case-live-incompatible"></a>Live request incompatible | Opening state with selected own and an otherwise valid pending admission; explicit upgrade request. Start from the complete S2 tree, insert project: starter immediately after license: Apache-2.0 in COURSE.md, and add assets/starter/README.md containing exactly Start your agent here. followed by LF. The variant identity is sha256:6d0841f2afde2a608238c7f07ce634413fb3d238bf9049c1fdcca267f05cd5a2 | Runner behaviour | Accepted | Identity and course validation pass before compatibility is evaluated. The target offers only starter, so selected own is incompatible. No transition is appended; install, lock, record, generation, history, workspace and the pending admission stay unchanged. A later valid result for that admission can still apply. [Rule](#upgrade-projection) |
| <a id="case-live-same"></a>Live request same | Opening state; explicit upgrade request; Requested identity is already S1 | Runner behaviour | Accepted | No transition appended; install, lock, record, generation, history, workspace and otherwise valid pending admissions stay unchanged. [Rule](#upgrade-projection) |
| <a id="case-crash-before-snapshot"></a>Before snapshot | Opening; prepare S2 upgrade; Crash before retained-folder rename | Runner behaviour | Accepted | Recover opening generation 1 with no history; temporary/orphan target never moves the pin; workspace unchanged. [Rule](#transition-durability) |
| <a id="case-crash-after-snapshot"></a>After snapshot | Opening; prepare S2 upgrade; Crash after retained-folder rename but before event append | Runner behaviour | Accepted | Recover opening generation 1 with no history; temporary/orphan target never moves the pin; workspace unchanged. [Rule](#transition-durability) |
| <a id="case-crash-event"></a>Crash after event | Opening; committed S1→S2 at 10:00:00; After durable transition append | Runner behaviour | Accepted | Recovery gives exactly explicit-upgrade projection: generation 2, one generation-one history entry, original 09:09:00 objective time, empty active progress; no second event; other lock entries and workspace unchanged. [Rule](#transition-durability) |
| <a id="case-crash-install"></a>Crash after install | Opening; committed S1→S2 at 10:00:00; After installed-copy replacement | Runner behaviour | Accepted | Recovery gives exactly explicit-upgrade projection: generation 2, one generation-one history entry, original 09:09:00 objective time, empty active progress; no second event; other lock entries and workspace unchanged. [Rule](#transition-durability) |
| <a id="case-crash-lock"></a>Crash after lock | Opening; committed S1→S2 at 10:00:00; After lock replacement | Runner behaviour | Accepted | Recovery gives exactly explicit-upgrade projection: generation 2, one generation-one history entry, original 09:09:00 objective time, empty active progress; no second event; other lock entries and workspace unchanged. [Rule](#transition-durability) |
| <a id="case-crash-record"></a>Crash after record | Opening; committed S1→S2 at 10:00:00; After record replacement | Runner behaviour | Accepted | Recovery gives exactly explicit-upgrade projection: generation 2, one generation-one history entry, original 09:09:00 objective time, empty active progress; no second event; other lock entries and workspace unchanged. [Rule](#transition-durability) |
| <a id="case-durability-conflict"></a>Conflicting retained folder | S2 final directory already exists but contains altered bytes; prepare explicit upgrade | Runner behaviour | Rejected | Refuse before commitment; never overwrite it or change active state. [Rule](#transition-durability) |
| <a id="case-durability-lock-damaged"></a>Unrecoverable other lock entry | Committed S2 transition; another course entry is damaged and cannot be restored trustworthily | Runner behaviour | Accepted | Stop before teaching; preserve damaged lock and publish no partial record. [Rule](#transition-durability) |
| <a id="case-durability-lost-transition"></a>Lost committed transition | Known committed S2 history is truncated; newer lock still names S2 | Runner behaviour | Accepted | Stop authoritative resume; do not infer transition, reset generation or reinterpret it as a refused request. [Rule](#transition-durability) |
| <a id="case-transition-local"></a>Valid local transition | Opening start with source=local and commit=absent | Record replay | Accepted | Start applies at generation 1; recovery reconstructs the matching lock source and Git-only commit. [Rule](#event-fields) |
| <a id="case-transition-git"></a>Valid git transition | Opening start with source=gh:example-co/courses@v1.0.0#sample-course and commit=9f3c2e1a4b5d6c7e8f90a1b2c3d4e5f607182930 | Record replay | Accepted | Start applies at generation 1; recovery reconstructs the matching lock source and Git-only commit. [Rule](#event-fields) |
| <a id="case-transition-no-source"></a>Invalid transition no-source | Opening start; Remove source | Record replay | Rejected | Invalid transition line; no inferred start or generation; report damage. [Rule](#event-fields) |
| <a id="case-transition-no-git-commit"></a>Invalid transition no-git-commit | Opening start; Use Git source but omit commit | Record replay | Rejected | Invalid transition line; no inferred start or generation; report damage. [Rule](#event-fields) |
| <a id="case-transition-local-commit"></a>Invalid transition local-commit | Opening start; Set source local and add a commit | Record replay | Rejected | Invalid transition line; no inferred start or generation; report damage. [Rule](#event-fields) |
| <a id="case-transition-credential"></a>Invalid transition credential | Opening start; Set source git+https://user:token@git.example.com/team/repo.git | Record replay | Rejected | Invalid transition line; no inferred start or generation; report damage. [Rule](#event-fields) |
| <a id="case-transition-absolute"></a>Invalid transition absolute | Opening start; Set source /Users/learner/course | Record replay | Rejected | Invalid transition line; no inferred start or generation; report damage. [Rule](#event-fields) |
| <a id="case-transition-home"></a>Invalid transition home | Opening start; Set source ~/course | Record replay | Rejected | Invalid transition line; no inferred start or generation; report damage. [Rule](#event-fields) |
| <a id="case-transition-bad-commit"></a>Invalid transition bad-commit | Opening start; Use Git source and commit ABC | Record replay | Rejected | Invalid transition line; no inferred start or generation; report damage. [Rule](#event-fields) |
| <a id="case-transition-generation"></a>Invalid transition generation | Opening start; Add generation 1 to the transition | Record replay | Rejected | Invalid transition line; no inferred start or generation; report damage. [Rule](#event-fields) |
| <a id="case-upgrade-reset"></a>Old evidence is historical | Learner-verified finishing history, then committed S1→S2 | Record replay | Accepted | Archive completed finish and its evidence/time; active generation 2 has null position and empty lessons/calls/objectives; course is not complete. [Rule](#upgrade-projection) |
| <a id="case-upgrade-complete-immediate"></a>Completion without new start | Previous upgraded state, then lesson-completed finish snapshot=S2 generation=2 | Record replay | Rejected | Not applied because finish has no current lesson-start; history unchanged. [Rule](#upgrade-projection) |
| <a id="case-upgrade-fresh"></a>Fresh evidence after upgrade | Previous upgraded state; new finish start, call-put, fresh generation-two confirmed decision, current check pass, current 2-of-3 judgement and completion at 11:00:00 | Record replay | Accepted | Finish passes and two objectives settle under S2 at 11:00:00; archived S1 outcomes remain unchanged. [Rule](#upgrade-projection) |
| <a id="case-upgrade-revisit"></a>Revisit an older identity | Opening; S1→S2 at 10:00:00, then S2→S1 version=1.0.0 source=local at 11:00:00 | Record replay | Accepted | Generation 3; history ordered generations 1 then 2; active progress empty, position null; original make achievement is only in history[0]. [Rule](#upgrade-projection) |
| <a id="case-upgrade-current-noop"></a>Already-current request | Revisit trace, then request S1 again while a generation-three check is admitted | Runner behaviour | Accepted | Append nothing; keep generation 3 and two history entries; otherwise valid pending result may append. [Rule](#upgrade-projection) |
| <a id="case-delayed-check"></a>Delayed check from first visit | Admit check for finish in generation 1; apply S1→S2→S1; start finish in generation 3; receive old result | Runner behaviour | Rejected | Reject before appending, even though identity and lesson match; no current evidence. [Rule](#operation-admission) |
| <a id="case-relabel-check"></a>Relabelled check result | Same delayed result, but caller supplies snapshot=S1 generation=3 | Runner behaviour | Rejected | Protected original admission remains generation 1; reject without append. [Rule](#operation-admission) |
| <a id="case-fresh-check"></a>Fresh check after revisit | Start finish in generation 3; dispatch check there and receive its matching passing result | Runner behaviour | Accepted | Accept as current evidence if its normal declared-id/attempt checks pass; this result alone does not settle. [Rule](#operation-admission) |
| <a id="case-restart-check"></a>Restart with unfinished check | Admit check in generation 3; restart without upgrade; receive that result | Runner behaviour | Rejected | Cancel unfinished admission; refuse arriving result; snapshot equality cannot revive it. [Rule](#operation-admission) |
| <a id="case-restart-fresh-check"></a>New check after restart | Same state after restart; dispatch and receive a new check result | Runner behaviour | Accepted | Fresh protected current admission can supply evidence. [Rule](#operation-admission) |
| <a id="case-delayed-explain"></a>Delayed explain from first visit | Admit explain for finish in generation 1; apply S1→S2→S1; start finish in generation 3; receive old result | Runner behaviour | Rejected | Reject before appending, even though identity and lesson match; no current evidence. [Rule](#operation-admission) |
| <a id="case-relabel-explain"></a>Relabelled explain result | Same delayed result, but caller supplies snapshot=S1 generation=3 | Runner behaviour | Rejected | Protected original admission remains generation 1; reject without append. [Rule](#operation-admission) |
| <a id="case-fresh-explain"></a>Fresh explain after revisit | Start finish in generation 3; dispatch explain there and receive its matching passing result | Runner behaviour | Accepted | Accept as current evidence if its normal declared-id/attempt checks pass; this result alone does not settle. [Rule](#operation-admission) |
| <a id="case-restart-explain"></a>Restart with unfinished explain | Admit explain in generation 3; restart without upgrade; receive that result | Runner behaviour | Rejected | Cancel unfinished admission; refuse arriving result; snapshot equality cannot revive it. [Rule](#operation-admission) |
| <a id="case-restart-fresh-explain"></a>New explain after restart | Same state after restart; dispatch and receive a new explain result | Runner behaviour | Accepted | Fresh protected current admission can supply evidence. [Rule](#operation-admission) |
| <a id="case-receipt-unused-old"></a>Unused old occurrence | Issue unused O2 in generation 1 for S1/finish/choose-check; revisit S1 at generation 3; open that call and submit O2 | Record replay | Rejected | Known issuance mismatch rejects; call stays open, even if public event claims generation 3. [Rule](#operation-admission) |
| <a id="case-receipt-fresh-current"></a>Fresh current occurrence | Same current open call, but issue a new occurrence durably bound to generation 3 | Record replay | Accepted | Verified callback may decide the call; normal check/explain evidence is still required for settlement. [Rule](#operation-admission) |
| <a id="case-race-before-upgrade"></a>Admission ordering before-upgrade | Opening with admitted current result; Append result before durable upgrade | Runner behaviour | Accepted | Result belongs to generation-one history; upgrade then clears active evidence. [Rule](#operation-admission) |
| <a id="case-race-after-upgrade"></a>Admission ordering after-upgrade | Opening with admitted current result; Commit upgrade before result arrives | Runner behaviour | Accepted | Original generation-one result refuses before append. [Rule](#operation-admission) |
| <a id="case-race-before-result"></a>Admission ordering before-result | Opening with admitted current result; Restart just before result append | Runner behaviour | Accepted | No committed result; cancel admission and require fresh dispatch. [Rule](#operation-admission) |
| <a id="case-race-after-result"></a>Admission ordering after-result | Opening with admitted current result; Restart just after result is durably appended | Runner behaviour | Accepted | Replay original committed result and timestamp once; do not redeem occurrence again. [Rule](#operation-admission) |
| <a id="case-confirmation-binding"></a>Confirmation recovery binding | Current-generation open call after restart; Recover original current-generation issuance and attestation | Record replay | Accepted | Same event verifies on repeated replay without another redemption. [Rule](#replay-interface) |
| <a id="case-confirmation-missing"></a>Confirmation recovery missing | Current-generation open call after restart; Lose issuance binding before event commitment | Record replay | Accepted | Missing provenance remains unverified; no settlement; request fresh confirmation. [Rule](#replay-interface) |
| <a id="case-confirmation-old"></a>Confirmation recovery old | Current-generation open call after restart; Recover a generation-one binding after revisit at generation 3 | Record replay | Accepted | Known mismatch is rejected; event label cannot repair it. [Rule](#replay-interface) |
| <a id="case-confirmation-authority"></a>Confirmation recovery authority | Current-generation open call after restart; Lose authority required to replay previously established history | Runner behaviour | Accepted | Stop authoritative resume; never rewrite established history as newly verified. [Rule](#replay-interface) |
| <a id="case-callback-bad"></a>Invalid callback result | Otherwise applicable learner decision; callback returns yes instead of one of the three statuses | Record replay | Rejected | Raise ContractError; no partial projection. [Rule](#replay-interface) |
| <a id="case-callback-import"></a>Imported verified label | Read learner-verified JSON without original protected authority | Record replay | Accepted | View remains unverified, objectives cannot settle; JSON/digest proves no provenance. [Rule](#replay-interface) |
| <a id="case-callback-no-promotion"></a>Unverified label cannot promote | Otherwise applicable unverified learner event; callback returns verified | Record replay | Accepted | Decision remains unverified; no objective settlement. [Rule](#replay-interface) |
| <a id="case-generation-missing"></a>Malformed generation missing | Opening through line 2, then lesson-started intro with generation=absent | Record replay | Rejected | Invalid event; no lesson entry, lookup or generation change. [Rule](#event-fields) |
| <a id="case-generation-string"></a>Malformed generation string | Opening through line 2, then lesson-started intro with generation="1" | Record replay | Rejected | Invalid event; no lesson entry, lookup or generation change. [Rule](#event-fields) |
| <a id="case-generation-boolean"></a>Malformed generation boolean | Opening through line 2, then lesson-started intro with generation=true | Record replay | Rejected | Invalid event; no lesson entry, lookup or generation change. [Rule](#event-fields) |
| <a id="case-generation-zero"></a>Malformed generation zero | Opening through line 2, then lesson-started intro with generation=0 | Record replay | Rejected | Invalid event; no lesson entry, lookup or generation change. [Rule](#event-fields) |
| <a id="case-generation-negative"></a>Malformed generation negative | Opening through line 2, then lesson-started intro with generation=-1 | Record replay | Rejected | Invalid event; no lesson entry, lookup or generation change. [Rule](#event-fields) |
| <a id="case-generation-past"></a>Wrong-current generation past | Revisit state at generation 3; lesson-started intro snapshot=S1 generation=1 | Record replay | Rejected | Well-shaped but not applied before lookup; active lessons remain empty. [Rule](#applying-events) |
| <a id="case-generation-future"></a>Wrong-current generation future | Revisit state at generation 3; lesson-started intro snapshot=S1 generation=4 | Record replay | Rejected | Well-shaped but not applied before lookup; active lessons remain empty. [Rule](#applying-events) |
| <a id="case-generation-current"></a>Current generation | Revisit state; lesson-started intro snapshot=S1 generation=3 | Record replay | Accepted | Creates intro started and position intro/goal; counter remains 3. [Rule](#applying-events) |
| <a id="case-changed-command"></a>New command declined | Upgrade to S2, start finish at generation 2, disclose command including --strict, learner declines, check-run final-check not-run without evidence; learner skips | Record replay | Accepted | Finish skipped, runs 0, no objective; old passing command cannot avoid disclosure. [Rule](#upgrade-projection) |
| <a id="case-optional-fails"></a>Optional failure does not gate | Variant S1 make declares checks: [{id: agent-runs, required: false}]; compute variant identity; start make, agent-runs fail observed, complete at 09:09:00 | Record replay | Accepted | Make passes but agent-runs-ok remains unsettled because its own optional evidence failed. [Rule](#completing) |
| <a id="case-optional-passes"></a>Optional objective has evidence | Same variant and log, changing only result fail to pass | Record replay | Accepted | Make passes and agent-runs-ok settles observed at 09:09:00 under the variant identity. [Rule](#settling) |
| <a id="case-required-fails"></a>Required failure still gates | Unmodified S1 make, start, agent-runs fail observed, complete | Record replay | Rejected | Completion not applied; make stays started and no objective settles. [Rule](#completing) |
| <a id="case-privacy-admission"></a>Private admission payload | Confirmation controller retains an answer hash beside its issuance binding | Runner behaviour | Rejected | Forbidden even outside public JSON; no answer-derived data may establish provenance. [Rule](#privacy) |
| <a id="case-schema-no-cache"></a>Existing schemas cover inputs | Describe event transition/lesson fields, record generation/history and authored-file schemas; no replay manifest | Candidate wording | Accepted | Exactly eight types remain; callback and cross-file checks are semantic proof duties. [Rule](#replay-interface) |
| <a id="case-host-synthetic"></a>Synthetic qualification limit | A controlled callback returns verified in a bounded replay experiment | Candidate wording | Accepted | Report only synthetic assumed authority; no actual host or filesystem durability claim. [Rule](#replay-interface) |

### Projection and schema boundary cases <a id="projection-cases"></a>

These cases mutate a complete derived projection or transition, one field at a time. A shape failure never supplies missing authority. Reconstruction uses the same protected history and required sources; it is unavailable when those are lost.

| Case | Baseline and decisive change | Judged as | Outcome | Deciding rule |
| --- | --- | --- | --- | --- |
| <a id="case-projection-current"></a>Complete projection | The opening record includes generation 1 and history [] | Record structure | Accepted | [Record fields](#record-fields) require both |
| <a id="case-projection-generation-missing"></a>No record generation | Remove generation from the opening record | Record structure | Rejected | Rebuild; never trust an absent counter |
| <a id="case-projection-generation-wrong"></a>False derived counter | Opening record says generation 3 although its log has only one applied start | Record replay | Rejected | Replay derives 1 and replaces stale projection |
| <a id="case-projection-history-missing"></a>No history list | Remove history from the opening record | Record structure | Rejected | Rebuild the required empty list |
| <a id="case-projection-history-null"></a>Null archive identity | Explicit-upgrade record history[0].snapshot is null | Record structure | Rejected | Archived identity/version are non-null |
| <a id="case-projection-history-zero"></a>Zero archived generation | Explicit-upgrade history[0].generation is 0 | Record structure | Rejected | An archive is a previously active positive generation |
| <a id="case-projection-history-nested"></a>Recursive history | Add history: [] inside explicit-upgrade history[0] | Record structure | Rejected | Archive entries have exactly seven fields and no nested history |
| <a id="case-projection-history-project"></a>Project copied into history | Add project to explicit-upgrade history[0] | Record structure | Rejected | Project and consent remain only in the active root |
| <a id="case-projection-history-restamped"></a>Old achievement restamped | Explicit-upgrade history[0].objectives[0].at becomes 10:00:00 instead of 09:09:00 | Record replay | Rejected | Replay restores its original completion time and S1 evidence |
| <a id="case-projection-history-reordered"></a>History reversed | Revisit record has generation-two entry before generation-one entry | Record replay | Rejected | Replay restores transition order 1,2 |
| <a id="case-lock-generation"></a>Counter in the lock | Add generation: 1 to an otherwise valid course lock entry | Record structure | Rejected | The lock never carries generation |
| <a id="case-claim-host-qualified"></a>Synthetic callback claimed to qualify a host | A report labels an actual host qualified solely because replay used a controlled verified callback | Candidate wording | Rejected | [Replay handoff](#replay-interface) proves no actual host |
| <a id="case-claim-durability"></a>Crash oracle claimed as filesystem proof | A report treats a simulated cut-point oracle as proof of real durable writes | Candidate wording | Rejected | Real persistence qualification remains separate |
