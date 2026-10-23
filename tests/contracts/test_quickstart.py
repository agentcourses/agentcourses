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


def test_current_author_guide_snippets(tmp_path):
    """The displayed current declarations and programs work together without a validator claim."""
    from markdown_it import MarkdownIt
    import yaml

    text = (ROOT / 'site/src/content/docs/authors/quickstart.mdx').read_text()
    fences = [token for token in MarkdownIt('commonmark').parse(text) if token.type == 'fence']
    courses = [token.content for token in fences if token.info == 'markdown' and 'format:' in token.content]
    assert len(courses) == 1
    metadata = yaml.safe_load(courses[0].split('---', 2)[1])
    assert metadata['format'] == '1.0.0-rc.2'
    assert {entry['id'] for entry in metadata['checks']} == {'final-check', 'agent-runs'}
    assert metadata['checks'][0]['run'] == 'python "$AGENT_COURSE_DIR/scripts/final_check.py"'
    declaration = next(yaml.safe_load(token.content) for token in fences if token.info == 'yaml' and token.content.startswith('checks:'))
    assert declaration['checks'] == metadata['checks']
    feedback = next(yaml.safe_load(token.content) for token in fences if token.info == 'yaml' and token.content.startswith('feedback:'))
    assert set(feedback) == {'feedback'}
    assert feedback['feedback']['rating'] == 'at-end'
    python = [token.content for token in fences if token.info == 'python']
    assert len(python) == 3
    course = tmp_path / 'quickstart'
    program = course / 'scripts/final_check.py'
    program.parent.mkdir(parents=True)
    program.write_text(python[0])
    # Includes provide unchanged lessons and rubric; declaration references still resolve.
    referenced = set()
    for lesson in ('intro', 'make', 'finish'):
        source = (ROOT / f'examples/quickstart/lessons/{lesson}.md').read_text()
        referenced.update(yaml.safe_load(source.split('---', 2)[1]).get('checks', []))
    assert referenced == {entry['id'] for entry in metadata['checks']}
    for fixture, source, expected in [('pass', python[1], 0), ('fail', python[2], 1)]:
        project = course / f'scripts/fixtures/final-check/{fixture}'
        project.mkdir(parents=True)
        (project / 'agent.py').write_text(source)
        before = (project / 'agent.py').read_bytes()
        result = subprocess.run([sys.executable, '-I', '-B', str(program)], cwd=project,
            env={'PATH': os.defpath, 'AGENT_COURSE_DIR': str(course), 'AGENT_COURSE_PROJECT': str(project)},
            capture_output=True, text=True, timeout=5)
        assert result.returncode == expected, (result.stdout, result.stderr)
        assert json.loads(result.stdout)['status'] == fixture
        assert (project / 'agent.py').read_bytes() == before


def test_current_worked_trace_identities(tmp_path):
    """Current public traces have their own exact bytes; retained proof inputs remain separate."""
    import re
    import yaml

    text = (ROOT / 'spec/records.md').read_text()
    section = text.split('<details><summary>Exact authored files for sample-course</summary>')[1].split('</details>')[0]
    files = dict(re.findall(r'`([^`]+)`:\n\n```[^\n]*\n(.*?)```', section, re.S))
    course = tmp_path / 'sample-course'
    for name, payload in files.items():
        path = course / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload.encode())
    meta = yaml.safe_load(files['COURSE.md'].split('---', 2)[1])
    assert meta['format'] == '1.0.0-rc.2'
    assert set(files) == {'COURSE.md', 'scripts/final_check.py',
        'scripts/fixtures/final-check/pass/agent.py', 'scripts/fixtures/final-check/fail/agent.py',
        'lessons/intro.md', 'lessons/make.md', 'lessons/finish.md', 'tutor/finish.rubric.md'}
    initial = c.course_digest(course)
    assert f'initial course identity is `{initial}`' in text
    page = course / 'COURSE.md'
    page.write_text(page.read_text().replace('version: "1.0.0"', 'version: "1.1.0"').replace('final_check.py"', 'final_check.py" --strict'))
    upgraded = c.course_digest(course)
    assert upgraded != initial
    assert f'content upgrade identity is `{upgraded}`' in text


def test_public_repository_commands_have_current_scope_and_setup():
    """Every published harness command names its supported inputs and real setup."""
    from markdown_it import MarkdownIt

    setup = 'https://github.com/agentcourses/agentcourses/blob/main/docs/CONTRIBUTING.md#set-up-and-run-the-checks'
    assert '## Set up and run the checks' in (ROOT / 'docs/CONTRIBUTING.md').read_text()
    commands = {}
    problems = []
    for page in sorted((ROOT / 'site/src/content/docs').rglob('*.mdx')):
        text = page.read_text()
        name = page.relative_to(ROOT).as_posix()
        lines = [line for line in text.splitlines() if 'tools/check_contracts.py ' in line]
        if lines:
            commands[name] = lines
            if any('--root .' not in line or '--example' in line for line in lines):
                problems.append((name, 'unsupported author-course validation command'))
            if setup not in text:
                problems.append((name, 'repository command lacks actual checkout setup'))
            if 'current-format' not in text.lower() or 'still being implemented' not in text:
                problems.append((name, 'repository proof lacks current-consumer limitation'))
        for token in MarkdownIt('commonmark').parse(text):
            for child in token.children or []:
                if child.type == 'link_open' and child.attrGet('href') == 'https://github.com/agentcourses/agentcourses#install-and-check':
                    problems.append((name, 'missing README setup anchor'))
    assert commands, 'the existing repository proof commands remain documented'
    assert problems == []


def test_public_folder_diagrams_resolve_starters_under_assets():
    """Resolve the tree indentation so a repeated parent cannot change the taught path."""
    from markdown_it import MarkdownIt
    from pathlib import PurePosixPath
    import re

    paths = [ROOT / 'README.md', ROOT / 'spec/format.md',
             *sorted((ROOT / 'site/src/content/docs').rglob('*.mdx'))]
    observed = []
    for page in paths:
        for fence in MarkdownIt('commonmark').parse(page.read_text()):
            if fence.type != 'fence' or fence.info != 'text':
                continue
            parents = []
            for line in fence.content.splitlines():
                branch = re.match(r'^([│ ]*)[├└]── ([^#]+)', line)
                if not branch:
                    continue
                depth = len(branch[1]) // 4
                name = branch[2].strip().rstrip('/')
                parents = parents[:depth] + [name]
                resolved = PurePosixPath(*parents).as_posix()
                if 'starter' in PurePosixPath(name).parts:
                    observed.append((page.relative_to(ROOT).as_posix(), resolved))
    assert observed, 'public layouts retain the starter role'
    assert [(page, path) for page, path in observed if path != 'assets/starter'] == []
