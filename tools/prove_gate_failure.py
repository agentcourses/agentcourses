"""Prepare a source-only broken tree or prove the ordinary gate rejects it."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def prepare(destination):
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("Destination must be absent or empty")
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("README.md", "AGENTS.md", "REVIEW.md", "CLAUDE.md", "LICENSE", ".node-version"):
        if (ROOT / name).is_file(): shutil.copy2(ROOT / name, destination / name)
    for name in ("spec", "docs", "examples", "site/src/content/docs"):
        source = ROOT / name
        if source.is_dir(): shutil.copytree(source, destination / name, dirs_exist_ok=True)
    (destination / "tools").mkdir(exist_ok=True)
    shutil.copy2(ROOT / "tools/document-stage.json", destination / "tools/document-stage.json")
    with (destination / "README.md").open("a") as stream:
        stream.write("\n[Deliberately broken gate proof](gate-proof-absent-target.md)\n")
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", type=Path)
    args = parser.parse_args()
    if args.prepare_only:
        try: prepare(args.prepare_only)
        except (OSError, ValueError) as exc: parser.error(str(exc))
        print(f"Prepared broken document tree: {args.prepare_only}")
        return 0
    with tempfile.TemporaryDirectory(prefix="agentcourses-broken-") as temporary:
        destination = prepare(Path(temporary))
        result = subprocess.run(["make", "check", f"CHECK_ROOT={destination}"], cwd=ROOT, text=True, capture_output=True)
        if result.returncode == 0 or "missing-link" not in result.stderr or "gate-proof-absent-target.md" not in result.stderr:
            print(result.stdout + result.stderr, file=sys.stderr)
            print("Gate failure proof did not observe the intended missing-link rejection", file=sys.stderr)
            return 1
        print(f"Ordinary make check exited {result.returncode}; missing-link rejected gate-proof-absent-target.md before tests/build")
    return 0


if __name__ == "__main__":
    sys.exit(main())
