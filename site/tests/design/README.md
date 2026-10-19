# Documentation design suite

This folder proves the Agent Courses documentation design with fixed sample pages, so the look can be reviewed before real content exists. `AC_SITE_MODE=design` builds only the nine fixtures here; the default production build never includes them. The fixtures are sample text, never public documentation or specification text.

## Run it

```bash
AC_SITE_MODE=design pnpm --dir site run build
AC_SITE_MODE=design pnpm --dir site exec playwright test tests/design
```

`make check` runs the same build and tests, then rebuilds production last.

| Spec | What it proves |
|---|---|
| `layout.spec.ts` | Phone and desktop layouts in both colour modes, with no sideways page scroll |
| `identity.spec.ts` | Local typefaces, type scale, neutral colours, the open-book mark, and the 640 and 620 pixel breakpoints |
| `navigation.spec.ts` | Nine destinations, the current page, the drawer at 980 pixels and below, and contents above 1240 pixels |
| `controls.spec.ts` | Search by button and shortcut, results and no results, and copy controls including refusal |
| `accessibility.spec.ts` | axe on every destination, focus rings measured against what surrounds them, reduced motion, keyboard-scrollable tables and code, and contrast |
| `screens.spec.ts` | Screenshot baselines at 390×844 and 1440×1000 in both modes, plus the open drawer |

## Screenshot baselines

Baselines live in `screens.spec.ts-snapshots/` and are macOS Chromium renders; on other systems the comparison is skipped. Update them only on purpose:

```bash
AC_SITE_MODE=design pnpm --dir site exec playwright test tests/design/screens.spec.ts --update-snapshots
```

An updated baseline is preparation for review, not approval. Inspect each image change before it lands.

## Seams for real content

Later content keeps these and needs nothing else from the design:

- **Layout.** The sidebar frame in `site/astro.config.mjs` labels and groups the nine destinations; each build passes Starlight only the routes its collection has. The frame, the component overrides in `site/src/components/` and the styles in `site/src/styles/` apply to any page in the `docs` collection.
- **Copy.** `CopyPage.astro` copies the page title, its frontmatter `description` and the rendered `.sl-markdown-content`. Mark anything inside an article that must not be copied with `data-copy-page-exclude`.
- **Content components.** `Stages.astro` and `RunnerTile.astro` draw stages and runner tiles from the props a page passes; they choose no wording.
