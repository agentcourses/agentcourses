"""Independent expected digests come from the unchanged public vector manifest."""
import hashlib
import json
from pathlib import Path

import pytest

from tools import check_contracts as c

ROOT=Path(__file__).resolve().parents[2]


def test_identity_vectors():
    outcomes=c.identity_vectors(ROOT)
    assert len(outcomes)==45
    assert all(result['status']=='passed' for result in outcomes), outcomes


def test_identity_worked_hex(tmp_path):
    (tmp_path/'COURSE.md').write_bytes(b'hi\n')
    (tmp_path/'fail').mkdir()
    (tmp_path/'go').symlink_to('COURSE.md')
    # Public worked example was checked independently with shasum.
    assert c.course_digest(tmp_path)=='sha256:70dc1a84f335a8118e54c7d38a2088551bf13add821f0c5f6666e1593a446a75'


def test_identity_full_path_limit():
    path='/'.join(['a'*255]*4)
    c._path_check(path)
    with pytest.raises(c.ContractError,match='invalid-path'):
        c._path_check(path+'/xx')


def test_identity_independent_framing():
    vector=json.loads((ROOT/'fixtures/identity/worked.json').read_text())
    assert 'sha256:'+hashlib.sha256(bytes.fromhex(vector['framed_hex'])).hexdigest()==vector['expected_digest']
