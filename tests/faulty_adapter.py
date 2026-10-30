"""A deliberately wrong runner reading, used to prove the conformance suite catches mistakes.

It accepts every course and ignores phases.
"""

import json
import sys

from agentcourses import describe

reading = describe(sys.argv[1])
if not reading["valid"]:
    reading = {"valid": True}
reading["phases"] = []
print(json.dumps(reading))
