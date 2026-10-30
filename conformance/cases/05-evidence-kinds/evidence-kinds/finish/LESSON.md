---
title: Finish
stage: demonstrate
checks:
  - id: runs
    run: python check.py
  - id: reads-well
    kind: observe
    scope: [app.py]
    verify: It reads well.
calls:
  - id: pick-name
    ask: What should it be called?
objectives:
  - id: it-runs
    text: It runs.
    by: runs
  - id: it-reads
    text: It reads well.
    by: reads-well
  - id: it-explained
    text: You explain it.
    by: explain-back
---

## Goal

Do it.

## Explain back

Explain it.
