---
title: Meet the agent
stage: understand
minutes: 10
calls:
  - id: choose-tool
    ask: Which tool should your agent call first?
---

## Goal

You can say what an agent loop is, and which tool your agent will call first.

## Build

Explain the agent loop using the learner's own project. The agent reads a request, decides whether a tool would help, calls it, and uses the result.

Ask what small job the learner's agent could do with one tool. Put the `choose-tool` call to them and wait for their answer. Offer two or three safe options if they are stuck.

## Hints

1. A tool is an ordinary function that the agent may decide to call.
2. Good first tools are small and safe, such as telling the time or adding two numbers.

## Quiz

1. Who decides when a tool is called?
   - The person typing the request
   - The agent, based on the request
   - The Python interpreter
2. What makes a good first tool?
   - Something small, safe and easy to check
   - Something that deletes files
   - Something that needs a paid account
