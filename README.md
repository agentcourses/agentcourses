# Agent Courses

Agent Courses defines a course format for AI tutors, with a specification, schemas, examples and nine documentation pages.
The proposed first candidate is `1.0.0-rc.1`; its label still needs owner confirmation.
Publication will use `https://agentcourses.github.io/agentcourses/` after owner merge; the separate candidate freeze remains pending.
Read the [candidate handoff](docs/releases/candidate.md) for accepted contracts, remaining gates and downstream obligations.
Nothing here qualifies a runner or provides a public validator.

## Candidate sources

Start with the [course format](spec/format.md), [execution contract](spec/execution.md), [records](spec/records.md) and [identity](spec/identity.md).
The [schema manifest](schemas/manifest.json) lists the eight proposed versioned addresses and exact source checksums.
The [quickstart course](examples/quickstart/COURSE.md) and [author quickstart](site/src/content/docs/authors/quickstart.mdx) show the format in use.
The [changelog](CHANGELOG.md) records the current candidate preparation.
These are repository artefacts; schema hosting, protected release tags and package installation are not yet available.

The proposed release tag is `agentcourses-v1.0.0-rc.1`.
Once the owner approves the freeze, that tag will identify the reviewed source without changing published schema bytes.
The [Pages workflow](.github/workflows/pages.yml) builds with ordinary checks before uploading its production artefact.
After owner merge, the main workflow deploys to the default GitHub Pages address.
The owner will configure DNS manually later; custom-domain publication and the candidate freeze remain separate work.

## Install and check

Use Python 3.12.11, uv 0.9.9, Node 24.22.0 from [.node-version](.node-version), and pnpm 10.27.0.
Install those runtimes before running these commands from the repository root:

```bash
uv lock --check
uv sync --locked --python 3.12.11
pnpm --dir site install --frozen-lockfile
PLAYWRIGHT_BROWSERS_PATH="$PWD/site/.browsers" pnpm --dir site exec playwright install chromium
make check
uv run --locked python tools/prove_gate_failure.py
```

Linux CI installs Chromium system dependencies with `playwright install --with-deps chromium`.
The gate inspects documents first, checks the lock, runs Python tests, checks and builds Astro, then opens the built overview in Chromium.
Playwright proves the built overview opens with active navigation; axe is installed for the separate design acceptance suite.
No account, model credential or paid call is required.

## Source contracts

[The stage marker](tools/document-stage.json) explicitly activates cumulative document groups.
Stages advance in this order: `foundation`, `course`, `records`, `authors`, `runners`, `candidate`.
Deleting files cannot lower the declared stage or the reviewed baseline.
Set `DOCS_BASE_REF` to the immutable predecessor commit; local checks default to `HEAD`.
CI uses the pull request merge base or the preceding main commit.
Only the reviewed nine-file seed may lack a baseline marker.

```bash
make check-docs CHECK_ROOT=/absolute/source/tree
uv run --locked python tools/check_docs.py --scope course
uv run --locked python tools/check_docs.py --site-map
uv run --locked python tools/prove_gate_failure.py --prepare-only /tmp/fresh-broken-tree
make check CHECK_ROOT=/tmp/fresh-broken-tree
```

The final command must fail with `missing-link`.
Inspection exits zero on success, one for findings and two for invalid arguments.
Each finding names its rule, source path and problem.
The map command writes only JSON to stdout and reads active canonical specification sources without generated pages.
Explicit HTML IDs map source roots to `/specification/#format` and source fragments to `/specification/#format--course-folder`.
The other canonical stems are `execution`, `consent`, `records` and `identity`.
Public guides may use these mapped targets before composition exists; other links require present routes.

The [requirement register](spec/requirements.md) uses Markdown tables with `Delivery owner` (`course`, `records`, `schemas`) and `State` (`resolved`, `pending`) columns.
A pending requirement row needs `Question`, `Source` and `Why waits`; unresolved cells contain plain `pending`.
Only records may own pending questions: receipts, call events, replay/recovery, settlement, followed-field, identity, schema addresses, naming or freeze qualification.
Resolved requirement rows require `Normative` and `Example` links.
A later schema proof owner may be assigned without claiming an executed proof.
Records activation permits no pending requirement rows.
The documentation gate reads only this repository; no strategy checkout or resolution history is required.
The receipt experiment report is allowed at foundation and mandatory at records.
Identity vector manifests name source files with `input` or `input_path`, relative to their manifest.

## Documentation collections

Production contains the overview, specification, runner showcase, four author pages and two implementer pages.
Navigation follows the active source map and candidate stage marker.
The generated specification composes five canonical sources; ignored schema downloads come from the manifest and complete release tags.
`ExampleCode.astro` reads an `example`, `file` and `lang` from repository examples; it never executes them.
Example names are lowercase kebab-case directories; file paths must remain inside that example, including after resolving symlinks.

`AC_SITE_MODE=design` reads only `site/tests/design/fixtures`, using the same docs schema.
An explicit design build requires `index.mdx`, `specification.mdx`, `runners.mdx`, four author pages and two implementer pages.
Missing fixtures fail rather than falling back to production.
`make check` builds and tests both collections and restores the production build last.

## Contributing and operations

Read [the working conventions](AGENTS.md) and [the independent review guide](REVIEW.md).
Independent review and passing checks precede draft pull request publication; the owner reviews and merges the pull request.
The Actions status is named `make check`; its workflow runs on pull requests and main pushes with full tag history.
The publication workflow deploys main pushes and main-only manual dispatches through the `github-pages` environment.
Ordinary pull request events and publication branches cannot deploy.
The owner has chosen the default address, `https://agentcourses.github.io/agentcourses/`, for the initial publication.
After merge, verify the normal deployment, exact live bytes and the controlled failure that must skip upload and deployment.
Those checks remain pending; preparing the pull request does not complete publication.
Read-only checks on 22 October 2026 found workflow Pages, no custom domain and an environment limited to `main`.
The environment has no required reviewers and allows administrator bypass.
Main protection remains deferred by the owner; no settings change is part of this publication adjustment.
The candidate freeze, protected tag, prerelease record and later custom-domain setup retain their separate owner gates.

Production defaults to the fixed `github-pages` deployment profile, including the `/agentcourses/` base.
Use `AC_DEPLOYMENT=custom-domain` for a future root build at `https://agentcourses.io/`; deployment needs separate owner authorisation.
`AC_SITE_MODE=design` keeps its existing root preview in either profile.
The build and browser checks must use the same profile.
After a clean, committed production build, verify the deployed artefact with:

```bash
node site/scripts/verify-release.mjs --root . --url https://agentcourses.github.io/agentcourses/
```

This checks temporary download locations while preserving permanent `https://agentcourses.io/schemas/` identifiers inside the payloads.
It does not establish that those permanent addresses are live.
Owned material is licensed under [Apache-2.0](LICENSE).
