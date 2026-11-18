"""A deliberately wrong runner reading, used to prove the conformance suite catches mistakes.

It accepts every course, ignores 0.1 phases and 0.2 additions, and recognises
teaching and homework in 0.1 courses.
"""

import json
import sys

from agentcourses import describe

reading = describe(sys.argv[1])
if not reading["valid"]:
    reading = {"valid": True}
else:
    legacy = reading["spec"] == "0.1"
    reading["teaching"] = legacy
    if legacy:
        reading["phases"] = []
    else:
        for phase in reading["phases"]:
            phase.pop("closing", None)
    for lesson in reading["lessons"]:
        lesson["homework"] = legacy
        lesson["preferences"] = {}
print(json.dumps(reading))
