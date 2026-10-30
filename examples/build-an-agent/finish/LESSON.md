---
title: Explain what you built
stage: demonstrate
minutes: 15
checks:
  - id: agent-answers
    run: python "$AGENT_LESSON_DIR/checks/agent_answers.py"
    verify: answer() returns text for a request with and without a tool.
    timeout: 30
  - id: names-are-clear
    kind: observe
    scope: [agent.py]
    verify: The tool and answer functions have names that say what they do.
    required: false
calls:
  - id: choose-failure
    ask: Which way could your agent fail that you most want to guard against?
objectives:
  - id: agent-works
    text: Your agent answers requests with and without its tool.
    by: agent-answers
  - id: agent-explained
    text: You can explain how your agent decides to use its tool.
    by: explain-back
---

## Goal

You can show your agent works, and explain how it decides to use its tool.

## Build

Run the checks with the learner. If one fails, read the message together and fix the cause.

Put the `choose-failure` call to the learner. Help them add one line to `agent.py` that guards against the failure they chose.

## Explain back

Ask the learner to explain, in their own words, how `answer` decides whether to call the tool, what it returns, and the failure they guarded against.
