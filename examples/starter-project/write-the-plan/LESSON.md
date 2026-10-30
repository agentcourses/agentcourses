---
title: Write the plan
stage: build
checks:
  - id: plan-has-steps
    run: python "$AGENT_LESSON_DIR/checks/plan_has_steps.py"
    verify: plan.md lists at least three numbered steps.
calls:
  - id: choose-first-step
    ask: Which step should come first, and why?
objectives:
  - id: plan-written
    text: You wrote a plan with at least three steps.
    by: plan-has-steps
---

## Goal

You have a written plan with at least three concrete steps.

## Build

This lesson adds `plan.md` to the project. Ask the learner for their idea, then help them break it into steps. Put the `choose-first-step` call to them before writing the steps down.
