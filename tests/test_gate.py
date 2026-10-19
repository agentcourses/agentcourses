from pathlib import Path
import subprocess
from test_workspace import fixture, write

ROOT = Path(__file__).parents[1]


def test_gate_propagates_named_document_failure(tmp_path):
    fixture(tmp_path)
    write(tmp_path, "README.md", "[Broken](does-not-exist.md)\n")
    for target in ("check-docs", "check"):
        result = subprocess.run(["make", target, f"CHECK_ROOT={tmp_path}"], cwd=ROOT, capture_output=True, text=True)
        assert result.returncode != 0
        assert "missing-link" in result.stderr
        assert "pytest -q" not in result.stdout
        assert "astro build" not in result.stdout


def test_prepare_only_exposes_real_failing_gate(tmp_path):
    destination = tmp_path / "broken"
    result = subprocess.run([str(ROOT / ".venv/bin/python"), "tools/prove_gate_failure.py", "--prepare-only", str(destination)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run(["make", "check", f"CHECK_ROOT={destination}"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode != 0 and "missing-link" in result.stderr
