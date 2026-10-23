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


def test_migration_preserves_old_snapshot(tmp_path):
    import shutil
    from test_candidates import prepare
    snapshot=ROOT/'tests/contracts/fixtures/rc1/quickstart'
    inventory=ROOT/'examples/manifest.json'
    assert snapshot.is_dir() and inventory.is_file(), 'migration-preserves-old-snapshot: absent retained fixture/inventory'
    before={p.relative_to(snapshot):p.read_bytes() for p in snapshot.rglob('*') if p.is_file()}
    entry=json.loads(inventory.read_text())['courses'][0]
    assert c.course_digest(snapshot)==entry['identity']
    target=tmp_path/'quickstart'
    shutil.copytree(snapshot,target)
    # Move declarations without changing the retained source.
    import yaml
    data,body=c.decode_markdown((target/'COURSE.md').read_text())
    data['format']='1.0.0-rc.2';data['checks']=c.decode_yaml((target/'checks/checks.yaml').read_text())
    (target/'checks/checks.yaml').unlink()
    shutil.move(str(target/'checks'),target/'scripts')
    for check in data['checks']:
        if 'run' in check:check['run']=check['run'].replace('/checks/','/scripts/')
    (target/'COURSE.md').write_text('---\n'+yaml.safe_dump(data,sort_keys=False)+'---\n'+body)
    assert c.course_digest(target)!=entry['identity']
    assert before=={p.relative_to(snapshot):p.read_bytes() for p in snapshot.rglob('*') if p.is_file()}
