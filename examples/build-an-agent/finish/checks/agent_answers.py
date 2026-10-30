"""Pass when answer() returns text for a request with and without a tool.

Imports agent.py from the project, which runs the learner's own code.
"""
import importlib.util
import json
import sys
from pathlib import Path


def report(status, message, fix=""):
    print(json.dumps({"status": status, "path": "agent.py", "message": message, "fix": fix}))
    raise SystemExit(0 if status == "pass" else 1)


path = Path("agent.py")
if not path.exists():
    report("fail", "agent.py does not exist.", "Create agent.py in the project folder.")
spec = importlib.util.spec_from_file_location("agent", path)
agent = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(Path.cwd()))
try:
    spec.loader.exec_module(agent)
except Exception as error:  # the learner's code may raise anything on import
    report("fail", f"agent.py raised {type(error).__name__} when imported.", "Run python agent.py and fix the error.")

answer = getattr(agent, "answer", None)
tools = getattr(agent, "TOOLS", None)
if not callable(answer):
    report("fail", "agent.py has no answer() function.", "Add def answer(request): ... to agent.py.")
if not tools:
    report("fail", "agent.py has no TOOLS.", "Register your tool in TOOLS.")

name = next(iter(tools)) if isinstance(tools, dict) else getattr(tools[0], "__name__", "")
for request in (f"please use {name}", "hello"):
    try:
        result = answer(request)
    except Exception as error:
        report("fail", f"answer({request!r}) raised {type(error).__name__}.", "Make answer() handle every request.")
    if not isinstance(result, str):
        report("fail", f"answer({request!r}) returned {type(result).__name__}, not text.", "Return a string.")
report("pass", "answer() returns text with and without a tool.")
