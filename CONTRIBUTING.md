# Contributing to Agent Courses

Thank you for helping. Agent Courses is in beta, so feedback from real courses and real runners matters most.

## Questions and proposals

Open an [issue](https://github.com/agentcourses/agentcourses/issues) for a question, a problem or a proposal. Start a proposal from a real problem you met while writing a course or building a runner, and show how your change solves it.

The bar for additions is high. Adding to a specification is easy; removing from it is hard. A good addition:

- helps more than one course;
- reads the same way in every runner;
- can be checked by `agentcourses validate`, or is clearly a runner duty.

Runner-specific settings belong under the runner's own key in `metadata` until a second runner needs them.

## Changing the repository

| To change | Edit | Then |
| --- | --- | --- |
| A rule | `spec/specification.md` | Update `schemas/`, the validator and a test that proves the rule. |
| A frontmatter shape | `schemas/` | Update the specification's field table. |
| An example | `examples/` | It must validate with no warnings and its fixtures must pass. |
| Conformance | `conformance/cases/` | The reference reading must pass and the faulty one must fail. |
| The site | `site/src/content/docs/` | The specification page is rendered from `spec/`; do not copy it. |

## Checks

Install [uv](https://docs.astral.sh/uv/), Node.js 22 or later and pnpm 10, then run:

```bash
make check
```

It must exit zero before you open a pull request.

## Licence

By contributing, you agree that your contribution is licensed under [Apache-2.0](LICENSE).
