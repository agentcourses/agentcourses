"""Candidate schema proofs; no schema retrieval is permitted."""
import json
import sys
from pathlib import Path

import pytest
from referencing.exceptions import Unresolvable
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def contracts():
    from tools import check_contracts
    return check_contracts


def test_schema_registry():
    c = contracts()
    schemas, registry = c.schema_registry(ROOT, '1.0.0-rc.1')
    assert set(schemas) == set(c.KINDS)
    assert len(schemas) == 8
    for kind, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        assert schema['$id'] == f'https://agentcourses.io/schemas/1.0.0-rc.1/{kind}.schema.json'
        registry.resolver().lookup(schema['$id'])
    with pytest.raises(Unresolvable):
        registry.resolver().lookup('https://unavailable.invalid/never-fetch.json')


def test_schema_cases_decode():
    c = contracts()
    assert c.decode_yaml('name: sample\n') == {'name': 'sample'}
    for text in ('name: first\nname: second\n', '!!python/object:os.PathLike {}', 'x: &x [*x]'):
        with pytest.raises(c.ContractError):
            c.decode_yaml(text)
    assert c.decode_markdown('---\npass: 2 of 3\n---\n- criterion\n') == ({'pass': '2 of 3'}, '- criterion\n')
    for text in ('', '---\nx: 1\n', '---\n- list\n---\nbody'):
        with pytest.raises(c.ContractError):
            c.decode_markdown(text)


def test_schema_cases():
    c = contracts()
    cases = json.loads((ROOT / 'fixtures/schema/cases.json').read_text())
    assert {case['kind'] for case in cases if case['outcome'] == 'accepted'} == set(c.KINDS)
    assert {case['kind'] for case in cases if case['outcome'] == 'rejected'} == set(c.KINDS)
    for case in cases:
        assert case['requirement'].startswith('req-')
        findings = c.validate_frontmatter(case['kind'], case['data'],candidate=case['candidate'])
        errors = [f for f in findings if f.severity == 'error']
        if case['outcome'] == 'rejected':
            assert isinstance(case['finding'], dict), case['case']
            expected = case['finding']
            assert 'keyword' in expected or expected['rule'].startswith('req-'), case['case']
            assert any(c.matches_expected(f, expected) for f in errors), (case['case'], errors)
            if 'repair' in case:
                from copy import deepcopy
                repaired = deepcopy(case['data'])
                edit = case['repair']
                parent = repaired
                for key in edit['path'][:-1]:
                    parent = parent[key]
                key = edit['path'][-1]
                if edit['op'] == 'remove':
                    del parent[key]
                elif edit['op'] == 'add' and isinstance(parent, list):
                    parent.insert(key, edit['value'])
                else:
                    parent[key] = edit['value']
                assert not [f for f in c.validate_frontmatter(case['kind'], repaired,candidate=case['candidate']) if f.severity == 'error'], case['case']
            else:
                assert case.get('malformed') in ('null', 'empty', 'wrong-type'), case['case']
        else:
            assert not errors, (case['case'], findings)
            if case['outcome'] == 'warning':
                assert 'req-unknown-keys' in {f.rule for f in findings}, case['case']


@pytest.mark.parametrize(('kind','data'),[
    ('course',{'name':'sample\n','description':'x','version':'1.0.0'}),
    ('course',{'name':'sample','description':'x','version':'1.0.0\n'}),
    ('record',dict(spec='1.0',course=None,version=None,snapshot=None,generation=1,history=[],project=None,position=None,lessons={},calls=[],objectives=[],consent=[],declined=[])),
])
def test_schema_exact_scalar_boundaries(kind,data):
    assert any(f.severity=='error' for f in contracts().validate_frontmatter(kind,data))


def test_schema_registry_checks_root_payload_and_refs(tmp_path):
    import hashlib
    import shutil
    c=contracts()
    for directory in ['schemas','fixtures','examples','tests/contracts/fixtures']:
        shutil.copytree(ROOT/directory,tmp_path/directory)
    path=tmp_path/'schemas/course.schema.json'
    schema=json.loads(path.read_text())
    schema['properties']['description']['minLength']=1000
    path.write_text(json.dumps(schema)+'\n')
    def rehash():
        manifest_path=tmp_path/'schemas/history/1.0.0-rc.1/manifest.json'
        manifest=json.loads(manifest_path.read_text())
        for entry in manifest['releases'][0]['schemas']:
            entry['sha256']=hashlib.sha256((tmp_path/entry['path']).read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest)+'\n')
    rehash()
    assert any('course-baseline' in f.message for f in c.check_repository(tmp_path))
    schema['properties']['description']={'$ref':'https://unavailable.invalid/schema.json'}
    path.write_text(json.dumps(schema)+'\n');rehash()
    with pytest.raises(Unresolvable):c.schema_registry(tmp_path,'1.0.0-rc.1')


@pytest.mark.parametrize('expected', [
    {'rule': 'schema-course', 'path': 'version', 'keyword': 'pattern'},
    {'rule': 'schema-course', 'path': 'name', 'keyword': 'maxLength'},
])
def test_repository_cases_require_exact_finding(tmp_path, monkeypatch, expected):
    import shutil
    c = contracts()
    shutil.copytree(ROOT / 'schemas', tmp_path / 'schemas')
    (tmp_path / 'fixtures/schema').mkdir(parents=True)
    (tmp_path / 'examples').mkdir()
    (tmp_path / 'examples/manifest.json').write_text(json.dumps(dict(courses=[],includes=[])))
    case = dict(candidate='1.0.0-rc.1',case='wrong-reason', kind='course', requirement='req-course-frontmatter',
                outcome='rejected', finding=expected,
                data=dict(name='UPPER', description='Example', version='1.0.0'))
    (tmp_path / 'fixtures/schema/cases.json').write_text(json.dumps([case]))
    monkeypatch.setattr(c, 'identity_vectors', lambda root, **kwargs: [])
    monkeypatch.setattr(c, 'check_course', lambda root, **kwargs: [])
    findings = c.check_repository(tmp_path)
    assert {f.rule for f in findings} == {'req-course-frontmatter'}
    assert 'wrong-reason' in findings[0].message


CASES = json.loads((ROOT / 'fixtures/schema/cases.json').read_text())
TIME_LOCATIONS = [
    (case['case'], case['kind'], ['at'])
    for case in CASES if case['kind'] == 'event' and case['outcome'] == 'accepted'
]
TIME_LOCATIONS += [
    ('record-nested-valid', 'record', path)
    for path in [
        ['lessons', 'finish', 'at'], ['objectives', 0, 'at'],
        ['history', 0, 'lessons', 'finish', 'at'], ['history', 0, 'objectives', 0, 'at'],
    ]
]


@pytest.mark.parametrize(('name', 'kind', 'path'), TIME_LOCATIONS)
@pytest.mark.parametrize('at', [
    '2026-13-21T09:00:00Z', '2026-10-32T09:00:00Z',
    '2026-10-21T24:00:00Z', '2026-02-30T09:00:00Z',
])
def test_real_utc_times(name, kind, path, at):
    from copy import deepcopy
    data = deepcopy(next(case['data'] for case in CASES if case['case'] == name))
    parent = data
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = at
    findings = contracts().validate_frontmatter(kind, data)
    expected = {'rule': 'schema-' + kind, 'path': '/'.join(map(str, path)), 'keyword': 'format'}
    assert any(contracts().matches_expected(f, expected) for f in findings), (name, findings)


@pytest.mark.parametrize('at', ['2024-02-29T23:59:59Z', '2000-02-29T00:00:00Z'])
def test_valid_utc_leap_dates(at):
    data = dict(next(case['data'] for case in CASES if case['case'] == 'event-baseline'), at=at)
    assert not contracts().validate_frontmatter('event', data)


@pytest.mark.parametrize('project_kind', ['own', 'starter', 'git', 'local'])
@pytest.mark.parametrize('kind', ['event', 'record'])
@pytest.mark.parametrize('path', ['C:/app', 'z:app'])
def test_project_drive_letters(project_kind, kind, path):
    from copy import deepcopy
    project = deepcopy(next(case['data']['project'] for case in CASES
                            if case['case'] == 'event-project-' + project_kind))
    project['path'] = path
    if kind == 'event':
        data = dict(at='2026-10-21T09:00:00Z', kind='project-chosen', project=project)
    else:
        data = deepcopy(next(case['data'] for case in CASES if case['case'] == 'record-baseline'))
        data['project'] = project
    expected = dict(rule='schema-' + kind, path='project', keyword='oneOf' if kind == 'event' else 'anyOf')
    assert any(contracts().matches_expected(f, expected) for f in contracts().validate_frontmatter(kind, data))
