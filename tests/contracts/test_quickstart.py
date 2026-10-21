"""A copied author course works using only repository-owned fixture programs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from tools import check_contracts as c

ROOT=Path(__file__).resolve().parents[2]


def test_quickstart_copy(tmp_path, monkeypatch):
    run = subprocess.run

    def run_with_contract_environment(*args, **kwargs):
        assert kwargs['env']['AGENT_COURSE_PROJECT'] == str(kwargs['cwd'].resolve())
        assert kwargs['env']['AGENT_COURSE_DIR'] == str((tmp_path / 'quickstart').resolve())
        return run(*args, **kwargs)

    monkeypatch.setattr(subprocess, 'run', run_with_contract_environment)
    copied=tmp_path/'quickstart'
    shutil.copytree(ROOT/'examples/quickstart',copied)
    assert c.check_course(copied) == []
    course,lessons,checks,rubric=c.course_metadata(copied)
    assert rubric==(2,3) and course['project']==['own']
    assert lessons['finish']['stage']=='demonstrate'
    check=checks['final-check']
    assert check.get('network',False) is False and check['timeout']<=30
    assert check['run']=='python "$AGENT_COURSE_DIR/checks/final_check.py"'
    for outcome,exitcode in [('pass',0),('fail',1)]:
        project=tmp_path/outcome
        shutil.copytree(copied/'checks/fixtures/final-check'/outcome,project)
        before={p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()}
        result=subprocess.run([sys.executable,'-I','-B',str(copied/'checks/final_check.py')],cwd=project,
            env={'PATH':os.defpath,'AGENT_COURSE_DIR':str(copied),'AGENT_COURSE_PROJECT':str(project),'PYTHONDONTWRITEBYTECODE':'1'},
            capture_output=True,text=True,timeout=5)
        assert result.returncode==exitcode,(result.stdout,result.stderr)
        diagnostic=json.loads(result.stdout)
        assert diagnostic['status']==outcome
        if outcome=='fail':assert diagnostic['path']=='agent.py' and diagnostic['fix']
        assert before=={p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()}


@pytest.mark.parametrize(('args','exitcode','message'),[
    (['--root',str(ROOT)],0,'contracts:'),
    (['--example',str(ROOT/'examples/quickstart')],0,'contracts:'),
    (['--bad-option'],2,'usage:'),
    (['--example','/absent-course'],2,'usage:'),
    (['--root','/absent-course'],2,'usage:'),
])
def test_quickstart_cli(args,exitcode,message):
    result=subprocess.run([sys.executable,str(ROOT/'tools/check_contracts.py'),*args],capture_output=True,text=True,timeout=20)
    assert result.returncode==exitcode,(result.stdout,result.stderr)
    assert message in result.stdout+result.stderr


@pytest.mark.parametrize('option', ['--root', '--example'])
def test_nonexistent_path_is_bad_invocation(tmp_path, option, capsys):
    with pytest.raises(SystemExit) as error:
        c.main([option, str(tmp_path / 'absent')])
    assert error.value.code == 2
    output = capsys.readouterr()
    assert output.out == ''
    assert 'usage:' in output.err
    assert 'error: ' + option in output.err
