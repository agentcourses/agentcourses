# Conformance

The conformance suite checks that a runner reads courses the way the [specification](../spec/specification.md) says. It covers reading: lesson order, lesson ids, phases, check defaults, evidence kinds, project options and quizzes. It also checks that a runner refuses invalid courses. Teaching behaviour, such as waiting at gates or never deciding a call, cannot be tested this way. The [runner checklist](runner-checklist.md) covers those duties.

## Run the suite

Give the suite an *adapter*: a command that reads one course folder and prints JSON. The suite runs `<adapter> <course-folder>` once for every case.

```bash
agentcourses conformance --adapter "my-runner describe"
```

The reference reading comes from the `agentcourses` command itself:

```bash
agentcourses conformance --adapter "agentcourses describe"
```

## What the adapter prints

For a valid course, the adapter prints the runner's reading. Lessons appear in teaching order. Absent optional values are `null`.

```json
{
  "valid": true,
  "name": "build-an-agent",
  "spec": "0.1",
  "project": ["own"],
  "phases": [{ "title": "Basics", "lessons": ["meet-the-agent", "add-a-tool"] }],
  "lessons": [
    {
      "id": "add-a-tool",
      "title": "Add a tool",
      "stage": "build",
      "checks": [
        {
          "id": "tool-registered",
          "kind": "command",
          "run": "python \"$AGENT_LESSON_DIR/checks/tool_registered.py\"",
          "scope": null,
          "required": true,
          "timeout": 30,
          "network": false
        }
      ],
      "calls": [],
      "objectives": [{ "id": "agent-has-tool", "evidence": "checked" }],
      "explain_back": false,
      "quiz": 0
    }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `project` | The project options in order, with `own` when the field is omitted. |
| `phases` | Each phase's title and lesson ids, or `[]` when the course has no phases. |
| `checks` | Every check with its defaults filled in. |
| `calls` | The call ids in the lesson. |
| `objectives` | Each objective id with its evidence kind: `checked`, `observed` or `explained`. |
| `explain_back` | Whether the lesson has an `## Explain back` section. |
| `quiz` | The number of quiz questions. |

For a course the runner refuses, the adapter prints `{"valid": false}`. It may add an `errors` list with its own codes.

## How results are compared

Each case folder holds one course and an `expected.json` file. Every key in `expected.json` must match the adapter's output. Keys the adapter adds are ignored. Lists must match in full and in order.

Cases numbered from `20` are courses a runner must refuse.
