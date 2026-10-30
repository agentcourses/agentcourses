"""Pass when agent.py has a TOOLS mapping or list naming a top-level function.

Reads the file without running it.
"""
import ast
import json
from pathlib import Path


def report(status, message, fix=""):
    print(json.dumps({"status": status, "path": "agent.py", "message": message, "fix": fix}))
    raise SystemExit(0 if status == "pass" else 1)


try:
    tree = ast.parse(Path("agent.py").read_text(encoding="utf-8"))
except FileNotFoundError:
    report("fail", "agent.py does not exist.", "Create agent.py in the project folder.")
except SyntaxError as error:
    report("fail", f"agent.py has a syntax error on line {error.lineno}.", "Fix the syntax error.")

functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
for node in tree.body:
    if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "TOOLS" for t in node.targets):
        values = node.value.values if isinstance(node.value, ast.Dict) else getattr(node.value, "elts", [])
        if any(isinstance(value, ast.Name) and value.id in functions for value in values):
            report("pass", "TOOLS names a tool function.")
        report("fail", "TOOLS names no function defined in agent.py.", "Add your tool function to TOOLS.")
report("fail", "agent.py has no TOOLS.", 'Add TOOLS = {"name": your_function} to agent.py.')
