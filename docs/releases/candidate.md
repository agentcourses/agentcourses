---
title: Candidate publication and handoff
candidate: 1.0.0-rc.1
blockers: []
contract_approval: https://github.com/agentcourses/agentcourses/pull/6
receipt_approval: https://github.com/agentcourses/agentcourses/pull/2
---

# Candidate publication and handoff

This prepares the proposed `1.0.0-rc.1` candidate for publication at `https://agentcourses.io/`.
The owner has accepted the course, records and receipt capability contracts through the linked reviewed changes.
Publication, confirmation of the proposed candidate label and the separate owner freeze decision remain pending.
The next step is preliminary source review, followed by owner-controlled deployment and live verification.

## Candidate identity

The proposed tag is `agentcourses-v1.0.0-rc.1`; it does not exist yet.
Once approved and created, that tag resolves the exact reviewed source commit and tree.
No stable release, installable package or qualified runner is claimed.

The [source manifest](../../schemas/manifest.json) lists all eight schema addresses, flat source paths and payload SHA-256 checksums.
Its SHA-256 is `d4c817d4200539fb1e95edd8814e0a9999fd58ee48a30e93aed3fb38e7414cc3`.
The proposed public inventory is `https://agentcourses.io/schemas/manifest.json`.
Schema addresses follow `https://agentcourses.io/schemas/1.0.0-rc.1/<type>.schema.json`; these addresses are not yet published.
A published address must retain its exact bytes; changed schema bytes require a new candidate and tag.

## Accepted contract boundaries

The owner merged [the course and execution contract](https://github.com/agentcourses/agentcourses/pull/4) on 20 October 2026.
The owner merged [the records and identity contract](https://github.com/agentcourses/agentcourses/pull/6) on the same date.
The [receipt experiment](https://github.com/agentcourses/agentcourses/pull/2) records the capability choice accepted on 19 October 2026.
The [committed receipt report](../delivery/call-receipts.md#approved-capability-contract--19-october-2026) explains its evidence and limits.
These acceptances close the candidate contract questions, as mapped in the [requirement register](../../spec/requirements.md).
They do not constitute publication approval or the final candidate freeze.

Receipts require a learner-controlled confirmation path, a protected verifier and durable replay protection outside tutor authority.
No actual host has been qualified.
Unsupported hosts retain unverified calls, which cannot settle objectives.
Records must not contain private answers, conversations, code, file contents, their hashes, credentials or learner identifiers.

## Publication and freeze gates

The [Pages workflow](../../.github/workflows/pages.yml) checks source, builds the site and uploads only its tested production artefact.
Deployment requires the exact publication branch or main and the `github-pages` environment.
The owner must configure required environment reviewers before allowing that deployment branch to run.
The environment reviewer must approve the precise workflow commit.
A preliminary draft PR may use a review-only branch while this protection is absent.

Read-only checks refreshed on 22 October 2026 found the repository public and Pages configured for workflow deployment.
Pages reports HTTPS enforcement at `https://agentcourses.github.io/agentcourses/`, with no custom domain and no reported build status.
The `github-pages` environment permits only `main`, has no required reviewers and allows administrator bypass.
The main branch has no branch protection, and the rulesets API returns an empty list.
These observations describe current settings; they do not authorise deployment or the candidate freeze.
DNS still points to `34.216.117.25` and `54.149.79.189`, with no AAAA or CNAME records.
Nameservers are `launch1.spaceship.net` and `launch2.spaceship.net`; DNS edit authority remains unverified.
Required owner reviewers, deployment-branch policy, release protection, custom-domain setup and exact DNS changes remain separate owner gates.
Local checks cannot establish those settings or HTTPS readiness.

After deployment, verify all nine pages, their canonical URLs, response types and every built page, schema and asset byte.
Record the exact workflow commit, source tree, manifest checksum, deployment run and output digest in external execution evidence.
Present that evidence for the owner's separate freeze decision before creating a protected tag or prerelease record.
The approval record must bind the candidate, exact clean commit and tree, manifest checksum, deployment and attributable owner decision.
Do not edit this source merely to add later deployment or freeze evidence.

After merge, verify the exact fetched main commit and its successful ordinary checks.
Its source tree must equal the frozen tag's tree.
Dispatch `prove_failure=true` on that same main commit and confirm `missing-link` fails ordinary `make check`.
Upload and deployment must be skipped, with no Pages artefact, deployment or environment request.
Complete a normal protected deployment and repeat the frozen-reference, approval and live-byte verification before declaring publication complete.

## Downstream handoff

The [specification](../../spec/format.md), [schemas](../../schemas/manifest.json) and [examples](../../examples/quickstart/COURSE.md) describe the candidate for downstream implementation.
The [author quickstart](../../site/src/content/docs/authors/quickstart.mdx) and [runner guidance](../../site/src/content/docs/implementers/support.mdx) explain their intended use.
Stable launch still needs the reference library, public validator, conformance classes and suite, qualified hosts, pilot evidence and learner outcomes.
Package publication and runtime support remain later work.
