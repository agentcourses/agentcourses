# How to review a pull request here

This page tells a reviewer what to check, how to tell a blocking problem from a nit, and how to write findings. The reviewer is never the author, and always starts from a fresh context. Every finding must cite evidence, so the author can act on it without guessing. The verdict goes on the first line of the review.



## What to check

1. **It does what the theme asked.** Compare the change with the theme issue's "Done when" list and the plan's acceptance. Run the commands yourself.
2. **The checks pass.** Run `make check` and read the exit code.
3. **It is proven.** "How it was proven" in the pull request holds real output, and you can reproduce it.
4. **It stays in scope.** Nothing unrequested: no extra features, refactors or files.
5. **The seams hold.** Interfaces the next theme depends on match the plan's names and shapes, including empty and error cases.
6. **Bugs come with a test.** A bug fix has a test that failed before the fix.
7. **It reads well.** The pull request opens with a plain summary, uses no bare codes, and code comments explain the non-obvious why.
8. **Nothing leaks.** No secrets, personal data or private names.

## Blocking or a nit

- **Blocking:** the change is wrong, unproven, out of scope, breaks a check, breaks a seam, or would mislead a reader. It must be fixed before merge.
- **Nit:** a matter of taste or polish that does not change behaviour. The author may decline it with a reason.

If you are unsure, say so and explain what would settle it. Do not mark a guess as blocking.

## How to write a finding

Each finding has four parts: what is wrong, where, the evidence, and what would fix it. Evidence is a file and line, a command and its output, or a failing check.

```text
Blocking: the timeline shows updates oldest first.
Where: app/status_page.py, in render_timeline.
Evidence: `make check` passes, but loading /incidents/7 shows "Investigating" above "Resolved".
Fix: sort by posted time, newest first, and add a test for the order.
```

## The verdict

The first line of the review file is exactly one of these:

```text
Verdict: approved
Verdict: changes-needed
```

Any blocking finding means `changes-needed`. Nits alone never block.

## Also check here

- Check stage regression, deletion and pending-row proofs, because later themes share cumulative source contracts.
- Check the source-only canonical map and separate collections, because future pages must never become production mocks.
- Check ExampleCode traversal and symlink bounds, because snippets must read only their named repository example.
- Check the bad-input helper observes `missing-link` from ordinary `make check`, rather than accepting an unrelated failure.
- Check runtime and lock pins match local and CI setup, and distinguish local proof from an actual Actions run.
- Do not claim branch protection or public visibility: both are deferred by the owner until v1 is ready.
