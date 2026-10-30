---
title: Add a tool
stage: build
minutes: 20
checks:
  - id: tool-registered
    run: python "$AGENT_LESSON_DIR/checks/tool_registered.py"
    verify: agent.py lists at least one tool function in TOOLS.
    timeout: 30
objectives:
  - id: agent-has-tool
    text: Your agent can call a tool you wrote.
    by: tool-registered
---

## Goal

Your agent can call a Python function you wrote, and you can see when it does.

## Build

Create `agent.py` with the learner, or extend it if it exists. Show each change and say why.

1. Write the tool the learner chose as a plain function.
2. Add it to a `TOOLS` dictionary that maps a name to the function.
3. Write `answer(request)`, which picks a tool when the request mentions its name and returns the result as text.

Let the learner try a request that uses the tool and one that does not.

## Hints

1. `TOOLS = {"time": tell_time}` registers one tool called `time`.
2. `answer` should return a string in both cases: with and without a tool.
