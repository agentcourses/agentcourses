# Agent Courses

Agent Courses is an open course specification under preparation. This repository currently provides its internal documentation checks and a minimal documentation shell. The contract, examples and guides arrive through reviewed themes. Nothing here qualifies a runner or provides a public validator.

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

Course registers use Markdown tables with `Delivery owner` (`course`, `records`, `schemas`) and `State` (`resolved`, `pending`) columns.
A pending course row needs `Question`, `Source` and `Why waits`; unresolved cells contain plain `pending`.
Only records may own pending questions: receipts, call events, replay/recovery, settlement, followed-field, identity, schema addresses, naming or freeze qualification.
Resolved contract rows require `Normative`, `Valid example`, `Invalid example`, `Reason` and `Owner review`.
Resolved requirement rows require `Normative` and `Example` links.
A later schema proof owner may be assigned without claiming an executed proof.
Records activation permits no pending contract rows.
The receipt experiment report is allowed at foundation and mandatory at records.
Identity vector manifests name source files with `input` or `input_path`, relative to their manifest.

## Documentation collections

Production initially contains only the overview at `/` and Starlight's generated error page.
Navigation comes from the source map, so no future page slug is advertised.
The author, runner and candidate themes activate their routes through the stage marker.
`ExampleCode.astro` reads an `example`, `file` and `lang` from repository examples; it never executes them.
Example names are lowercase kebab-case directories; file paths must remain inside that example, including after resolving symlinks.

`AC_SITE_MODE=design` reads only `site/tests/design/fixtures`, using the same docs schema.
An explicit design build requires `index.mdx`, `specification.mdx`, `runners.mdx`, four author pages and two implementer pages.
Missing fixtures fail rather than falling back to production.
When design fixtures arrive, `make check` builds and tests both collections and restores the production build last.
Until then, the foundation proves production only.

## Contributing and operations

Read [the working conventions](AGENTS.md) and [the independent review guide](REVIEW.md).
The owner reviews the complete diff before commits, then merges reviewed pull requests.
The Actions status is named `make check`; its workflow runs on pull requests and main pushes with full tag history.
CI proof remains pending until an authorised commit and push runs that workflow.
The owner has deferred branch protection and public visibility until v1 is ready; neither is claimed configured.
Pages is absent and DNS edit authority remains unverified; publication is a later theme.
Owned material is licensed under [Apache-2.0](LICENSE).
