# Locked authoring comparison protocol

This protocol compares one owner's authoring work against two pinned candidates.
The [baseline manifest](authoring-baseline.json) preserves the first candidate's source and eight schema payloads.
Four timed tasks measure effort and understanding before the later candidate can be accepted.
Synthetic observations in `tests/comparison/fixtures/pass.json` test the instrument and never count as owner evidence.

## Preparation and allowed tools

Use baseline commit `f39cbea910c475f76d87ae186184f1c1d1150f34` and record the new candidate's full commit identifier.
Supply clean, separate workspaces containing only that candidate and the neutral project files described below.
Use each candidate's own documentation, ordinary editor tools and local checks.
Do not use AI authoring assistance, remembered solutions, copied answers or another candidate's documentation during a run.
The facilitator reads only: “Please use the supplied documentation and files. You may stop at any time.”
Record every task-specific help request and response verbatim, with its UTC time; any received task-specific help counts as assistance.

Before starting, retain the exact workspace contents, Git commits and this protocol's SHA-256 digest.
Choose a private participant label; do not store personal details, credentials or learner conversations.
Use `synthetic: false` only for actual owner observations.
Freeze this protocol before any owner timing; changing it requires restarting the comparison with newly recorded identities.
The scorer, `tools/authoring_comparison.py`, verifies the protocol digest and pinned baseline before scoring CLI input.

## Fixed tasks and order

Every task creates a course from scratch, using equivalent supplied project files.
Variant A uses the neutral project name “Cedar Notes”; variant B uses “Harbour Notes”.
Names and sample note text differ; file counts, behaviours, declarations and explanation questions remain equivalent.
Use the same editor and computer throughout, and retain unfinished work at the cap.
No run is repeated to improve its result.

| Order | Candidate | Task | Variant | Active time cap |
| --- | --- | --- | --- | --- |
| First | Baseline | Minimal | A | 20 minutes |
| Second | New | Minimal | B | 20 minutes |
| Third | New | Representative | A | 40 minutes |
| Fourth | Baseline | Representative | B | 40 minutes |

For each minimal task, author a course with a title, description and one linked lesson.
The lesson asks a learner to create a plain text note and explain what it contains.
Supply an empty course directory and the project brief only; use the candidate's documented declaration format.
Declare the lesson's required material and optional reading in the candidate's supported form.
Add separate `references/required.md` and `references/optional.md` files, each containing one neutral paragraph supplied with the brief.
Declare one tutor-only rubric, requiring the note to contain the project name and a non-empty summary.
Explain all four protection questions below after completing the files.

Each representative task contains that minimal structure plus a second lesson and selected starter files.
Supply `starter/note.txt` with a project title and a blank summary line, plus `starter/unused.txt` as an unselected distractor.
Declare only `starter/note.txt` as the starter file for the second lesson.
Declare a command check whose local script passes when the note has a non-empty summary and fails otherwise.
Declare an observe check for the learner demonstrating where the note is saved.
Add one learner call asking which summary to keep, and one objective tied to both checks and that call.
Add optional feedback to a supplied destination `https://feedback.example.test/notes`; provide a decline path and explicit destination consent.
Keep the rubric tutor-only and explain all four protection questions again.
Use the candidate's supported syntax for these same behaviours; the task never requires a particular declaration layout.

## Timing and event recording

Start the clock immediately before opening the task brief and candidate documentation.
End it after the files and four explanations are submitted, or at the active time cap.
Reading, checking, asking questions and correcting mistakes are active time.
Pause only for an external interruption, recording UTC start, end and a concrete reason.
Pauses must fall inside the run and must not overlap; adjacent pauses are allowed.
Active seconds equal elapsed seconds minus the total recorded pause duration.
Keep unfinished files and the actual active time when a run ends at the cap; mark `completed: false`.
Record runs in the fixed order, with no overlapping run intervals.

Count each distinct invalid declaration, broken reference or incorrect protection explanation once, even if later corrected.
Assign one stable error code per distinct error within a run, with a short description.
Do not duplicate that code when the same mistake is observed again.
An incorrect explanation is both an error entry and an incorrect comprehension score.
Retain the owner's four explanations alongside the run artefacts; observation JSON stores only their boolean scores.

## Four explanation questions

Ask these questions after each task, without hints or corrections until all answers are recorded.
Score each explanation strictly as correct or incorrect against these criteria.
Missing answers are missing observations; do not assume correctness or invent a score.
Record the original answer privately with the authored artefacts for later review.

| JSON score | Question | Correct explanation must include |
| --- | --- | --- |
| `required_material` | What must the learner read, and what may they skip? | Required material must be presented; optional reading can be declined without blocking progress. |
| `assessment` | What proves the objective, and who makes the learner's choice? | Check evidence alone cannot replace a required learner decision; missing or unverified evidence cannot count as passed. |
| `tutor_privacy` | Who may see the rubric and its answers? | Tutor-only material stays outside learner disclosure and public output. |
| `consent` | When may feedback leave the workspace? | Each destination requires explicit learner consent; declining sends nothing and does not block course progress. |

## Observation and result contract

The session object has `participant`, `synthetic`, `baseline_commit`, `candidate_commit`, `protocol_sha256` and `runs`.
Use full lowercase Git commit identifiers and the SHA-256 digest of this file's exact bytes.
Each run has `candidate`, `task`, `variant`, `started_at`, `ended_at`, `pauses`, `active_seconds`, `completed`, `errors`, `assistance` and `comprehension`.
Timestamps use UTC ISO 8601 with `Z` or `+00:00`, including seconds and at most six fractional digits.
Each pause has `start`, `end` and `reason`; each error has `code` and `description`.
Each assistance entry has `time` and `text`; its timestamp must fall within the run.
Comprehension contains the four boolean scores above, for every run.
Empty error, assistance and pause lists are valid observed zeroes; absent fields are unknown.
Malformed values, duplicate JSON keys, unexpected fields, duplicate runs and inconsistent timing are rejected rather than repaired.

The result retains `synthetic`, full per-run observations, individual comprehension scores, ordered reasons and per-candidate totals.
Totals contain `active_seconds`, `errors` and `help`, where help counts assistance entries.
Incomplete output retains known measures and represents missing measures and affected totals as JSON `null`.
A missing run produces `missing-run:<candidate>:<task>` in fixed protocol order.
Missing session fields precede run reasons as `missing-field:<field>`.
Missing run fields use `missing-field:<candidate>:<task>:<field>`; individual score gaps append `comprehension.<score>`.
Missing fields follow their order in the session and run field lists above, with `variant` first among measured run fields.
The scorer returns `incomplete` whenever any required observation is absent; it still rejects malformed supplied values.

A complete result passes only when both new tasks are completed unaided and within their respective caps.
New total active time must be strictly lower than baseline total active time.
New errors must not exceed baseline errors; all four explanations must be correct in both new tasks.
Baseline outcomes remain measured, including unfinished baseline work at its cap.
Complete failure reasons appear only in this order: `completion`, `time-cap`, `assistance`, `active-time`, `errors`, `comprehension`.
Each reason appears once, even when both new tasks fail that rule.
Caps apply to all four runs and include their exact boundary; equal total active time fails.
A passing synthetic result remains synthetic and cannot establish owner success.
One owner participates; this exercise makes no wider usability claim.

Run the instrument from the build repository root:

```bash
uv run --locked python tools/authoring_comparison.py --observations observations.json --baseline docs/delivery/authoring-baseline.json
```

The CLI emits JSON and exits zero for a complete pass, one for fail or incomplete, and two for malformed input.
Keep the observations and output beside the pinned run artefacts for independent review.
The separate [publication hold](publication-hold.md) must be approved and observed before implementation merges.
