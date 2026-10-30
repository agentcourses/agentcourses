---
title: Finish
stage: demonstrate
checks:
  - id: runs
    run: python check.py
    verify: It runs.
  - id: looks-right
    kind: observe
    scope: [app.py]
    verify: It reads well.
    required: false
    timeout: 10
    network: true
---

## Goal

Do it.

## Explain back

Explain it.
