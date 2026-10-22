from pathlib import Path
import importlib.util
import re
import subprocess
import sys

import pytest
from test_workspace import checker

ROOT = Path(__file__).parents[1]
INJECTION = "\n[Deliberately broken gate proof](gate-proof-absent-target.md)\n"
EXPECTED = {
    "rule": "missing-link", "path": "README.md",
    "message": "Missing or unsafe local target: gate-proof-absent-target.md",
}
EXPECTED_LINE = f'{EXPECTED["path"]}: {EXPECTED["rule"]}: {EXPECTED["message"]}'


def assert_document_failure(result, expected):
    assert result.returncode != 0
    lines = result.stderr.splitlines()
    assert lines[:-1] == expected, "ordinary gate must report exactly the expected document findings"
    assert re.fullmatch(r"(?:g?make)(?:\[\d+\])?: \*\*\* \[(?:[^\]\n]+: )?check-docs\] Error 1", lines[-1])
    assert "pytest -q" not in result.stdout
    assert "astro build" not in result.stdout


def test_gate_propagates_named_document_failure(tmp_path):
    destination = tmp_path / "broken"
    result = subprocess.run([sys.executable, "tools/prove_gate_failure.py", "--prepare-only", str(destination)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    readme = destination / "README.md"
    readme.write_text(readme.read_text().replace("gate-proof-absent-target.md", "does-not-exist.md"))
    for target in ("check-docs", "check"):
        result = subprocess.run(["make", target, f"CHECK_ROOT={destination}"], cwd=ROOT, capture_output=True, text=True)
        assert_document_failure(result, [EXPECTED_LINE.replace("gate-proof-absent-target.md", "does-not-exist.md")])


def test_prepare_only_exposes_real_failing_gate(tmp_path):
    destination = tmp_path / "broken"
    result = subprocess.run([sys.executable, "tools/prove_gate_failure.py", "--prepare-only", str(destination)], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert checker().check_tree(destination, "candidate") == [EXPECTED], "prepared proof tree must contain only the injected missing-link"
    result = subprocess.run(["make", "check", f"CHECK_ROOT={destination}"], cwd=ROOT, capture_output=True, text=True)
    assert_document_failure(result, [EXPECTED_LINE])
    readme = destination / "README.md"
    readme.write_text(readme.read_text().removesuffix(INJECTION))
    assert checker().check_tree(destination, "candidate") == [], "copied proof tree must close before injection"


def test_ordinary_proof_helper_observes_exact_failure():
    result = subprocess.run([sys.executable, "tools/prove_gate_failure.py"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stderr == ""
    assert re.fullmatch(r"Ordinary make check exited [1-9]\d*; missing-link rejected gate-proof-absent-target.md before tests/build\n", result.stdout)


@pytest.mark.parametrize("label,returncode,findings", [
    ("extra-finding", 2, [EXPECTED_LINE, "README.md: missing-link: Missing or unsafe local target: another.md"]),
    ("unrelated-error", 2, [EXPECTED_LINE, "uv: environment unavailable"]),
    ("wrong-source", 2, [EXPECTED_LINE.replace("README.md:", "OTHER.md:")]),
    ("missing-make-failure", 2, [EXPECTED_LINE]),
    ("successful-gate", 0, [EXPECTED_LINE]),
])
def test_proof_helper_rejects_contaminated_results(tmp_path, monkeypatch, label, returncode, findings):
    monkeypatch.syspath_prepend(str(ROOT / "tools"))
    spec = importlib.util.spec_from_file_location("gate_proof", ROOT / "tools/prove_gate_failure.py")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    monkeypatch.setattr(sys, "argv", ["prove_gate_failure.py"])
    monkeypatch.setattr(helper, "prepare", lambda destination: destination)
    stderr = "\n".join(findings) + "\n"
    if label != "missing-make-failure":
        stderr += "make: *** [check-docs] Error 1\n"
    monkeypatch.setattr(helper.subprocess, "run", lambda *args, **kwargs: subprocess.CompletedProcess(args, returncode, "", stderr))
    assert helper.main() == 1, "proof helper must reject every contaminated or unsuccessful observation"
