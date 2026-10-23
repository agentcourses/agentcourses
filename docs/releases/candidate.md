---
title: Candidate publication and handoff
candidate: 1.0.0-rc.2
blockers: []
contract_approval: https://github.com/agentcourses/agentcourses/pull/18
receipt_approval: https://github.com/agentcourses/agentcourses/pull/2
---

# Candidate publication and handoff

This prepares the proposed `1.0.0-rc.2` candidate for publication at `https://agentcourses.io/`.
The [central declaration interpretation](https://github.com/agentcourses/agentcourses/pull/18) supplies the new contract lineage.
That predecessor has independent source approval; its owner acceptance and merge remain pending before this change may merge.
Publication, confirmation of the proposed candidate label and the separate owner freeze decision remain pending.
After predecessor acceptance, independent review and current-head checks, the owner may merge the publication pull request.

## Candidate identity

The proposed tag is `agentcourses-v1.0.0-rc.2`; it does not exist yet.
Once approved and created, that tag resolves the exact reviewed source commit and tree.
No stable release, installable package or qualified runner is claimed.

The [source manifest](../../schemas/manifest.json) lists all eight new schema addresses, versioned source paths and payload SHA-256 checksums.
It also identifies the exact retained first-candidate manifest and its baseline source commit.
The retained candidate is unfrozen; no tag or release approval is invented for it.
Its SHA-256 is `04d371a90b4ea918e794fa0bea6d0da4c3b79fd2e6b00be68339d219961134f6`.
The download inventory will be `https://agentcourses.io/schemas/manifest.json`.
Schema addresses follow `https://agentcourses.io/schemas/1.0.0-rc.2/<type>.schema.json`; these permanent identifiers are not yet live.
Downloads will serve each payload at its own identifier address once deployment and HTTPS succeed.
A published address must retain its exact bytes; changed schema bytes require a new candidate and tag.

## Accepted contract boundaries

The owner merged [the course and execution contract](https://github.com/agentcourses/agentcourses/pull/4) on 20 October 2026.
The owner merged [the records and identity contract](https://github.com/agentcourses/agentcourses/pull/6) on the same date.
The [receipt experiment](https://github.com/agentcourses/agentcourses/pull/2) records the capability choice accepted on 19 October 2026.
The [committed receipt report](../delivery/call-receipts.md#approved-capability-contract--19-october-2026) explains its evidence and limits.
These historical acceptances preserve the original contract boundaries, as mapped in the [requirement register](../../spec/requirements.md).
The new interpretation additionally waits for the predecessor owner acceptance described above.
Neither the historical acceptances nor schema readiness constitutes publication approval or the final candidate freeze.

Receipts require a learner-controlled confirmation path, a protected verifier and durable replay protection outside tutor authority.
No actual host has been qualified.
Unsupported hosts retain unverified calls, which cannot settle objectives.
Records must not contain private answers, conversations, code, file contents, their hashes, credentials or learner identifiers.

## Publication and freeze gates

The [checks and publication workflow](../../.github/workflows/gates.yml) checks source, builds the site and uploads only its tested production artefact.
Deployment accepts only main and uses the existing `github-pages` environment.
The owner will review and merge the source before the normal main deployment runs.
This sequence supersedes the earlier pre-merge deployment and freeze prerequisites.
It does not complete publication or approve the candidate freeze.

Read-only checks refreshed on 22 October 2026 found a public repository and Pages configured for workflow deployment.
Pages reports the custom domain `agentcourses.io`, without enforced HTTPS and with no reported build status.
The `github-pages` environment permits only `main`, has no required reviewers and allows administrator bypass.
Main protection remains deferred by the owner; this adjustment changes no settings.
On 22 October 2026 the owner chose `agentcourses.io` for the initial publication and configured its DNS.
HTTPS enforcement, release protection, candidate-label confirmation and freeze approval remain separate owner gates.
Local checks cannot establish live HTTPS readiness or successful deployment.

After merge, record the exact fetched main commit and its successful ordinary checks.
Run the normal checks and publication workflow, then verify all nine pages, their canonical URLs, response types and every built page, schema and asset byte.
Build and verify the same `custom-domain` profile; its deployment base is `/`.
The verifier accepts `https://agentcourses.io/` and the fallback `https://agentcourses.github.io/agentcourses/` project profile.
It confines redirects to the chosen HTTPS origin and base, verifies production provenance, and checks unchanged schema identifiers and bytes.
Only a passing live verification shows that the permanent schema identifiers are live.
Record the workflow commit, source tree, manifest checksum, deployment run and output digest in external execution evidence.

Dispatch `prove_failure=true` on that same main commit and confirm `missing-link` fails ordinary `make check`.
Upload and deployment must be skipped, with no Pages artefact, deployment or environment request.
Both normal live proof and this controlled failure remain outstanding before publication can be declared complete.
No pre-merge deployment, freeze, tag or prerelease is authorised by this adjustment.

Present the live evidence for the owner's separate freeze decision before creating a protected tag or prerelease record.
The approval record must bind the candidate, exact clean commit and tree, manifest checksum, deployment and attributable owner decision.
A later frozen-reference check must match the inspected source tree to the approved tag and repeat live-byte verification.
Do not edit this source merely to add later deployment or freeze evidence.

## Downstream handoff

The [specification](../../spec/format.md) and [schemas](../../schemas/manifest.json) describe the new candidate for downstream implementation.
The unchanged [quickstart](../../examples/quickstart/COURSE.md) remains first-candidate input in the [reviewed inventory](../../examples/manifest.json).
Example migration, public comparison evidence, publication and freeze remain pending separately.
The [author quickstart](../../site/src/content/docs/authors/quickstart.mdx) and [runner guidance](../../site/src/content/docs/implementers/support.mdx) explain their intended use.
Stable launch still needs the reference library, public validator, conformance classes and suite, qualified hosts, pilot evidence and learner outcomes.
Package publication and runtime support remain later work.
