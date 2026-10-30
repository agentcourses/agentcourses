"""Pass when plan.md lists at least three numbered steps with text."""
import json
import re
from pathlib import Path

try:
    text = Path("plan.md").read_text(encoding="utf-8")
except FileNotFoundError:
    text = ""
steps = re.findall(r"^\s*\d+\.\s+\S", text, flags=re.MULTILINE)
passed = len(steps) >= 3
print(json.dumps({
    "status": "pass" if passed else "fail",
    "path": "plan.md",
    "message": f"plan.md has {len(steps)} numbered steps.",
    "fix": "" if passed else "Add numbered steps until there are at least three.",
}))
raise SystemExit(0 if passed else 1)
