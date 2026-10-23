# Pending publication hold

**Pending: implementation merges are blocked until the owner approves this setting change and both event paths demonstrate the hold.**
This procedure protects the existing live publication while the authoring candidate changes.
It targets the existing `github-pages` environment, without approving either waiting deployment.
No approval, configuration change, held run, cancellation or unchanged live-byte result is claimed here.

## Starting evidence and exact requested settings

The orchestrator supplied a read-back dated 23 October 2026 for environment identifier `25019793960`.
It reported `can_admins_bypass=true`, no required reviewers, and only `branch_policy` protection.
That environment does not yet enforce the requested reviewer hold.
Re-read its current settings before acting; this supplied summary is not fresh operational proof.

The owner must separately approve these exact changes before anyone applies them:

| Setting | Required value |
| --- | --- |
| Repository and environment | `agentcourses/agentcourses`, existing `github-pages`, identifier `25019793960` |
| Required reviewers | Exactly repository owner `hnrly`, resolved to the verified GitHub user identifier |
| Administrator bypass | Disabled: `can_admins_bypass=false` |
| Prevent self-review | Disabled, so the owner can review their own manually requested deployment |
| Wait timer | Zero; a timer must not substitute for owner review |
| Deployment branch policy | Preserve its current main-only restriction; record the exact policy fields and rule identifiers before and after |
| Workflow publication guards | Preserve existing checks, upload and deploy conditions |

Save the attributable approval link, date, owner and exact approved settings in this record before configuration.
Approval to implement the milestone does not approve these environment changes.
In repository Settings → Environments → `github-pages`, enable required reviewers, select only the owner, and disable administrator bypass.
Keep the main-only branch policy and workflow unchanged.
If the plan, permissions or environment interface cannot enforce those values, stop and retain the actual error.
Report the limitation and keep merges blocked; do not replace the hold with a delay, failing check or undocumented workaround.

## Read-back after the separately approved change

Read-only API commands below are a procedure for the authorised operator; they have not been executed for this record.
Retain raw JSON, command exit codes and UTC capture times outside the source repository, then link that evidence here.
Resolve the reviewer to the actual account, rather than guessing a numeric identifier.
Do not treat a saved settings screen alone as proof of enforcement.

```bash
gh api users/hnrly
gh api repos/agentcourses/agentcourses/environments/github-pages
gh api repos/agentcourses/agentcourses/environments/github-pages/deployment-branch-policies
```

Confirm the environment identifier, reviewer user identifier and type, required-reviewer rule, and disabled administrator bypass.
Confirm zero wait time, self-review setting and unchanged main-only deployment policy.
A missing field, failed request or unavailable feature leaves the hold unverified.
Before any run, also inspect in-flight deployments and cancel any unapproved work that could publish around the new hold.
Cancelling runs needs the same separately approved operational scope described below.

## Observe the normal main push path

The [publication workflow](../../.github/workflows/gates.yml) runs ordinary checks before uploading the tested production artefact.
Its deployment job requires the protected environment only after successful checks and release preflight.
Observe an authorised normal `push` event on `refs/heads/main`, using the unchanged workflow and default `prove_failure=false`.
Do not merge implementation work to manufacture the prerequisite evidence.
Use an already authorised main push, or obtain separate approval for the exact trigger if none is available.

Record the main commit, workflow revision, event, run URL and run identifier.
Wait for the whole `make check` job, including release preflight and artefact upload, to succeed.
A passing individual check step followed by failed preflight does not prove the environment hold.
Read the run's jobs and pending environment request, for example:

```bash
gh api repos/agentcourses/agentcourses/actions/runs/MAIN_RUN_ID
gh api repos/agentcourses/agentcourses/actions/runs/MAIN_RUN_ID/jobs
gh api repos/agentcourses/agentcourses/actions/runs/MAIN_RUN_ID/pending_deployments
```

Confirm the deployment is waiting for owner review in environment `25019793960`.
Confirm its deploy step has not run, no deployment was approved, and no new successful Pages deployment exists.
Retain request and job identities with UTC times; a queued job without a pending environment request is insufficient.
Cancel the held run without approving or bypassing it, then observe final `cancelled` status and no deploy-step execution.
Use the recorded identifier with `gh run cancel MAIN_RUN_ID --repo agentcourses/agentcourses` only after operational approval.
Read the run, jobs and pending requests again, and confirm no outstanding request remains.
Cancellation releases the shared `gates-refs/heads/main` concurrency group before the dispatch proof starts.

## Observe the manual dispatch path

Separately approved execution must dispatch `gates.yml` on the same main commit with `prove_failure=false`.
An approved operator can use `gh workflow run gates.yml --repo agentcourses/agentcourses --ref main -f prove_failure=false`.
Read back the resolved commit and `workflow_dispatch` event; stop if main moved or another run was selected.
Record its independent run URL and identifier, and repeat every checks, request, deployment and cancellation observation above.
Use that dispatch identifier in all API paths and cancellation commands.
Do not use the failure-proof input, a pull request event, a failed job or a skipped deployment as evidence of this hold.
Never approve either environment request.

## Compare live bytes before and after both held runs

Before the first trigger, retain a timestamped live-byte inventory for `https://agentcourses.io/`.
Use a clean, pinned copy of the currently published source, built with the locked `custom-domain` production profile.
The existing release verifier, `site/scripts/verify-release.mjs`, checks every built page, schema and asset against live bytes:

```bash
node site/scripts/verify-release.mjs --root /ABSOLUTE/CLEAN/PUBLISHED/SOURCE --url https://agentcourses.io/
```

Record that published commit and tree, schema manifest digest, build provenance, command output and successful exit code.
Repeat against the same source and artefact after each cancellation, retaining source, build and live digests.
Require identical live digests and unchanged successful deployment identity throughout.
If the published source cannot be identified or live verification fails, record the actual result and keep merges blocked.
No local build, unchanged homepage alone or missing deployment notification proves unchanged live bytes.

## Evidence required to close this checkpoint

Replace pending entries only with observed facts and durable evidence links.
Keep configuration approval distinct from workflow-trigger and cancellation approval where their scopes differ.
Fresh independent review must reconcile the owner decision, raw read-back, both event paths and live-byte observations.
Only then can implementation merges proceed under the verified hold.

| Evidence | Current state |
| --- | --- |
| Attributable owner approval for exact environment settings | Pending |
| Approval covering both triggers and cancellations | Pending |
| Fresh protection read-back and verified owner account identifier | Pending |
| Main push: successful whole check job and blocked environment request | Pending |
| Main push: cancelled run and no deploy-step execution | Pending |
| Dispatch: successful whole check job and blocked environment request | Pending |
| Dispatch: cancelled run and no deploy-step execution | Pending |
| Before/after full live-byte and successful deployment identity comparison | Pending |
| Independent evidence review | Pending |

The [comparison protocol](authoring-comparison-protocol.md) can be reviewed while this operational checkpoint remains pending.
Preparing this procedure does not satisfy the observed-hold acceptance or authorise deployment.
