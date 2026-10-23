"""Candidate selection is trusted context, never inferred from authored extensions."""
import inspect
import json
import shutil
from pathlib import Path

import pytest
import yaml

from tools import check_contracts as c

OLD = '1.0.0-rc.1'
NEW = '1.0.0-rc.2'
FEEDBACK = {'rating': 'at-end', 'stuck': {'after_failures': 2}, 'questions': [{'id': 'helpful', 'ask': 'Was it helpful?', 'options': ['Yes', 'No']}]}
FILES = {'plan/README.md': b'Write your project plan here.\n', 'src/main.py': b'# Begin your implementation here.\n'}


def invoke(fn, *args, candidate=NEW, **kwargs):
    # Base-only compatibility exposes the missing behaviour without a signature error.
    if 'candidate' in inspect.signature(fn).parameters:
        kwargs['candidate'] = candidate
    return fn(*args, **kwargs)


def edit(root, **changes):
    path = root / 'COURSE.md'
    data, body = c.decode_markdown(path.read_text())
    for key, value in changes.items():
        if value is ABSENT:
            data.pop(key, None)
        else:
            data[key] = value
    path.write_text('---\n' + yaml.safe_dump(data, sort_keys=False) + '---\n' + body)


ABSENT = object()


def prepare(root, candidate=NEW, provenance=False):
    checks = c.decode_yaml((root/'checks/checks.yaml').read_text())
    if candidate == NEW:
        (root/'checks/checks.yaml').unlink()
        shutil.move(str(root/'checks'), root/'scripts')
        for check in checks:
            if 'run' in check:
                check['run'] = check['run'].replace('/checks/', '/scripts/')
        edit(root, format=NEW, checks=checks)
    base = root / ('assets/starter' if candidate == NEW else 'starter')
    for name, payload in FILES.items():
        target = base/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    notes = root / ('assets/notes.md' if candidate == NEW else 'references/notes.md')
    notes.parent.mkdir(parents=True, exist_ok=True)
    notes.write_text('Read the project notes.\n')
    path=root/'lessons/make.md'
    path.write_text(path.read_text().replace('stage: build', 'stage: build\nstarter: [plan/README.md]'))
    edit(root, project=['own', 'starter'] if provenance else 'own')
    if provenance:
        if candidate == NEW:
            edit(root, feedback=FEEDBACK)
        else:
            (root/'feedback.yaml').write_text(yaml.safe_dump(FEEDBACK))
    return root


@pytest.fixture
def central(course):
    return prepare(course)


def findings(root, candidate=NEW):
    return {(f.rule, f.severity, f.path.removeprefix(str(root)+'/')) for f in invoke(c.check_course, root, candidate=candidate)}


def exact(root, expected, candidate=NEW, case='candidate'):
    actual=findings(root, candidate)
    assert actual == expected, f'{case}: actual findings {sorted(actual)!r}'


def test_central_course(central):
    exact(central, set(), case='central-course')
    metadata=invoke(c.course_metadata, central)
    assert set(metadata[2]) == {'agent-runs', 'final-check'}
    assert metadata[3] == (2, 3)


def test_unknown_candidate(central):
    edit(central, format='private-extension')
    exact(central, {('req-format-identifier','error','COURSE.md')})


def test_central_fields_need_identifier(central):
    edit(central, format=ABSENT)
    exact(central, {('req-format-identifier','error','COURSE.md')})


def test_mixed_checks_even_equal(central):
    data,_=c.decode_markdown((central/'COURSE.md').read_text())
    (central/'checks').mkdir()
    (central/'checks/checks.yaml').write_text(yaml.safe_dump(data['checks']))
    exact(central, {('req-mixed-declarations','error','COURSE.md')})


def test_mixed_feedback_even_empty(central):
    edit(central, feedback={})
    (central/'feedback.yaml').write_text('')
    exact(central, {('req-mixed-declarations','error','COURSE.md')})


def test_invalid_central_checks(central):
    edit(central, checks={'id':'final-check'})
    exact(central, {('schema-course','error','COURSE.md:checks')})


def test_invalid_central_feedback(central):
    edit(central, feedback=None)
    exact(central, {('schema-course','error','COURSE.md:feedback')})


def test_duplicate_central_checks(central):
    data,_=c.decode_markdown((central/'COURSE.md').read_text())
    edit(central, checks=data['checks']+[dict(data['checks'][0])])
    exact(central, {('req-check-declaration','error','COURSE.md')})


def test_duplicate_feedback_questions(central):
    edit(central, feedback=dict(FEEDBACK,questions=FEEDBACK['questions']*2))
    exact(central, {('req-closed-hooks','error','COURSE.md')})


def test_catalogue_summary(central, monkeypatch):
    edit(central,compatibility='Python 3.12',spec='1.0',metadata={'private':'excluded'},feedback=FEEDBACK)
    summary=getattr(c, 'catalogue_summary', None)
    assert callable(summary), 'catalogue-summary: absent summary callable'
    real=c.read_authored
    reads=[]
    def read(root,name,**kwargs):
        reads.append(name)
        assert not name.startswith('tutor/'), 'catalogue read tutor material'
        return real(root,name,**kwargs)
    monkeypatch.setattr(c,'read_authored',read)
    data,_=c.decode_markdown((central/'COURSE.md').read_text())
    assert summary(central)=={key:data[key] for key in ('name','description','version','license','compatibility','spec') if key in data}
    assert reads == ['COURSE.md']


def test_fixture_is_not_project_source(central):
    edit(central, project='./scripts/fixtures/final-check/pass')
    exact(central, {('req-resource-roles','error','COURSE.md')})


PROVENANCE = [
    ('old-format-absent',ABSENT), ('old-format-null',None), ('old-format-number',42),
    ('old-format-boolean',True), ('old-format-list',['private-extension']),
    ('old-format-mapping',{'private-extension':True}), ('old-format-empty',''),
    ('old-format-arbitrary','private-extension'), ('old-format-new-value',NEW),
    ('old-checks-extension',{'private-extension':True}), ('old-feedback-extension','private-extension'),
    ('new-context-match',NEW), ('new-context-missing',ABSENT),
    ('new-context-unknown','private-extension'), ('new-context-mismatch',OLD),
    ('retained-context-missing',None), ('retained-context-unknown','private-extension'),
]


def retained(root,candidate):
    cls=getattr(c,'RetainedCourse',None)
    return cls(root,candidate) if cls else root


def start(root):
    return {'at':'2026-10-21T09:00:00Z','kind':'course-started','course':'sample-course','version':'1.0.0','source':'local','snapshot':c.course_digest(root)}


@pytest.mark.parametrize('case,value',PROVENANCE,ids=[v[0] for v in PROVENANCE])
def test_candidate_provenance(course,case,value,monkeypatch):
    old=case.startswith('old-') or case.startswith('retained-')
    candidate=OLD if old else NEW
    root=prepare(course,candidate,provenance=True)
    original=invoke(c.course_metadata,root,candidate=candidate)
    key='checks' if case=='old-checks-extension' else 'feedback' if case=='old-feedback-extension' else 'format'
    if not case.startswith('retained-'):
        edit(root,**{key:value})
    ev=start(root); identity=ev['snapshot']
    if case.startswith('retained-'):
        reads=[]
        real=c.course_metadata
        def metadata(*args,**kwargs):
            reads.append(args)
            return real(*args,**kwargs)
        monkeypatch.setattr(c,'course_metadata',metadata)
        context=root if case.endswith('missing') else retained(root,value)
        label='missing' if case.endswith('missing') else 'unsupported'
        expected=f'req-record-replay-data: {label} retained candidate provenance for {identity}; supply the original installation candidate'
        try:
            c.replay([ev],{identity:context},receipt_status=lambda *args:'verified')
        except c.ContractError as error:
            assert str(error)==expected, f'{case}: {error}'
        else:
            pytest.fail(f'{case}: replay accepted missing/unknown provenance; metadata reads={len(reads)}')
        assert reads==[], f'{case}: metadata reads {reads}'
        return
    invalid=not old and case!='new-context-match'
    expected={('req-format-identifier','error','COURSE.md')} if invalid else ({('req-unknown-keys','warning',f'COURSE.md:/{key}')} if old and value is not ABSENT else set())
    # The paired normal-input result is the meaningful base red for old extensions.
    normal='req-mixed-declarations' if case=='old-format-new-value' else 'req-format-identifier'
    if old:
        exact(root,{(normal,'error','COURSE.md')},case=case+' normal input')
        message = 'req-mixed-declarations: legacy declaration file present' if normal == 'req-mixed-declarations' else 'req-format-identifier: expected format \"1.0.0-rc.2\"'
        for read in [lambda:invoke(c.course_metadata,root), lambda:invoke(c.catalogue_summary,root), lambda:invoke(c.resolve_project,root,'starter'), lambda:invoke(c.starter_sources,root), lambda:invoke(c.starter_sources,root,lesson_id='make')]:
            with pytest.raises(c.ContractError) as error:read()
            assert str(error.value)==message,case
        with pytest.raises(c.ContractError) as error:
            c.replay([ev],{identity:retained(root,NEW)},receipt_status=lambda *args:'verified')
        replay_label='mixed declarations' if normal=='req-mixed-declarations' else 'invalid rc.2 format identifier'
        assert str(error.value)==f'req-record-replay-data: {replay_label} for {identity}',case
    exact(root,expected,candidate,case)
    readers=[lambda:invoke(c.course_metadata,root,candidate=candidate),
             lambda:invoke(c.catalogue_summary,root,candidate=candidate),
             lambda:invoke(c.resolve_project,root,'starter',candidate=candidate),
             lambda:invoke(c.starter_sources,root,candidate=candidate),
             lambda:invoke(c.starter_sources,root,lesson_id='make',candidate=candidate)]
    if invalid:
        for read in readers:
            with pytest.raises(c.ContractError) as error: read()
            assert str(error.value)=='req-format-identifier: expected format "1.0.0-rc.2"', case
        with pytest.raises(c.ContractError) as error:
            c.replay([ev],{identity:retained(root,candidate)},receipt_status=lambda *args:'verified')
        assert str(error.value)==f'req-record-replay-data: invalid rc.2 format identifier for {identity}'
        return
    metadata=readers[0]()
    assert metadata[1:]==original[1:], case
    assert readers[1]()=={key:metadata[0][key] for key in ('name','description','version','license','compatibility','spec') if key in metadata[0]},case
    assert readers[2]()==(root/('starter' if old else 'assets/starter')).resolve(),case
    assert readers[3]()==FILES,case
    assert readers[4]()=={'plan/README.md':FILES['plan/README.md']},case
    projection=c.replay([ev],{identity:retained(root,candidate)},receipt_status=lambda *args:'verified')
    assert projection==dict(spec='1.0',course='sample-course',version='1.0.0',snapshot=identity,generation=1,history=[],project=None,position=None,lessons={},calls=[],objectives=[],consent=[],declined=[]),case


# Each entry replaces one literal NOT_BUILT explanation with an executable exact-set proof.
CANDIDATE_CASES = {
    'format.md#case-central-checks-null-rejected': ('checks-null','schema-course','COURSE.md:checks'),
    'format.md#case-central-checks-type-rejected': ('checks-type','schema-course','COURSE.md:checks'),
    'format.md#case-central-feedback-null-rejected': ('feedback-null','schema-course','COURSE.md:feedback'),
    'format.md#case-central-feedback-type-rejected': ('feedback-type','schema-course','COURSE.md:feedback'),
    'format.md#case-central-checks-duplicate-rejected': ('checks-duplicate','req-check-declaration','COURSE.md'),
    'format.md#case-central-check-shape-rejected': ('check-shape','schema-course','COURSE.md:checks/0/timeout'),
    'format.md#case-central-extension-warning': ('extension','req-unknown-keys','COURSE.md:/difficulty'),
    'format.md#case-mixed-checks-equal-rejected': ('mixed-equal','req-mixed-declarations','COURSE.md'),
    'format.md#case-mixed-checks-empty-rejected': ('mixed-empty','req-mixed-declarations','COURSE.md'),
    'format.md#case-mixed-feedback-empty-rejected': ('mixed-feedback-empty','req-mixed-declarations','COURSE.md'),
    'format.md#case-mixed-feedback-equal-rejected': ('mixed-feedback-equal','req-mixed-declarations','COURSE.md'),
    'format.md#case-mixed-both-rejected': ('mixed-both','req-mixed-declarations','COURSE.md'),
    'format.md#case-mixed-precedence-rejected': ('mixed-precedence','req-mixed-declarations','COURSE.md'),
    'format.md#case-resource-fixture-project-rejected': ('fixture-project','req-resource-roles','COURSE.md'),
    'format.md#case-resource-fixture-starter-rejected': ('fixture-starter','req-resource-roles','lessons/make.md'),
    'format.md#case-resource-markdown-relative-rejected': ('markdown-base','req-course-links','lessons/make.md'),
    'format.md#case-resource-old-base-rejected': ('old-base','req-starter-files','lessons/make.md'),
    'format.md#case-resource-selection-missing-rejected': ('selection','req-project-selection',None),
    'execution.md#case-candidate-copy-missing-rejected': ('missing','req-starter-files','lessons/make.md'),
    'execution.md#case-candidate-copy-nonfile-rejected': ('nonfile','req-starter-files','lessons/make.md'),
    'execution.md#case-candidate-copy-source-escape-rejected': ('escape','req-starter-files','lessons/make.md'),
    'consent.md#case-candidate-feedback-duplicate-rejected': ('feedback-duplicate','req-closed-hooks','COURSE.md'),
    'consent.md#case-candidate-feedback-range-rejected': ('feedback-range','schema-course','COURSE.md:feedback/stuck/after_failures'),
}


@pytest.mark.parametrize('anchor',CANDIDATE_CASES,ids=lambda value:value.split('#case-')[1])
def test_candidate_register_case(central,anchor,tmp_path):
    action,rule,path=CANDIDATE_CASES[anchor]
    data,_=c.decode_markdown((central/'COURSE.md').read_text())
    if action=='checks-null':edit(central,checks=None)
    if action=='checks-type':edit(central,checks={})
    if action=='feedback-null':edit(central,feedback=None)
    if action=='feedback-type':edit(central,feedback=[])
    if action=='checks-duplicate':edit(central,checks=data['checks']+[data['checks'][0]])
    if action=='check-shape':
        data['checks'][0]['timeout']=301;edit(central,checks=data['checks'])
    if action=='extension':edit(central,difficulty='easy')
    if action.startswith('mixed'):
        if action in ('mixed-equal','mixed-empty','mixed-both','mixed-precedence'):
            (central/'checks').mkdir();(central/'checks/checks.yaml').write_text(yaml.safe_dump(data['checks']) if action=='mixed-equal' else '')
        if action in ('mixed-feedback-empty','mixed-feedback-equal','mixed-both'):
            edit(central,feedback={'rating':'at-end'} if action=='mixed-feedback-equal' else {})
            (central/'feedback.yaml').write_text('rating: at-end\n' if action=='mixed-feedback-equal' else '')
        if action=='mixed-precedence':edit(central,checks=None)
    if action=='fixture-project':edit(central,project='./scripts/fixtures/final-check/pass')
    if action=='fixture-starter':
        shutil.rmtree(central/'assets/starter');(central/'assets/starter').symlink_to('../scripts/fixtures/final-check/pass')
        lesson=central/'lessons/make.md';lesson.write_text(lesson.read_text().replace('plan/README.md','agent.py'))
    if action=='markdown-base':
        lesson=central/'lessons/make.md';lesson.write_text(lesson.read_text()+'\n[Notes](../assets/notes.md)\n')
    if action=='old-base':
        target=central/'starter/plan/README.md';target.parent.mkdir(parents=True);shutil.move(str(central/'assets/starter/plan/README.md'),target)
    if action in ('missing','nonfile','escape'):
        source=central/'assets/starter/plan/README.md';source.unlink()
        if action=='nonfile':source.mkdir()
        if action=='escape':source.symlink_to('../../../assets/notes.md')
    if action=='feedback-duplicate':edit(central,feedback=dict(FEEDBACK,questions=FEEDBACK['questions']*2))
    if action=='feedback-range':edit(central,feedback={'stuck':{'after_failures':1}})
    if action=='selection':
        edit(central,project=['own','starter'])
        resolver=getattr(c,'resolve_project',None)
        assert callable(resolver), f'{anchor}: absent resolver'
        with pytest.raises(c.ContractError) as error:resolver(central,None)
        assert str(error.value)=='req-project-selection: supply an explicitly selected project option'
        return
    exact(central,{(rule,'warning' if action=='extension' else 'error',path)},case=anchor)
    if action.startswith('mixed'):
        for reader in [lambda:invoke(c.course_metadata,central),lambda:invoke(c.catalogue_summary,central),lambda:invoke(c.resolve_project,central,'own'),lambda:invoke(c.starter_sources,central,lesson_id='make')]:
            with pytest.raises(c.ContractError) as error:reader()
            assert str(error.value)=='req-mixed-declarations: legacy declaration file present'
        ev=start(central)
        with pytest.raises(c.ContractError) as error:c.replay([ev],{ev['snapshot']:retained(central,NEW)},receipt_status=lambda *args:'verified')
        assert str(error.value)==f"req-record-replay-data: mixed declarations for {ev['snapshot']}"


@pytest.mark.parametrize('candidate',[OLD,NEW])
def test_tampered_retained_sources(course,candidate):
    root=prepare(course,candidate)
    ev=start(root)
    path=root/'lessons/intro.md';path.write_text(path.read_text()+'\nTampered.\n')
    with pytest.raises(c.ContractError,match='retained identity mismatch'):
        c.replay([ev],{ev['snapshot']:retained(root,candidate)},receipt_status=lambda *args:'verified')


def test_central_script_fixtures(central,tmp_path):
    import os
    import subprocess
    import sys
    exact(central,set())
    for outcome,expected in [('pass',0),('fail',1)]:
        project=tmp_path/outcome
        shutil.copytree(central/'scripts/fixtures/final-check'/outcome,project)
        before={p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()}
        result=subprocess.run([sys.executable,'-I','-B',str(central/'scripts/final_check.py')],cwd=project,env={'PATH':os.defpath,'AGENT_COURSE_DIR':str(central),'AGENT_COURSE_PROJECT':str(project),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=5)
        assert result.returncode==expected,(outcome,result.stdout,result.stderr)
        assert before=={p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()}


def test_central_nested_extensions(central):
    data,_=c.decode_markdown((central/'COURSE.md').read_text())
    data['checks'][0]['future']='ignored'
    edit(central,checks=data['checks'],feedback={'stuck':{'after_failures':2,'future':'ignored'}})
    exact(central,{('req-unknown-keys','warning','COURSE.md:/checks/0/future'),('req-unknown-keys','warning','COURSE.md:/feedback/stuck/future')})


def test_optional_summary_fields_are_absent(central):
    edit(central,license=ABSENT,compatibility=ABSENT,spec=ABSENT)
    summary=getattr(c,'catalogue_summary',None)
    assert callable(summary),'optional-summary-fields: absent summary callable'
    data,_=c.decode_markdown((central/'COURSE.md').read_text())
    assert summary(central)=={key:data[key] for key in ('name','description','version')}
