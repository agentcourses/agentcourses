"""Immutable authored inputs from the internal retained-snapshot proof."""
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


@pytest.fixture
def course(tmp_path):
    root = tmp_path / 'sample-course'
    section = (ROOT / 'tests/contracts/fixtures/historical/records.md').read_text().split('<details><summary>Exact authored files for sample-course</summary>')[1].split('</details>')[0]
    for name, payload in re.findall(r'`([^`]+)`:\n\n```[^\n]*\n(.*?)```', section, re.S):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload.encode())
    assert len(list(root.rglob('*.*'))) >= 9
    return root
