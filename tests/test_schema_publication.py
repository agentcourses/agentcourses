"""A clean site build keeps published schema addresses immutable."""

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]
PUBLISHED_0_1 = "616002d0869870fc9fc6a1cca17887f28d55f645"


def test_clean_site_serves_both_schema_versions():
    output = ROOT / "site/public/schemas"
    shutil.rmtree(output, ignore_errors=True)
    output.mkdir(parents=True)
    stale = output / "stale.json"
    stale.write_text("{}", encoding="utf-8")
    subprocess.run(["node", "site/scripts/copy-schemas.mjs"], cwd=ROOT, check=True)
    assert not stale.exists()
    names = {p.name for p in (ROOT / "schemas").glob("*.json")}
    assert {p.name for p in output.iterdir()} == {"0.1", "0.2"}
    for version in ("0.1", "0.2"):
        assert {p.name for p in (output / version).iterdir()} == names
        for name in names:
            schema = output / version / name
            assert json.loads(schema.read_text())["$id"] == (
                f"https://agentcourses.io/schemas/{version}/{name}"
            )
            expected = (
                subprocess.check_output(
                    ["git", "show", f"{PUBLISHED_0_1}:schemas/{name}"], cwd=ROOT
                )
                if version == "0.1"
                else (ROOT / "schemas" / name).read_bytes()
            )
            assert schema.read_bytes() == expected
