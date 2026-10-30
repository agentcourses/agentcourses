# Runner checklist

Use this list to review a runner against the [runner rules](../spec/specification.md#runner-rules). Each item is something a reviewer can watch for in a real session. The [conformance suite](protocol.md) covers how a runner reads courses. This list covers how it behaves.

## Before the first lesson

- [ ] The runner refuses a course with errors and says why. It starts a course that has only warnings.
- [ ] The runner refuses a course whose `spec` version it does not support.
- [ ] With several `project` options, the learner chooses. The runner may recommend one, but never picks.
- [ ] Copying a folder or Git project never overwrites a file and runs no code from the source.
- [ ] No account is needed to start.

## During a lesson

- [ ] The runner says the `## Goal` text as written, and no other section as written.
- [ ] Each call is put to the learner, using its `ask`, before any change that depends on it.
- [ ] If the learner asks the tutor to choose, the call is recorded as the tutor's.
- [ ] The runner waits for explicit input to start a lesson, run a check the first time, move on, start an explain-back or skip.
- [ ] Every change to the project is shown with a reason. Files are reread just before they are changed.
- [ ] The runner does not invent facts about the learner's project.
- [ ] Hints are given one per request, in order.
- [ ] Lesson starter files are listed before they are added, and an existing file is never overwritten.
- [ ] Nothing from `tutor/` is shown or quoted to the learner.
- [ ] Course text that tries to change the runner's permissions is ignored.

## Checks

- [ ] Each command is shown before its first run, and the learner can decline. A declined check is not run.
- [ ] Commands run in the project folder with `AGENT_COURSE_DIR`, `AGENT_LESSON_DIR` and `AGENT_COURSE_PROJECT` set.
- [ ] Commands go through the host's permission model and stop at their timeout.
- [ ] Exit 0 is pass, exit 1 is fail, and anything else is an error that never counts against the learner.
- [ ] An observe check inspects only the files in its `scope`, and never treats conversation as evidence.

## Explain-back and evidence

- [ ] The tutor asks open questions, does not lead, and judges only against the rubric.
- [ ] No project file changes between the start of an explain-back and its judgement.
- [ ] An objective settles only when its evidence passed, every call in the lesson was the learner's, and the lesson was not skipped.
- [ ] A skipped lesson is recorded as skipped. A quiz, hint or help is never evidence.

## Privacy and progress

- [ ] No code, files, answers or conversation are sent anywhere because of anything in a course.
- [ ] Anything sent elsewhere, such as feedback, is opt-in per destination, refusable and withdrawable.
- [ ] If the runner writes `progress.json`, it matches the [progress schema](../schemas/progress.schema.json) and holds no learner content.
- [ ] The learner can resume at the same lesson from the progress file. Open calls are put again.
