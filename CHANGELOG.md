# Changelog

This changelog records the proposed first Agent Courses candidate.
The candidate label, publication and freeze remain subject to owner approval.
Stable launch, package installation and host qualification remain later work.

## Proposed 1.0.0-rc.1 — awaiting publication and freeze

The candidate combines the [course format](spec/format.md), [execution rules](spec/execution.md), [consent](spec/consent.md), [records](spec/records.md) and [identity](spec/identity.md).
The [source manifest](schemas/manifest.json) binds eight versioned schema addresses to flat source files and exact SHA-256 checksums.
The [quickstart course](examples/quickstart/COURSE.md) supplies repository examples for author guidance.
Nine site pages provide the overview, specification, runner showcase, author guidance and implementer guidance.

The [publication workflow](.github/workflows/pages.yml) runs ordinary checks and uploads the tested production site before protected deployment.
A manual failure-proof dispatch must reject an injected missing link and skip upload and deployment.
The [candidate handoff](docs/releases/candidate.md) records accepted contract evidence, pending publication controls and the separate freeze process.
The proposed tag is `agentcourses-v1.0.0-rc.1`; no release tag or public schema availability is claimed yet.

No actual host is qualified, and this candidate provides no public validator or conformance certification.
The reference library, validator, conformance suite, pilot and learner evidence remain stable-launch obligations.
