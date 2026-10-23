"""Pure replay under an explicitly synthetic protected-history assumption.

No callback here qualifies a host or proves operation admission or disk durability.
"""
import copy
import json
import shutil

import pytest

from tools import check_contracts as c
from conftest import legacy_retained

S1 = 'sha256:c35480cb14f89d9e89719faa2452a5b494d58ba2f80cb3fe26abd2d0346f4ca4'
S2 = 'sha256:727fef18c5013d7ce206e0f8253218857e433f673af14129278e6bb097b927a6'
UNKNOWN = 'sha256:' + '0'*64


def event(kind, **kw):
    return {'at':'2026-10-21T09:00:00Z', 'kind':kind, **kw}


def progress(kind, lesson='finish', **kw):
    return event(kind,lesson=lesson,snapshot=S1,generation=1,**kw)


def start():
    return event('course-started',course='sample-course',version='1.0.0',snapshot=S1,source='local')


def opening():
    events=[start(),event('project-chosen',project={'kind':'own','path':'.'}),
            progress('lesson-started','intro'),progress('step-entered','intro',step='goal'),
            progress('call-put','intro',call='choose-tool'),
            progress('call-decided','intro',call='choose-tool',by='learner',provenance='verified',receipt={'occurrence':'A'*22,'verifier':'synthetic'}),
            progress('lesson-completed','intro'),progress('lesson-started','make'),
            progress('check-run','make',check='agent-runs',result='fail',evidence='observed'),
            progress('check-run','make',check='agent-runs',result='pass',evidence='observed'),
            progress('lesson-completed','make')]
    times=['09:00:00','09:00:05','09:01:00','09:01:05','09:02:00','09:03:00','09:04:00','09:05:00','09:06:00','09:08:00','09:09:00']
    return [dict(e,at='2026-10-21T'+t+'Z') for e,t in zip(events,times,strict=True)]


def finishing():
    events=[progress('lesson-started'),progress('call-put',call='choose-check'),
            progress('call-decided',call='choose-check',by='learner',provenance='verified',receipt={'occurrence':'B'*22,'verifier':'synthetic'}),
            progress('check-run',check='final-check',result='pass',evidence='checked'),
            progress('step-entered',step='explain-back'),progress('explain-judged',met=2,of=3),progress('lesson-completed')]
    times=['09:10:00','09:11:00','09:12:00','09:15:00','09:16:00','09:18:00','09:19:00']
    return [dict(e,at='2026-10-21T'+t+'Z') for e,t in zip(events,times,strict=True)]


def verified(index, event, generation):
    return 'verified'


def run(events, roots, verifier=verified):
    result=c.replay(events, {identity: value if isinstance(value,c.RetainedCourse) else legacy_retained(value) for identity,value in roots.items()},receipt_status=verifier)
    assert not [f for f in c.validate_frontmatter('record',result) if f.severity=='error']
    return result


@pytest.fixture
def roots(course,tmp_path):
    new=tmp_path/'new'/'sample-course'
    shutil.copytree(course,new)
    p=new/'COURSE.md';p.write_text(p.read_text().replace('"1.0.0"','"1.1.0"'))
    p=new/'checks/checks.yaml';p.write_text(p.read_text().replace('final_check.py"','final_check.py" --strict'))
    return {S1:legacy_retained(course),S2:legacy_retained(new)}


def upgrade(source=S1,target=S2,version='1.1.0'):
    return event('course-upgraded',**{'from':source,'to':target,'version':version,'source':'local'})


def test_replay_empty():
    assert c.replay([],{},receipt_status=verified)==dict(spec='1.0',course=None,version=None,snapshot=None,generation=0,history=[],project=None,position=None,lessons={},calls=[],objectives=[],consent=[],declined=[])


def test_replay_public_projection(roots):
    projection=run(opening(),roots)
    expected=json.loads((c.ROOT/'fixtures/schema/opening-record.json').read_text())
    assert projection==expected
    assert projection['generation']==1 and projection['history']==[]
    assert projection['lessons']=={'intro':{'status':'passed','at':'2026-10-21T09:04:00Z'},'make':{'status':'passed','checks':{'agent-runs':{'last':'pass','runs':2}},'at':'2026-10-21T09:09:00Z'}}
    assert projection['position']=={'lesson':'make','step':'goal'}
    assert projection['objectives']==[{'id':'agent-runs-ok','lesson':'make','evidence':'observed','by':'agent-runs','at':'2026-10-21T09:09:00Z','snapshot':S1}]
    result=run(opening()+finishing(),roots)
    assert [v['id'] for v in result['objectives']]==['agent-runs-ok','agent-passes','agent-explained']
    assert result==run(opening()+finishing(),roots)


@pytest.mark.parametrize('variant',['tutor','unverified','open','missing','repeated','snapshot','lesson','rejected','imported'])
def test_replay_call_variants(roots,variant):
    end=finishing();callback=verified
    if variant=='tutor':end[2].update(by='tutor');del end[2]['provenance'];del end[2]['receipt']
    if variant=='unverified':end[2]['provenance']='unverified';del end[2]['receipt']
    if variant=='open':del end[2]
    if variant=='missing':del end[1:3]
    if variant=='repeated':end[2]['receipt']['occurrence']='A'*22
    if variant=='snapshot':end[2]['snapshot']=UNKNOWN
    if variant=='lesson':end[2]['lesson']='make'
    if variant in ['rejected','imported']:callback=lambda *args:'rejected' if variant=='rejected' else 'unverified'
    result=run(opening()+end,roots,callback)
    assert result['lessons']['finish']['status']=='passed'
    assert [v['id'] for v in result['objectives']]==['agent-runs-ok']


@pytest.mark.parametrize('kind',['check-run','step-entered','hint-given','explain-judged','lesson-completed','lesson-skipped','call-put','call-decided'])
def test_replay_no_implicit_start(roots,kind):
    choices={e['kind']:e for e in finishing()};choices['hint-given']=progress('hint-given');choices['lesson-skipped']=progress('lesson-skipped')
    result=run([start(),choices[kind]],roots)
    assert result['lessons']=={} and result['objectives']==[] and result['calls']==[] and result['position'] is None


@pytest.mark.parametrize(('latest','status'),[(1,'started'),(2,'passed')])
def test_replay_latest_explain(roots,latest,status):
    end=finishing();end.insert(-1,progress('explain-judged',met=latest,of=3))
    result=run(opening()+end,roots)
    assert result['lessons']['finish']['status']==status
    assert len(result['objectives'])==(1 if latest==1 else 3)


def test_replay_skip_help_and_idempotence(roots):
    ev=[start(),progress('lesson-started','make'),progress('check-run','make',check='agent-runs',result='not-run'),progress('hint-given','make'),progress('lesson-completed','make'),progress('lesson-skipped','make')]
    result=run(ev,roots)
    assert result['lessons']['make']=={'status':'skipped','at':ev[-1]['at'],'checks':{'agent-runs':{'last':'not-run','runs':0}}}
    ev += [progress('lesson-started','make'),progress('check-run','make',check='agent-runs',result='pass',evidence='observed'),progress('lesson-completed','make')]
    passed=run(ev,roots)
    assert passed['lessons']['make']['status']=='passed'
    assert passed==run(ev+[progress('lesson-completed','make'),progress('lesson-skipped','make')],roots)


def test_replay_upgrade_and_revisit(roots):
    before=run(opening()+finishing(),roots)
    result=run(opening()+finishing()+[upgrade(),upgrade(S2,S1,'1.0.0')],roots)
    assert result['generation']==3 and len(result['history'])==2
    assert result['history'][0]=={k:before[k] for k in ['version','snapshot','generation','position','lessons','calls','objectives']}
    assert result['lessons']=={} and result['calls']==[] and result['objectives']==[] and result['position'] is None
    assert result['project']==before['project']


@pytest.mark.parametrize('kind',['check-run','explain-judged','call-put','call-decided','lesson-completed'])
def test_replay_stale_before_lookup_or_verification(roots,kind):
    ev=opening()+[upgrade(),upgrade(S2,S1,'1.0.0'),dict(progress('lesson-started'),generation=3)]
    end={e['kind']:e for e in finishing()}[kind]
    def forbidden(index,*args):
        if index>=len(ev):raise AssertionError('stale event must not verify')
        return 'verified'
    assert run(ev+[end],roots,forbidden)==run(ev,roots,forbidden)


def test_replay_callback_generation_and_no_promotion(roots):
    seen=[]
    def authority(index,ev,generation):seen.append((index,generation));return 'verified'
    result=run(opening()+finishing(),roots,authority)
    assert seen==[(5,1),(13,1)] and len(result['objectives'])==3
    ev=finishing();ev[2]['provenance']='unverified';del ev[2]['receipt']
    assert len(run(opening()+ev,roots,authority)['objectives'])==1
    with pytest.raises(c.ContractError,match='receipt'):
        run(opening()+finishing(),roots,lambda *args:'maybe')


def test_replay_unused_old_occurrence_and_fresh(roots):
    prefix=[start(),upgrade(),upgrade(S2,S1,'1.0.0')]
    end=[dict(e,generation=3) for e in finishing()]
    def old_issuance(index,event,generation):
        assert generation==3
        return 'rejected'
    assert run(prefix+end,roots,old_issuance)['objectives']==[]
    assert len(run(prefix+end,roots)['objectives'])==2


@pytest.mark.parametrize('fault',['missing','tampered','name','structure','rubric','symlink'])
def test_replay_required_source_stops(roots,fault,tmp_path):
    if fault=='missing':del roots[S1]
    if fault=='tampered':(roots[S1].root/'lessons/intro.md').write_text('changed')
    if fault in ['name','structure','rubric']:
        p=roots[S1].root/('COURSE.md' if fault=='name' else 'lessons/finish.md' if fault=='structure' else 'tutor/finish.rubric.md')
        p.write_text(p.read_text().replace('name: sample-course','name: wrong') if fault=='name' else p.read_text().replace('choose-check','choose-tool') if fault=='structure' else p.read_text().replace('2 of 3','2 of 4'))
        # Independently changed inputs must pass identity before their malformed structure is refused.
        identity=c.course_digest(roots[S1].root);roots[identity]=roots.pop(S1)
        ev=dict(start(),snapshot=identity)
    elif fault=='symlink':
        link=tmp_path/'alias';link.symlink_to(roots[S1].root,target_is_directory=True);roots[S1]=legacy_retained(link)
    with pytest.raises(c.ContractError):run([ev if fault in ['name','structure','rubric'] else start()],roots)


def test_replay_lookup_predicates(roots):
    before=run(opening(),roots)
    ev=[dict(start(),snapshot=UNKNOWN),upgrade(UNKNOWN,UNKNOWN),upgrade(S1,S1),event('future',snapshot=UNKNOWN)]
    assert run(opening()+ev,roots)==before
    with pytest.raises(c.ContractError,match=UNKNOWN):run(opening()+[upgrade(S1,UNKNOWN)],roots)


def test_replay_unknown_fields_consent_and_occurrence_consumption(roots):
    ev=opening()+[event('consent-changed',destination='z.example',state='granted'),event('consent-changed',destination='a.example',state='withdrawn'),event('consent-changed',destination='z.example',state='declined',lesson='make',hook='rating')]
    result=run(ev,roots)
    assert result['consent']==[{'destination':'a.example','state':'withdrawn'},{'destination':'z.example','state':'granted'}]
    assert len(result['declined'])==1
    assert run(ev+[ev[-1],dict(progress('hint-given','make'),followed=True)],roots)==result
    end=finishing();bad=dict(end[2],snapshot=UNKNOWN)
    result=run(opening()+[bad]+end,roots)
    assert len(result['objectives'])==1


def test_replay_line_damage():
    events,findings=c.decode_events(b'{"at":"2026-10-21T09:00:00Z","kind":"future"}\n{"kind":')
    assert len(events)==1 and [f.rule for f in findings]==['event-partial']
    events,findings=c.decode_events(b'{"at":"2026-10-21T09:00:00Z","kind":"future"}')
    assert len(events)==1 and not findings
    for raw in [b'{}\n',b'{"at":"x","at":"y","kind":"future"}\n',b'[]\n',b'\xff\n',b' '*4097+b'\n']:
        assert c.decode_events(raw)[1][0].rule=='req-record-event-line'


@pytest.mark.parametrize(('optional','result','expected_status','settles'),[
    (True,'fail','passed',False),(True,'pass','passed',True),(False,'fail','started',False),
    (False,'error','started',False),(False,'not-run','started',False),
])
def test_replay_optional_evidence(course,optional,result,expected_status,settles):
    path=course/'lessons/make.md'
    path.write_text(path.read_text().replace('checks: [agent-runs]',f'checks: [{{id: agent-runs, required: {str(not optional).lower()}}}]'))
    identity=c.course_digest(course)
    ev=[dict(start(),snapshot=identity),dict(progress('lesson-started','make'),snapshot=identity),
        dict(progress('check-run','make',check='agent-runs',result=result),snapshot=identity),
        dict(progress('lesson-completed','make'),snapshot=identity)]
    if result in ['pass','fail']:ev[2]['evidence']='observed'
    projected=run(ev,{identity:course})
    assert projected['lessons']['make']['status']==expected_status
    assert bool(projected['objectives'])==settles


def test_replay_reopened_call_and_latest_wrong_evidence(roots):
    end=finishing();end.insert(-1,progress('call-put',call='choose-check'))
    assert len(run(opening()+end,roots)['objectives'])==1
    end=finishing();end[-4]['evidence']='observed'
    assert run(opening()+end,roots)['lessons']['finish']['status']=='started'
    end=finishing();end[-2]['of']=4
    assert run(opening()+end,roots)['lessons']['finish']['status']=='started'


def test_replay_committed_history_preserves_one_generation(roots):
    # Install/lock/record caches are deliberately absent from the replay interface.
    log=opening()+[upgrade()]
    result=run(log,roots)
    assert result['generation']==2 and len(result['history'])==1
    assert result==run(log,roots)
    assert result['history'][0]['objectives'][0]['at']==opening()[-1]['at']
    assert run(opening(),roots)['generation']==1  # Published but uncommitted target is unused.


def test_replay_fresh_check_explain_and_noop_after_revisit(roots):
    log=[start(),upgrade(),upgrade(S2,S1,'1.0.0')]
    fresh=[dict(e,generation=3) for e in finishing()]
    assert len(run(log+fresh,roots)['objectives'])==2
    fresh.insert(-1,upgrade(S1,S1,'1.0.0'))
    result=run(log+fresh,roots)
    assert len(result['objectives'])==2 and result['generation']==3 and len(result['history'])==2


def test_replay_stable_metadata_internal_link_and_exclusion(course):
    path=course/'lessons/make.md';data=path.read_bytes();path.unlink()
    target=course/'references/make.txt';target.parent.mkdir(exist_ok=True);target.write_bytes(data)
    path.symlink_to('../references/make.txt')
    identity=c.course_digest(course)
    assert run([dict(start(),snapshot=identity)],{identity:course})['generation']==1
    path.unlink();target.unlink()
    target=course/'.agents/make.txt';target.parent.mkdir();target.write_bytes(data)
    path.symlink_to('../.agents/make.txt')
    identity=c.course_digest(course)
    with pytest.raises(c.ContractError,match='retained|replay-data'):
        run([dict(start(),snapshot=identity)],{identity:course})


def test_replay_incompatible_project_and_verifier_loss(roots):
    root=roots[S2].root;path=root/'COURSE.md';path.write_text(path.read_text().replace('license: Apache-2.0','license: Apache-2.0\nproject: ./examples/app'))
    source=root/'examples/app';source.mkdir(parents=True);(source/'README.md').write_text('Local source\n')
    identity=c.course_digest(root)
    with pytest.raises(c.ContractError,match='incompatible'):
        run(opening()+[upgrade(S1,identity)],{S1:roots[S1],identity:root})
    def lost(*args):raise c.ContractError('receipt authority lost')
    with pytest.raises(c.ContractError,match='authority lost'):
        run(opening(),roots,lost)


def test_replay_reads_both_candidates(course):
    from test_candidates import prepare, retained, start, OLD, NEW, exact
    exact(prepare(course),set(),case='replay-reads-both-candidates new input')
    ev=start(course)
    result=c.replay([ev],{ev['snapshot']:retained(course,NEW)},receipt_status=verified)
    assert result['generation']==1 and result['consent']==[]
    old=c.ROOT/'tests/contracts/fixtures/rc1/quickstart'
    assert old.is_dir()
    oldev=dict(ev,course='quickstart',snapshot=c.course_digest(old))
    assert c.replay([oldev],{oldev['snapshot']:retained(old,OLD)},receipt_status=verified)['generation']==1
