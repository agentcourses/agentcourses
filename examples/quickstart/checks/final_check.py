"""Check that the fixture project declares an agent without importing its code."""
import ast
import json
from pathlib import Path

path = Path('agent.py')
try:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    passed = any(
        isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(isinstance(target, ast.Name) and target.id == 'agent'
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target]))
        for node in tree.body
    )
except (OSError, UnicodeError, SyntaxError):
    passed = False
print(json.dumps({
    'check': 'final-check',
    'status': 'pass' if passed else 'fail',
    'path': 'agent.py',
    'line': 1,
    'message': 'Agent declared.' if passed else 'No agent declaration found.',
    'fix': 'Define an agent variable in agent.py.' if not passed else '',
}))
raise SystemExit(0 if passed else 1)
