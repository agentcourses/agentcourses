"""Whole-course rules need parsed Markdown and more than one authored file."""
from dataclasses import dataclass
from pathlib import Path
import os
import re
import shutil

import pytest

from tools import check_contracts as c


def errors(root):
    return {f.rule for f in c.check_course(root) if f.severity == 'error'}


def test_course_relations(course):
    assert not errors(course)


@pytest.mark.parametrize(('path', 'old', 'new', 'rule'), [
    ('COURSE.md', 'lessons/make.md', 'lessons/missing.md', 'req-lesson-list'),
    ('lessons/make.md', 'checks: [agent-runs]', 'checks: [absent]', {'req-lesson-frontmatter', 'req-objective-ids-unique'}),
    ('lessons/finish.md', 'id: choose-check', 'id: choose-tool', 'req-call-ids-unique'),
    ('lessons/finish.md', 'id: agent-passes', 'id: agent-runs-ok', 'req-objective-ids-unique'),
    ('lessons/finish.md', 'by: final-check', 'by: agent-runs', 'req-objective-ids-unique'),
    ('COURSE.md', '2. [Make the agent](lessons/make.md)\n3. [Finish and explain](lessons/finish.md)', '2. [Finish and explain](lessons/finish.md)\n3. [Make the agent](lessons/make.md)', 'req-final-demonstrate'),
    ('lessons/finish.md', 'stage: demonstrate', 'stage: build', {'req-final-demonstrate', 'req-lesson-heading-cardinality', 'req-objective-ids-unique'}),
    ('lessons/make.md', '## Build', '## Task', 'req-lesson-heading-cardinality'),
    ('COURSE.md', '## Outcome', '### Outcome', 'req-course-headings'),
    ('lessons/make.md', '## Goal', '## Goal\n\nOne\n\n## Goal', 'req-lesson-heading-cardinality'),
    ('tutor/finish.rubric.md', 'pass: 2 of 3', 'pass: 2 of 4', 'req-rubric'),
    ('lessons/intro.md', 'You can say what an agent tool is.', '[Key](tutor/finish.rubric.md)', 'req-course-links'),
    ('lessons/make.md', 'Your agent runs.', '[File](../outside.txt)', 'req-course-links'),
    ('lessons/make.md', 'Your agent runs.', '[File](project:src/app.py#L40-L10)', 'req-project-lines'),
])
def test_course_relations_reject(course, path, old, new, rule):
    p = course / path
    assert old in p.read_text()
    p.write_text(p.read_text().replace(old, new))
    assert_rules(course, {rule} if isinstance(rule, str) else rule)


@pytest.mark.parametrize(('path', 'rule'), [
    ('tutor/finish.rubric.md', 'req-rubric'),
    ('checks/checks.yaml', 'req-lesson-frontmatter'),
    ('lessons/finish.md', 'req-lesson-list'),
    ('checks/fixtures/final-check/pass/agent.py', 'req-check-rules'),
])
def test_course_relations_missing(course, path, rule):
    (course / path).unlink()
    if path.endswith('agent.py'):
        (course / path).parent.rmdir()
    assert_rules(course, {rule})


def test_fenced_headings_and_nested_rubric(course):
    p = course / 'lessons/intro.md'
    p.write_text(p.read_text() + '\n```markdown\n## Goal\n## Explain back\n```\n')
    p = course / 'tutor/finish.rubric.md'
    p.write_text(p.read_text() + '  - Nested detail\n\nA note, not a criterion.\n')
    assert not errors(course)


@pytest.mark.parametrize('target',['./tutor/finish.rubric.md','references/key.md'])
def test_goal_tutor_target_is_resolved(course,target):
    if target.startswith('references'):
        (course/'references').mkdir(exist_ok=True)
        (course/target).symlink_to('../tutor/finish.rubric.md')
    path=course/'lessons/intro.md'
    path.write_text(path.read_text()+f'\n[Key]({target})\n')
    assert_rules(course, {'req-course-links'})


@pytest.mark.parametrize('name',['hello world.txt','café.txt','a'*101,'empty-dir'])
def test_starter_files_use_their_own_path_grammar(course,name):
    target=course/'starter'/name;target.parent.mkdir(exist_ok=True)
    if name=='empty-dir':target.mkdir()
    else:target.write_text('TODO\n')
    path=course/'lessons/make.md'
    path.write_text(path.read_text().replace('stage: build',f'stage: build\nstarter: ["{name}"]'))
    if name == 'empty-dir':
        assert_rules(course, {'req-starter-files'})
    else:
        assert_rules(course, set())


def test_starter_project_needs_a_file(course):
    (course/'starter/empty').mkdir(parents=True)
    path=course/'COURSE.md';path.write_text(path.read_text().replace('license: Apache-2.0','license: Apache-2.0\nproject: starter'))
    assert_rules(course, {'req-project-field'})


@pytest.mark.parametrize('name',['feedback.yaml','checks/checks.yaml'])
@pytest.mark.parametrize('target',['missing.yaml','self'])
def test_optional_metadata_links_must_resolve(course,name,target):
    if name.startswith('checks'):
        for lesson in ['make','finish']:
            path=course/f'lessons/{lesson}.md'
            text=path.read_text().replace('checks: [agent-runs]\n','').replace('checks: [final-check]\n','').replace('stage: build','stage: understand')
            text=text.replace('objectives:\n  - id: agent-runs-ok\n    text: The agent runs\n    by: agent-runs\n','')
            text=text.replace('by: final-check','by: explain-back')
            path.write_text(text)
    path=course/name
    if path.exists():path.unlink()
    path.symlink_to(path.name if target=='self' else target)
    assert_rules(course, {'req-closed-hooks' if name == 'feedback.yaml' else 'req-check-declaration'})


def test_missing_course_names_folder_requirement(course):
    (course / 'COURSE.md').unlink()
    assert errors(course) == {'req-folder-and-name'}


@pytest.mark.parametrize(('old', 'new', 'expected'), [
    ('stage: demonstrate', 'stage: demonstrate\nminutes: 0', {'schema-lesson'}),
    ('    ask: Which behaviour will the final check protect?\n', '', {'schema-lesson'}),
    ('stage: demonstrate', 'stage: demonstrate\nstarter: [../COURSE.md]', {'schema-lesson'}),
    ('## Explain back\n\nExplain which tool your agent calls and why you chose it.',
     '```markdown\n## Explain back\n```', {'req-lesson-heading-cardinality'}),
])
def test_invalid_lesson_has_only_its_real_rules(tmp_path, old, new, expected):
    root = tmp_path / 'quickstart'
    shutil.copytree(Path(__file__).resolve().parents[2] / 'examples/quickstart', root)
    path = root / 'lessons/finish.md'
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new))
    assert errors(root) == expected


@pytest.fixture
def quickstart(tmp_path):
    root = tmp_path / 'quickstart'
    shutil.copytree(Path(__file__).resolve().parents[2] / 'examples/quickstart', root)
    return root


def assert_rules(root, expected_errors, expected_warnings=frozenset()):
    findings = c.check_course(root)
    assert {f.rule for f in findings if f.severity == 'error'} == expected_errors
    assert {f.rule for f in findings if f.severity == 'warning'} == expected_warnings
    assert all('req-record-replay-data' not in f.message for f in findings)


LESSON_LIST = ('1. [Meet the agent](lessons/intro.md)\n2. [Make the agent](lessons/make.md)\n'
               '3. [Finish and explain](lessons/finish.md)\n')
LESSONS_FAULTS = {
    # A missing, repeated, fenced or level-three heading breaks the course-page heading rule.
    'heading-deleted': ('\n## Lessons\n\n' + LESSON_LIST, '', 'req-course-headings'),
    'heading-repeated': (LESSON_LIST, LESSON_LIST + '\n## Lessons\n', 'req-course-headings'),
    'heading-fenced': ('## Lessons\n\n' + LESSON_LIST, '```markdown\n## Lessons\n\n' + LESSON_LIST + '```\n',
                       'req-course-headings'),
    'heading-level-three': ('## Lessons', '### Lessons', 'req-course-headings'),
    # A single Lessons heading whose list is broken breaks the lesson-list rule.
    'duplicate': ('lessons/make.md', 'lessons/intro.md', 'req-lesson-list'),
    'second-list': (LESSON_LIST, LESSON_LIST + '\nText.\n\n1. [Again](lessons/intro.md)\n', 'req-lesson-list'),
    'outside-lessons': ('lessons/make.md', 'COURSE.md', 'req-lesson-list'),
    'empty': (LESSON_LIST, '', 'req-lesson-list'),
}


@pytest.mark.parametrize(('old', 'new', 'rule'), LESSONS_FAULTS.values(), ids=LESSONS_FAULTS.keys())
@pytest.mark.parametrize('invalid_lesson', [False, True], ids=['valid-schema', 'invalid-schema'])
def test_lessons_heading_and_list_faults_have_exact_rules(quickstart, old, new, rule, invalid_lesson):
    path = quickstart / 'COURSE.md'
    text = path.read_text()
    assert text.count(old) == 1
    path.write_text(text.replace(old, new))
    expected = {rule}
    if invalid_lesson:
        path = quickstart / 'lessons/make.md'
        path.write_text(path.read_text().replace('stage: build', 'stage: build\nminutes: 0'))
        expected.add('schema-lesson')
    assert_rules(quickstart, expected)


@pytest.mark.parametrize('name', ['intro', 'make', 'finish'])
def test_missing_listed_lesson_has_exact_rules(quickstart, name):
    (quickstart / f'lessons/{name}.md').unlink()
    assert_rules(quickstart, {'req-lesson-list'})


@pytest.mark.parametrize(('renamed', 'rules'), [(False, {'req-rubric'}), (True, {'req-lesson-id-and-stage', 'req-rubric'})],
                         ids=['missing', 'renamed'])
def test_missing_rubric_has_exact_rules(quickstart, renamed, rules):
    path = quickstart / 'tutor/finish.rubric.md'
    if renamed:
        path.rename(path.with_name('wrap-up.rubric.md'))
    else:
        path.unlink()
    assert_rules(quickstart, rules)


@pytest.mark.parametrize(('old', 'new', 'expected'), [
    ('timeout: 30', 'timeout: 0', ['schema-checks']),
    ('verify: agent.py exists and defines an agent\n',
     'verify: agent.py exists and defines an agent\n- id: explain-back\n  kind: observe\n  verify: Reserved\n',
     ['schema-checks']),
    ('network: false', 'network: [false', ['req-check-declaration']),
], ids=['timeout-zero', 'reserved-observe-id', 'yaml-syntax'])
def test_broken_checks_file_reports_only_its_own_fault(quickstart, old, new, expected):
    path = quickstart / 'checks/checks.yaml'
    text = path.read_text()
    assert text.count(old) == 1
    path.write_text(text.replace(old, new))
    findings = c.check_course(quickstart)
    assert sorted(f.rule for f in findings) == expected, findings


@pytest.mark.parametrize('name', ['feedback.yaml', 'checks/checks.yaml'])
def test_course_metadata_fault_has_no_record_message(quickstart, name):
    path = quickstart / name
    path.unlink()
    path.symlink_to('missing.yaml')
    findings = c.check_course(quickstart)
    assert findings
    assert all('req-record-replay-data' not in f.message for f in findings)


# Requirement register sweep.
#
# Every rejected or warning case the register links for a course-folder rule is either built
# below on a copy of the quickstart or listed in NOT_BUILT with the reason it cannot be. Each
# built case must report exactly its expected findings and nothing else.

ROOT = Path(__file__).resolve().parents[2]
SPEC_TABLES = ('format.md', 'execution.md', 'consent.md')
COURSE_FOLDER_JUDGEMENTS = {'Course syntax', 'Source resolution', 'Project start', 'Advisory lint'}


def register():
    """Map each course-folder case to the requirements listing it, and each requirement to its enforcer."""
    judged, warned = {}, set()
    for name in SPEC_TABLES:
        for line in (ROOT / 'tests/contracts/fixtures/historical' / name).read_text().splitlines():
            match = re.match(r'\| <a id="(case-[^"]+)"></a>', line)
            if match:
                cells = [cell.strip() for cell in line.strip().strip('|').split(' | ')]
                # The invalid reference table has no judgement column; its heading judges every row as source resolution.
                judged[f'{name}#{match[1]}'] = cells[2] if len(cells) == 5 else 'Source resolution'
                if 'warning' in cells[-2]:
                    warned.add(f'{name}#{match[1]}')
    cases, enforcers = {}, {}
    section = ''
    for line in (ROOT / 'tests/contracts/fixtures/historical/requirements.md').read_text().splitlines():
        if line.startswith('## '):
            section = line
        match = re.match(r'\| <a id="(req-[^"]+)"></a>', line)
        if not match or 'id="record-rules"' in section:
            continue
        cells = line.strip().strip('|').split(' | ')
        enforcers[match[1]] = cells[5]
        # Rejected and warning cases sit in the invalid column; some warning cases sit with the examples.
        examples = [a for a in re.findall(r'\]\(([a-z]+\.md#case-[^)]+)\)', cells[3]) if a in warned]
        for anchor in re.findall(r'\]\(([a-z]+\.md#case-[^)]+)\)', cells[4]) + examples:
            if judged.get(anchor) in COURSE_FOLDER_JUDGEMENTS:
                cases.setdefault(anchor, set()).add(match[1])
    return cases, enforcers


def sub(path, old, new):
    def edit(root):
        file = root / path
        text = file.read_text()
        assert text.count(old) == 1, (path, old)
        file.write_text(text.replace(old, new))
    return edit


def put(path, text):
    def edit(root):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(text)
    return edit


def remove(path):
    def edit(root):
        target = root / path
        shutil.rmtree(target) if target.is_dir() else target.unlink()
    return edit


def move(path, new):
    return lambda root: (root / path).rename(root / new)


def link(path, target):
    def edit(root):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).symlink_to(target)
    return edit


def mkdir(path):
    return lambda root: (root / path).mkdir(parents=True)


def fifo(path):
    def edit(root):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        os.mkfifo(root / path)
    return edit


@dataclass(frozen=True)
class Case:
    anchor: str
    requirement: str
    edits: tuple
    errors: tuple = ()
    warnings: tuple = ()
    folder: str = 'quickstart'
    variant: str = ''

    @property
    def id(self):
        return self.anchor.split('#case-')[1].removesuffix('-rejected') + (f'-{self.variant}' if self.variant else '')


def case(anchor, requirement, errors, *edits, warnings=(), folder='quickstart', variant=''):
    errors = (errors,) if isinstance(errors, str) else errors
    return Case(anchor, requirement, edits, errors, warnings, folder, variant)


F, E, C = 'format.md#case-', 'execution.md#case-', 'consent.md#case-'
LESSONS = ('1. [Meet the agent](lessons/intro.md)\n2. [Make the agent](lessons/make.md)\n'
           '3. [Finish and explain](lessons/finish.md)\n')
MAKE_OBJECTIVES = 'objectives:\n  - id: agent-runs-ok\n    text: The agent runs\n    by: agent-runs\n'
BUILD_END = 'create `agent.py` with them.\n'
EXPLAIN = '\n## Explain back\n\nExplain which tool your agent calls and why you chose it.\n'
EXTRA = '---\ntitle: Extra\nstage: understand\n---\n\n## Goal\n\nYou can name one more tool.\n'
AGENT = 'agent = None\n'
FINAL_ENTRY = ('- id: final-check\n  run: python "$AGENT_COURSE_DIR/checks/final_check.py"\n'
               '  verify: agent.py defines an agent\n  timeout: 30\n  network: false\n')
FEEDBACK = ('rating: per-lesson\nstuck: { after_failures: 3 }\nquestions:\n  - id: provider\n'
            '    ask: Which model provider do you use most?\n    options: [Anthropic, OpenAI, Google, Other]\n')
QUESTION = '  - id: provider\n'
QUIZ = ('\n## Quiz\n\n1. Where is a tool registered?\n   - On the model\n   - On the agent object\n'
        '   - In the checks file\n2. What does the exit code 1 from a check mean?\n   - The check is broken\n'
        '   - The learner can fix the project\n   - The host refused the command\n')
QUIZ_KEY = ('- answer: 1\n  why: Tools are registered on the agent object, not on the model.\n- answer: 1\n'
            '  why: Exit 1 means the requirement is not met and the learner can fix it.\n')


def project(value):
    return sub('COURSE.md', 'project: [own]', f'project: {value}')


def course_name(name):
    return sub('COURSE.md', 'name: quickstart', f'name: "{name}"')


def build_link(target):
    return sub('lessons/make.md', BUILD_END, BUILD_END + f'\n[Target]({target})\n')


def check(check_id, kind='command'):
    if kind == 'observe':
        return sub('checks/checks.yaml', 'verify: agent.py exists and defines an agent\n',
                   f'verify: agent.py exists and defines an agent\n- id: {check_id}\n  kind: observe\n  verify: Reserved\n')
    entry = FINAL_ENTRY.replace('id: final-check', f'id: {check_id}')
    return lambda root: (sub('checks/checks.yaml', '  network: false\n', '  network: false\n' + entry)(root),
                         put(f'checks/fixtures/{check_id}/pass/agent.py', AGENT)(root),
                         put(f'checks/fixtures/{check_id}/fail/agent.py', AGENT)(root))


def local_source(readme_lines=40):
    """The local project source of the format's local-folder cases."""
    def edit(root):
        if readme_lines:
            put('examples/app/README.md', ''.join(f'Line {n}\n' for n in range(1, readme_lines + 1)))(root)
        put('examples/app/src/main.py', 'print("app")\n')(root)
        project("['./examples/app']")(root)
    return edit


STARTER = (put('starter/plan/README.md', '# Plan\n'),
           sub('lessons/make.md', 'stage: build', 'stage: build\nstarter: [plan/README.md]'))
NOTES = put('references/notes.md', '# Notes\n')
QUIZ_BASELINE = (sub('lessons/make.md', BUILD_END, BUILD_END + QUIZ), put('tutor/make.quiz.yaml', QUIZ_KEY))
FEEDBACK_BASELINE = put('feedback.yaml', FEEDBACK)
REFERENCES = {
    'empty-revision': 'git+https://git.example.com/team/repo@',
    'empty-folder': 'gh:example-co/payments#',
    'repeated-at': 'gh:example-co/payments@v1@v2',
    'no-repopath': 'git+https://git.example.com',
    'empty-repopath': 'git+https://git.example.com/@v1',
    'empty-segment': 'git+https://git.example.com/team//repo',
    'dotdot-segment': 'git+https://git.example.com/team/../repo',
    'trailing-slash': 'git+https://git.example.com/team/repo/',
    'port': 'git+https://git.example.com:0/team/repo',
    'host': 'git+https://-git.example.com/team/repo',
    'owner-long': 'gh:' + 'o' * 40 + '/payments',
    'repo-long': 'gh:example-co/' + 'r' * 101,
    'repo-git-suffix': 'gh:example-co/payments.git',
    'tag-long': 'gh:example-co/payments@' + 'v' * 129,
    'segment-long': 'gh:example-co/payments#' + 's' * 101,
    'label-long': 'git+https://' + 'h' * 64 + '.example.com/team/repo',
    'port-high': 'git+https://git.example.com:65536/team/repo',
}
BOUNDARIES = {
    'boundary-credentials-recorded': 'git+https://user:token@git.example.com/team/repo.git',
    'credentials': 'git+https://user:token@git.example.com/team/repo.git',
    'folder-traversal': 'gh:example-co/payments#../secrets',
    'folder-absolute': 'gh:example-co/payments#/etc',
    'local-traversal': './../outside',
    'absolute': '/home/learner/app',
    'ssh': 'git+ssh://git.example.com/team/repo.git',
    'local-revision': './app@v1',
    'query-after-path': 'git+https://git.example.com/team/repo.git?ref=main@v1.2.0#docs',
    'query-after-folder': 'git+https://git.example.com/team/repo.git@v1.2.0#docs?x=1',
}
PROJECT_LINKS = {
    'range-reversed': 'project:src/ledger/model.py#L40-L10',
    'range-zero': 'project:src/ledger/model.py#L0',
    'range-open': 'project:src/ledger/model.py#L10-',
    'range-multiple': 'project:src/ledger/model.py#L10,L20',
    'range-leading-zero': 'project:src/ledger/model.py#L010',
    'project-traversal': 'project:../secret.txt',
    'project-absolute': 'project:/etc/passwd',
    'project-fragment': 'project:src/model.py#section',
}

SWEEP = [
    # Course folder, names and reserved ids.
    case(F + 'folder-missing-course-rejected', 'req-folder-and-name', 'req-folder-and-name', remove('COURSE.md')),
    case(F + 'folder-name-differs-rejected', 'req-folder-and-name', 'req-folder-and-name', course_name('other-course')),
    case(F + 'id-too-long-rejected', 'req-kebab-ids', 'schema-course', course_name('a' + 'b' * 64), folder='a' + 'b' * 64),
    case(F + 'call-ask-missing-rejected', 'req-amend-3-calls-declared', 'schema-lesson',
         sub('lessons/intro.md', '    ask: Which tool will your agent call first?\n', '')),
    case(F + 'id-empty-rejected', 'req-kebab-ids', 'schema-lesson', sub('lessons/intro.md', 'id: choose-tool', 'id: ""')),
    case(F + 'id-uppercase-rejected', 'req-kebab-ids', 'schema-course', course_name('Add-A-Tool'), folder='Add-A-Tool'),
    case(F + 'id-underscore-rejected', 'req-kebab-ids', 'schema-course', course_name('add_a_tool'), folder='add_a_tool'),
    case(F + 'id-doubled-hyphen-rejected', 'req-kebab-ids', 'schema-course', course_name('add--tool'), folder='add--tool'),
    case(F + 'id-edge-hyphen-rejected', 'req-kebab-ids', 'schema-course', course_name('-add'), folder='-add', variant='leading'),
    case(F + 'id-edge-hyphen-rejected', 'req-kebab-ids', 'schema-course', course_name('add-'), folder='add-', variant='trailing'),
    case(F + 'id-reserved-check-rejected', 'req-explain-back-reserved', 'schema-checks', check('explain-back')),
    case(F + 'id-reserved-observe-rejected', 'req-explain-back-reserved', 'schema-checks', check('explain-back', 'observe')),
    case(F + 'id-reserved-lesson-rejected', 'req-explain-back-reserved', 'req-explain-back-reserved',
         move('lessons/make.md', 'lessons/explain-back.md'), sub('COURSE.md', 'lessons/make.md', 'lessons/explain-back.md')),
    case(F + 'id-reserved-call-rejected', 'req-explain-back-reserved', 'schema-lesson',
         sub('lessons/intro.md', 'id: choose-tool', 'id: explain-back')),
    case(F + 'id-reserved-objective-rejected', 'req-explain-back-reserved', 'schema-lesson',
         sub('lessons/finish.md', 'id: agent-explained', 'id: explain-back')),
    # Both the lesson's list and the declaration carry the reserved id, so each file's schema reports it.
    case(F + 'objectives-check-with-reserved-id-rejected', 'req-explain-back-reserved', ('schema-checks', 'schema-lesson'),
         sub('lessons/finish.md', 'checks: [final-check]', 'checks: [final-check, explain-back]'), check('explain-back')),
    case(F + 'understand-check-rejected', 'req-understand-stage', 'schema-lesson',
         sub('lessons/intro.md', 'stage: understand', 'stage: understand\nchecks: [final-check]')),
    case(F + 'understand-objective-rejected', 'req-understand-stage', 'schema-lesson',
         sub('lessons/intro.md', 'stage: understand',
             'stage: understand\nobjectives: [{id: intro-done, text: Knows tools, by: final-check}]')),
    # Course frontmatter and unknown keys.
    case(F + 'frontmatter-name-missing-rejected', 'req-course-frontmatter', 'schema-course', sub('COURSE.md', 'name: quickstart\n', '')),
    case(F + 'frontmatter-description-missing-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'description: Build a one-file agent and explain it. For beginners.\n', '')),
    case(F + 'frontmatter-version-missing-rejected', 'req-course-frontmatter', 'schema-course', sub('COURSE.md', 'version: "1.0.0"\n', '')),
    case(F + 'frontmatter-description-empty-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'description: Build a one-file agent and explain it. For beginners.', 'description: ""')),
    case(F + 'frontmatter-description-long-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'description: Build a one-file agent and explain it. For beginners.', 'description: ' + 'd' * 1025)),
    case(F + 'frontmatter-compatibility-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'license: Apache-2.0', 'license: Apache-2.0\ncompatibility: ""'), variant='empty'),
    case(F + 'frontmatter-compatibility-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'license: Apache-2.0', 'license: Apache-2.0\ncompatibility: ' + 'c' * 501), variant='long'),
    case(F + 'frontmatter-description-type-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'description: Build a one-file agent and explain it. For beginners.', 'description: 12')),
    case(F + 'frontmatter-version-number-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'version: "1.0.0"', 'version: 1.2')),
    case(F + 'frontmatter-version-build-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'version: "1.0.0"', 'version: "1.0.0+b1"')),
    case(F + 'frontmatter-metadata-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'license: Apache-2.0', 'license: Apache-2.0\nmetadata: [author, Ana]'), variant='list'),
    case(F + 'frontmatter-metadata-rejected', 'req-course-frontmatter', 'schema-course',
         sub('COURSE.md', 'license: Apache-2.0', 'license: Apache-2.0\nmetadata: {n: 1}'), variant='number'),
    case(F + 'frontmatter-invalid-page-rejected', 'req-course-frontmatter', 'req-course-frontmatter',
         lambda root: (root / 'COURSE.md').write_text('---\n- quickstart\n---\n' + (root / 'COURSE.md').read_text().split('---\n', 2)[2])),
    case(F + 'unknown-key-rejected', 'req-unknown-keys', (), sub('COURSE.md', 'license: Apache-2.0', 'license: Apache-2.0\ndifficulty: easy'),
         warnings=('req-unknown-keys',)),
    case(F + 'unknown-key-known-wrong-type-rejected', 'req-unknown-keys', 'schema-course',
         sub('COURSE.md', 'description: Build a one-file agent and explain it. For beginners.', 'description: 12')),
    case(F + 'unknown-key-course-warning', 'req-unknown-keys', (),
         sub('COURSE.md', 'license: Apache-2.0', 'license: Apache-2.0\ndifficulty: easy'), warnings=('req-unknown-keys',)),
    case(F + 'unknown-key-lesson-warning', 'req-unknown-keys', (),
         sub('lessons/finish.md', 'stage: demonstrate', 'stage: demonstrate\npace: slow'), warnings=('req-unknown-keys',)),
    case(F + 'unknown-key-check-warning', 'req-unknown-keys', (),
         sub('checks/checks.yaml', '  network: false\n', '  network: false\n  owner: team-a\n'), warnings=('req-unknown-keys',)),
    case(F + 'unknown-key-call-warning', 'req-unknown-keys', (),
         sub('lessons/intro.md', '    ask: Which tool', '    hint: be brief\n    ask: Which tool'), warnings=('req-unknown-keys',)),
    case(F + 'unknown-key-objective-warning', 'req-unknown-keys', (),
         sub('lessons/finish.md', '    by: final-check\n', '    by: final-check\n    weight: 2\n'), warnings=('req-unknown-keys',)),
    case(F + 'id-lesson-frontmatter-id-warning', 'req-lesson-id-and-stage', (),
         sub('lessons/intro.md', 'stage: understand', 'stage: understand\nid: setup'), warnings=('req-unknown-keys',)),
    case(F + 'evals-key-warning', 'req-evals-render-deferred', (),
         sub('COURSE.md', 'license: Apache-2.0', 'license: Apache-2.0\nevals: evals/evals.json'), warnings=('req-unknown-keys',)),
    case(F + 'evals-key-schema-rejected', 'req-evals-render-deferred', (),
         sub('COURSE.md', 'license: Apache-2.0', 'license: Apache-2.0\nevals: evals/evals.json'), warnings=('req-unknown-keys',)),
    # The course page.
    case(F + 'page-lessons-missing-rejected', 'req-course-headings', 'req-course-headings', sub('COURSE.md', '\n## Lessons\n\n' + LESSONS, '')),
    case(F + 'page-outcome-missing-rejected', 'req-course-headings', 'req-course-headings',
         sub('COURSE.md', '## Outcome\n\n`agent.py`: an agent that passes `final-check`.\n\n', '')),
    case(F + 'page-lessons-duplicate-rejected', 'req-course-headings', 'req-course-headings', sub('COURSE.md', LESSONS, LESSONS + '\n## Lessons\n')),
    case(F + 'page-outcome-duplicate-rejected', 'req-course-headings', 'req-course-headings', sub('COURSE.md', LESSONS, LESSONS + '\n## Outcome\n')),
    case(F + 'page-fenced-heading-rejected', 'req-course-headings', 'req-course-headings',
         sub('COURSE.md', '## Lessons\n\n' + LESSONS, '```markdown\n## Lessons\n\n' + LESSONS + '```\n')),
    case(F + 'page-level-three-rejected', 'req-course-headings', 'req-course-headings', sub('COURSE.md', '## Lessons', '### Lessons')),
    # The lesson list.
    case(F + 'list-duplicate-rejected', 'req-lesson-list', 'req-lesson-list', sub('COURSE.md', LESSONS, LESSONS + '4. [Again](lessons/intro.md)\n')),
    case(F + 'list-unlisted-rejected', 'req-lesson-list', 'req-lesson-list', put('lessons/extra.md', EXTRA)),
    case(F + 'list-missing-file-rejected', 'req-lesson-list', 'req-lesson-list', sub('COURSE.md', LESSONS, LESSONS + '4. [Extra](lessons/extra.md)\n')),
    case(F + 'list-second-list-rejected', 'req-lesson-list', 'req-lesson-list',
         sub('COURSE.md', LESSONS, LESSONS + '\nA paragraph.\n\n1. [Again](lessons/intro.md)\n')),
    case(F + 'list-outside-target-rejected', 'req-lesson-list', 'req-lesson-list',
         NOTES, sub('COURSE.md', LESSONS, LESSONS + '4. [Notes](references/notes.md)\n')),
    case(F + 'list-empty-rejected', 'req-lesson-list', 'req-lesson-list', sub('COURSE.md', LESSONS, '')),
    # Lesson ids, stages and lesson frontmatter.
    case(F + 'stage-name-rejected', 'req-lesson-id-and-stage', 'schema-lesson', sub('lessons/make.md', 'stage: build', 'stage: practice')),
    # A rename leaves a file that names no lesson and a final lesson without its rubric; both are reported.
    case(F + 'id-rubric-claim-rejected', 'req-lesson-id-and-stage', ('req-lesson-id-and-stage', 'req-rubric'),
         move('tutor/finish.rubric.md', 'tutor/wrap-up.rubric.md')),
    case(F + 'final-stage-not-demonstrate-rejected', 'req-final-demonstrate', 'req-final-demonstrate',
         sub('lessons/finish.md', 'stage: demonstrate', 'stage: build'),
         sub('lessons/finish.md', '  - id: agent-explained\n    text: The learner explains the agent\n    by: explain-back\n', ''),
         sub('lessons/finish.md', '## Explain back', '## Build'), remove('tutor/finish.rubric.md')),
    case(F + 'final-stage-two-demonstrate-rejected', 'req-final-demonstrate', 'req-final-demonstrate',
         sub('lessons/intro.md', 'stage: understand', 'stage: demonstrate'),
         sub('lessons/intro.md', 'is.\n', 'is.\n\n## Explain back\n\nExplain what an agent tool is.\n'),
         put('tutor/intro.rubric.md', '---\npass: 1 of 1\n---\n- **Names a tool** and what it returns\n')),
    case(F + 'final-stage-demonstrate-first-rejected', 'req-final-demonstrate', 'req-final-demonstrate',
         sub('COURSE.md', LESSONS, '1. [Finish and explain](lessons/finish.md)\n2. [Make the agent](lessons/make.md)\n'
                                   '3. [Meet the agent](lessons/intro.md)\n')),
    case(F + 'lesson-minutes-zero-rejected', 'req-lesson-frontmatter', 'schema-lesson',
         sub('lessons/make.md', 'stage: build', 'stage: build\nminutes: 0')),
    case(F + 'lesson-check-repeated-rejected', 'req-lesson-frontmatter', 'req-lesson-frontmatter',
         sub('lessons/make.md', 'checks: [agent-runs]', 'checks: [agent-runs, agent-runs]')),
    # The extended baseline's make.md has no objectives, so the unknown id is the only fault.
    case(F + 'lesson-check-unknown-rejected', 'req-lesson-frontmatter', 'req-lesson-frontmatter',
         sub('lessons/make.md', MAKE_OBJECTIVES, ''), sub('lessons/make.md', 'checks: [agent-runs]', 'checks: [no-such-check]')),
    case(F + 'lesson-field-type-rejected', 'req-lesson-frontmatter', 'schema-lesson',
         sub('lessons/make.md', 'stage: build', 'stage: build\nminutes: "12"'), variant='text-minutes'),
    case(F + 'lesson-field-type-rejected', 'req-lesson-frontmatter', 'schema-lesson',
         sub('lessons/make.md', 'stage: build', 'stage: build\nminutes: 1.5'), variant='fractional-minutes'),
    case(F + 'lesson-field-type-rejected', 'req-lesson-frontmatter', 'schema-lesson',
         sub('lessons/make.md', 'stage: build', 'stage: build\ncalls: choose-tool'), variant='scalar-calls'),
    case(F + 'lesson-checks-missing-rejected', 'req-lesson-frontmatter', 'schema-lesson',
         sub('lessons/make.md', MAKE_OBJECTIVES, ''), sub('lessons/make.md', 'checks: [agent-runs]\n', '')),
    case(F + 'lesson-title-rejected', 'req-lesson-frontmatter', 'schema-lesson', sub('lessons/make.md', 'title: Make the agent\n', '')),
    # Lesson headings.
    case(F + 'headings-goal-missing-rejected', 'req-lesson-heading-cardinality', 'req-lesson-heading-cardinality',
         sub('lessons/make.md', '## Goal\n\n', '')),
    case(F + 'headings-goal-duplicate-rejected', 'req-lesson-heading-cardinality', 'req-lesson-heading-cardinality',
         sub('lessons/make.md', 'Your agent runs.\n', 'Your agent runs.\n\n## Goal\n\nIt runs again.\n')),
    case(F + 'headings-build-missing-rejected', 'req-lesson-heading-cardinality', 'req-lesson-heading-cardinality',
         sub('lessons/make.md', '## Build\n\n', '')),
    case(F + 'headings-build-duplicate-rejected', 'req-lesson-heading-cardinality', 'req-lesson-heading-cardinality',
         sub('lessons/make.md', BUILD_END, BUILD_END + '\n## Build\n\nBuild it again.\n')),
    case(F + 'headings-task-for-build-rejected', 'req-lesson-heading-cardinality', 'req-lesson-heading-cardinality',
         sub('lessons/make.md', 'stage: build', 'stage: practise'), sub('lessons/make.md', '## Build', '## Task')),
    case(F + 'headings-explain-back-in-build-rejected', 'req-lesson-heading-cardinality', 'req-lesson-heading-cardinality',
         sub('lessons/make.md', BUILD_END, BUILD_END + EXPLAIN)),
    case(F + 'headings-explain-back-missing-rejected', 'req-lesson-heading-cardinality', 'req-lesson-heading-cardinality',
         sub('lessons/finish.md', EXPLAIN, '')),
    # Calls, objectives and starter files.
    case(F + 'call-ids-duplicate-rejected', 'req-call-ids-unique', 'req-call-ids-unique',
         sub('lessons/finish.md', 'id: choose-check', 'id: choose-tool')),
    case(F + 'objectives-duplicate-rejected', 'req-objective-ids-unique', 'req-objective-ids-unique',
         sub('lessons/make.md', 'id: agent-runs-ok', 'id: agent-passes')),
    case(F + 'objectives-check-elsewhere-rejected', 'req-objective-ids-unique', 'req-objective-ids-unique',
         sub('lessons/finish.md', 'by: final-check', 'by: agent-runs')),
    case(F + 'objectives-explain-back-in-build-rejected', 'req-objective-ids-unique', 'req-objective-ids-unique',
         sub('lessons/make.md', MAKE_OBJECTIVES, 'objectives:\n  - id: made\n    text: Made\n    by: explain-back\n')),
    case(F + 'markdown-only-duplicate-rejected', 'req-markdown-only', 'req-objective-ids-unique',
         sub('lessons/make.md', 'id: agent-runs-ok', 'id: agent-passes')),
    case(F + 'starter-missing-rejected', 'req-starter-files', 'req-starter-files',
         *STARTER, sub('lessons/make.md', '[plan/README.md]', '[plan/MISSING.md]')),
    case(F + 'starter-traversal-rejected', 'req-starter-files', 'schema-lesson',
         *STARTER, sub('lessons/make.md', '[plan/README.md]', '[../outside.md]')),
    case(F + 'starter-absolute-rejected', 'req-starter-files', 'schema-lesson',
         *STARTER, sub('lessons/make.md', '[plan/README.md]', '[/etc/hosts]')),
    case(F + 'starter-empty-segment-rejected', 'req-starter-files', 'schema-lesson',
         *STARTER, sub('lessons/make.md', '[plan/README.md]', '[plan//README.md]')),
    # Course links.
    case(F + 'link-http-rejected', 'req-course-links', 'req-course-links', NOTES, build_link('http://example.com/guide')),
    case(F + 'link-missing-rejected', 'req-course-links', 'req-course-links', NOTES, build_link('lessons/nope.md')),
    case(F + 'link-escape-rejected', 'req-course-links', 'req-course-links', NOTES, build_link('../other-course/COURSE.md')),
    case(F + 'link-tutor-in-page-rejected', 'req-course-links', 'req-course-links', NOTES,
         sub('COURSE.md', 'passes `final-check`.', 'passes `final-check`. See the [rubric](tutor/finish.rubric.md).')),
    case(F + 'link-tutor-in-goal-rejected', 'req-course-links', 'req-course-links', NOTES,
         sub('lessons/make.md', 'Your agent runs.', 'Your agent runs. [Rubric](tutor/finish.rubric.md)')),
    case(F + 'link-file-relative-rejected', 'req-course-links', 'req-course-links', NOTES, build_link('../references/notes.md')),
    # The project field, references and local project sources.
    case(F + 'options-empty-rejected', 'req-project-field', 'schema-course', project('[]')),
    case(F + 'options-duplicate-rejected', 'req-project-field', 'schema-course', project('[own, own]')),
    case(F + 'options-mapping-rejected', 'req-project-field', 'schema-course', project('{kind: own}')),
    case(F + 'options-unknown-rejected', 'req-project-field', 'schema-course', project('Own')),
    case(F + 'options-starter-empty-rejected', 'req-project-field', 'req-project-field', project('starter')),
    *[case(F + f'ref-{name}-rejected', 'req-reference-grammar', 'schema-course', project(f"['{value}']"))
      for name, value in REFERENCES.items()],
    *[case(F + f'ref-{name}-rejected', 'req-reference-boundaries', 'schema-course', project(f"['{value}']"))
      for name, value in BOUNDARIES.items()],
    case(F + 'ref-boundary-local-escape-rejected', 'req-reference-boundaries', 'req-local-materialisation',
         local_source(), link('examples/app/src/secret.txt', '../../../COURSE.md')),
    case(F + 'local-source-missing-rejected', 'req-local-materialisation', 'req-local-materialisation',
         project("['./examples/missing']"), variant='missing'),
    case(F + 'local-source-missing-rejected', 'req-local-materialisation', 'req-local-materialisation',
         mkdir('examples/app'), project("['./examples/app']"), variant='empty'),
    case(F + 'local-escaping-link-rejected', 'req-local-materialisation', 'req-local-materialisation',
         local_source(), link('examples/app/src/secret.txt', '../../../COURSE.md')),
    case(F + 'local-cycle-rejected', 'req-local-materialisation', 'req-local-materialisation',
         local_source(), link('examples/app/loop', '.')),
    case(F + 'local-special-file-rejected', 'req-local-materialisation', 'req-local-materialisation',
         local_source(), fifo('examples/app/src/feed')),
    *[case(F + f'link-{name}-rejected', 'req-project-lines', 'req-project-lines', build_link(target))
      for name, target in PROJECT_LINKS.items()],
    case(F + 'link-baseline-out-of-bounds-rejected', 'req-local-link-timing', 'req-local-link-timing',
         local_source(9), build_link('project:README.md#L10-L40'), variant='range'),
    case(F + 'link-baseline-out-of-bounds-rejected', 'req-local-link-timing', 'req-local-link-timing',
         local_source(9), build_link('project:README.md#L10'), variant='line'),
    case(F + 'link-baseline-missing-file-rejected', 'req-local-link-timing', 'req-local-link-timing',
         local_source(0), build_link('project:README.md#L10')),
    case(F + 'link-git-offline-accepted', 'req-local-link-timing', (),
         project("['gh:example-co/payments']"), build_link('project:README.md#L10'), warnings=('req-local-link-timing',)),
    case(F + 'link-git-offline-claimed-rejected', 'req-local-link-timing', (),
         project("['gh:example-co/payments']"), build_link('project:README.md#L10'), warnings=('req-local-link-timing',)),
    # Advice is never a reason to reject a course.
    case(F + 'count-rejected', 'req-amend-8-count-lint', (),
         sub('lessons/intro.md', 'You can say what an agent tool is.', 'Lesson 3 adds a tool.')),
    case(F + 'count-duration-rejected', 'req-rules-vs-advice', (),
         sub('COURSE.md', 'For beginners.', 'About 45 minutes in total.')),
    # Check declarations and fixture layout.
    case(E + 'check-run-missing-rejected', 'req-check-declaration', 'schema-checks',
         sub('checks/checks.yaml', '  run: python "$AGENT_COURSE_DIR/checks/final_check.py"\n', '')),
    case(E + 'check-verify-missing-rejected', 'req-check-declaration', 'schema-checks',
         sub('checks/checks.yaml', '  verify: agent.py defines an agent\n', '')),
    case(E + 'check-observe-run-rejected', 'req-check-declaration', 'schema-checks',
         sub('checks/checks.yaml', 'exists and defines an agent\n', 'exists and defines an agent\n  run: python check.py\n')),
    case(E + 'check-timeout-zero-rejected', 'req-check-declaration', 'schema-checks', sub('checks/checks.yaml', 'timeout: 30', 'timeout: 0')),
    case(E + 'check-timeout-high-rejected', 'req-check-declaration', 'schema-checks', sub('checks/checks.yaml', 'timeout: 30', 'timeout: 301')),
    case(E + 'check-timeout-fraction-rejected', 'req-check-declaration', 'schema-checks', sub('checks/checks.yaml', 'timeout: 30', 'timeout: 1.5')),
    case(E + 'check-network-type-rejected', 'req-check-declaration', 'schema-checks',
         sub('checks/checks.yaml', 'network: false', 'network: "yes"')),
    case(E + 'check-unlisted-warning', 'req-check-declaration', (), check('spare-check'), warnings=('req-check-declaration',)),
    case(E + 'cwd-unquoted-warning', 'req-command-path', (),
         sub('checks/checks.yaml', '"$AGENT_COURSE_DIR/checks/final_check.py"', '$AGENT_COURSE_DIR/checks/final_check.py'),
         warnings=('req-command-path',)),
    case(E + 'fixture-undeclared-warning', 'req-check-rules', (), put('checks/fixtures/other-check/pass/agent.py', AGENT),
         warnings=('req-check-rules',)),
    case(E + 'check-id-duplicate-rejected', 'req-check-declaration', 'req-check-declaration',
         sub('checks/checks.yaml', '  network: false\n', '  network: false\n' + FINAL_ENTRY)),
    case(E + 'fixture-fail-missing-rejected', 'req-check-rules', 'req-check-rules', remove('checks/fixtures/final-check/fail')),
    # Quizzes, on the execution contract's quiz added to make.md.
    case(E + 'quiz-options-high-rejected', 'req-evidence-kinds', 'req-evidence-kinds', *QUIZ_BASELINE,
         sub('lessons/make.md', '   - In the checks file\n', '   - In the checks file\n   - Four\n   - Five\n   - Six\n')),
    case(E + 'quiz-options-low-rejected', 'req-evidence-kinds', 'req-evidence-kinds', *QUIZ_BASELINE,
         sub('lessons/make.md', '   - On the model\n   - On the agent object\n   - In the checks file\n', '   - On the agent object\n'),
         sub('tutor/make.quiz.yaml', '- answer: 1\n  why: Tools', '- answer: 0\n  why: Tools')),
    case(E + 'quiz-count-rejected', 'req-evidence-kinds', 'req-evidence-kinds', *QUIZ_BASELINE,
         sub('tutor/make.quiz.yaml', 'fix it.\n', 'fix it.\n- answer: 0\n  why: A third entry.\n')),
    case(E + 'quiz-answer-range-rejected', 'req-evidence-kinds', 'req-evidence-kinds', *QUIZ_BASELINE,
         sub('tutor/make.quiz.yaml', '- answer: 1\n  why: Tools', '- answer: 3\n  why: Tools')),
    case(E + 'quiz-why-missing-rejected', 'req-evidence-kinds', 'req-evidence-kinds', *QUIZ_BASELINE,
         sub('tutor/make.quiz.yaml', '  why: Exit 1 means the requirement is not met and the learner can fix it.\n', '')),
    # The final rubric.
    case(E + 'rubric-pass-missing-rejected', 'req-rubric', 'req-rubric', sub('tutor/finish.rubric.md', 'pass: 2 of 3\n', '')),
    case(E + 'rubric-zero-rejected', 'req-rubric', 'schema-rubric', sub('tutor/finish.rubric.md', 'pass: 2 of 3', 'pass: 0 of 3')),
    case(E + 'rubric-exceeds-rejected', 'req-rubric', 'req-rubric', sub('tutor/finish.rubric.md', 'pass: 2 of 3', 'pass: 4 of 3')),
    case(E + 'rubric-empty-rejected', 'req-rubric', 'schema-rubric', put('tutor/finish.rubric.md', '---\npass: 2 of 0\n---\n')),
    case(E + 'rubric-denominator-rejected', 'req-rubric', 'req-rubric',
         sub('tutor/finish.rubric.md', 'catch it\n', 'catch it\n- **Names a fourth thing** the agent does\n')),
    case(E + 'rubric-no-list-rejected', 'req-rubric', 'req-rubric',
         put('tutor/finish.rubric.md', '---\npass: 2 of 3\n---\nThe learner names the output type, the tool call and one failure mode.\n')),
    case(E + 'rubric-slash-rejected', 'req-rubric', 'schema-rubric', sub('tutor/finish.rubric.md', 'pass: 2 of 3', 'pass: 2/3')),
    case(E + 'rubric-leading-zero-rejected', 'req-rubric', 'schema-rubric', sub('tutor/finish.rubric.md', 'pass: 2 of 3', 'pass: 02 of 3')),
    # Feedback hooks, on the consent contract's feedback.yaml.
    case(C + 'hooks-rating-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', 'rating: per-lesson', 'rating: per-lesson-with-note')),
    case(C + 'hooks-stuck-low-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', 'after_failures: 3', 'after_failures: 1')),
    case(C + 'hooks-stuck-high-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', 'after_failures: 3', 'after_failures: 11')),
    case(C + 'hooks-stuck-fraction-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', 'after_failures: 3', 'after_failures: 2.5'), variant='fraction'),
    case(C + 'hooks-stuck-fraction-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', 'after_failures: 3', 'after_failures: "3"'), variant='text'),
    case(C + 'hooks-options-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', '[Anthropic, OpenAI, Google, Other]', '[Only one]')),
    case(C + 'hooks-question-id-rejected', 'req-closed-hooks', 'req-closed-hooks', FEEDBACK_BASELINE,
         sub('feedback.yaml', 'Other]\n', 'Other]\n  - id: provider\n    ask: Which provider do you use next?\n    options: [First, Second]\n')),
    case(C + 'hooks-questions-zero-rejected', 'req-closed-hooks', 'schema-feedback',
         put('feedback.yaml', FEEDBACK.split('questions:')[0] + 'questions: []\n')),
    case(C + 'hooks-questions-six-rejected', 'req-closed-hooks', 'schema-feedback',
         put('feedback.yaml', FEEDBACK.split('questions:')[0] + 'questions:\n' + ''.join(
             f'  - id: question-{n}\n    ask: Question {n}?\n    options: [First, Second]\n' for n in range(1, 7)))),
    case(C + 'hooks-ask-empty-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', 'ask: Which model provider do you use most?', 'ask: ""')),
    case(C + 'hooks-ask-long-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', 'ask: Which model provider do you use most?', 'ask: ' + 'a' * 201)),
    case(C + 'hooks-option-empty-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', '[Anthropic, OpenAI, Google, Other]', '[Anthropic, ""]')),
    case(C + 'hooks-option-long-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', '[Anthropic, OpenAI, Google, Other]', '[Anthropic, ' + 'o' * 81 + ']')),
    case(C + 'hooks-options-many-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', '[Anthropic, OpenAI, Google, Other]', '[' + ', '.join(f'Option {n}' for n in range(1, 10)) + ']')),
    case(C + 'hooks-question-id-form-rejected', 'req-closed-hooks', 'schema-feedback', FEEDBACK_BASELINE,
         sub('feedback.yaml', 'id: provider', 'id: Provider')),
    case(C + 'hooks-feedback-key-warning', 'req-unknown-keys', (), FEEDBACK_BASELINE,
         sub('feedback.yaml', 'rating: per-lesson\n', 'rating: per-lesson\ntheme: dark\n'), warnings=('req-unknown-keys',)),
    case(C + 'free-text-warning', 'req-no-free-text', (), FEEDBACK_BASELINE,
         sub('feedback.yaml', '    options: [Anthropic', '    free_text: true\n    options: [Anthropic'), warnings=('req-unknown-keys',)),
]

# Cases whose findings name a related requirement instead of, or as well as, the one listing them.
REPORTED_UNDER = {
    # The case shows that whole-course checks follow single-file checks; the duplicate objective decides it.
    F + 'markdown-only-duplicate-rejected': ('req-objective-ids-unique',),
    # The same escaping link is the local-folder case "Link leaves the source", the validator's home for it.
    F + 'ref-boundary-local-escape-rejected': ('req-local-materialisation',),
    # A rename cannot be told apart from a deletion plus an unrelated file, so the missing rubric is reported too.
    F + 'id-rubric-claim-rejected': ('req-lesson-id-and-stage', 'req-rubric'),
    # These cases show that a key is ignored; an unknown key is warned about under its own rule.
    F + 'evals-key-schema-rejected': ('req-unknown-keys',),
    F + 'evals-key-warning': ('req-unknown-keys',),
    F + 'id-lesson-frontmatter-id-warning': ('req-unknown-keys',),
    C + 'free-text-warning': ('req-unknown-keys',),
}

RUNNER = 'judged on what a runner does when it resolves or starts a project, not on the course folder'
RECORD = 'the recorded project path lives in learner records, which the record and event schema cases cover'
RUNS_CHECK = 'needs the check program run against its fixtures; course validation never runs a course command'
NOT_BUILT = {
    # This sweep uses the original quickstart and reader; these named cases need rc.2 interpretation.
    F + 'central-checks-null-rejected': 'needs the rc.2 course schema: checks is an ignored extension in the original reader',
    F + 'central-checks-type-rejected': 'needs rc.2 list validation: the original reader does not type-check central checks',
    F + 'central-feedback-null-rejected': 'needs the rc.2 course schema: feedback is an ignored extension in the original reader',
    F + 'central-feedback-type-rejected': 'needs rc.2 object validation: the original reader does not type-check central feedback',
    F + 'central-checks-duplicate-rejected': 'needs central check-id comparison; the original reader compares checks/checks.yaml entries only',
    F + 'central-check-shape-rejected': 'needs nested rc.2 check validation reported as schema-course; the original reader validates the separate checks file',
    F + 'central-extension-warning': 'needs an identified rc.2 baseline; the original reader additionally warns about its format and central fields',
    F + 'mixed-checks-equal-rejected': 'needs rc.2 rejection of a present checks/checks.yaml even when equal; the original reader uses that file',
    F + 'mixed-checks-empty-rejected': 'needs rc.2 presence rejection of empty checks/checks.yaml; the original reader has no mixed-layout rule',
    F + 'mixed-feedback-empty-rejected': 'needs rc.2 presence rejection of empty feedback.yaml; the original reader has no mixed-layout rule',
    F + 'mixed-feedback-equal-rejected': 'needs rc.2 rejection of a present feedback.yaml even when equal; the original reader uses that file',
    F + 'mixed-both-rejected': 'needs one rc.2 mixed-layout finding for both old files; the original reader treats them as declaration sources',
    F + 'mixed-precedence-rejected': 'needs rc.2 mixed-layout rejection before nested validation; the original reader has neither central loading nor that early boundary',
    F + 'resource-fixture-project-rejected': 'needs rc.2 fixture-role exclusion under scripts/fixtures; the original reader accepts contained local project sources',
    F + 'resource-fixture-starter-rejected': 'needs the rc.2 assets/starter base and resolved fixture-role exclusion; the original reader uses starter/',
    F + 'resource-markdown-relative-rejected': 'needs the otherwise valid rc.2 resource baseline; applying it to the original reader adds unrelated declaration and starter findings',
    F + 'resource-old-base-rejected': 'needs assets/starter as the rc.2 lesson base; starter/ is the valid base for this historical sweep',
    F + 'resource-selection-missing-rejected': RUNNER + '; this case also requires the rc.2 assets/starter source',
    E + 'candidate-copy-missing-rejected': 'needs rc.2 lesson resolution from assets/starter; the original reader searches starter/',
    E + 'candidate-copy-nonfile-rejected': 'needs the rc.2 resource baseline so only its selected directory fails; the original reader searches starter/',
    E + 'candidate-copy-source-escape-rejected': 'needs containment relative to the rc.2 assets/starter base; the original reader validates the historical starter base',
    C + 'candidate-feedback-duplicate-rejected': 'needs central feedback question-id comparison; the original reader compares feedback.yaml questions only',
    C + 'candidate-feedback-range-rejected': 'needs nested rc.2 feedback validation reported as schema-course; the original reader validates feedback.yaml',
    F + 'starter-answer-finished-rejected': 'needs a person to judge whether a starter file is a finished answer',
    F + 'version-rename-patch-rejected': 'needs two versions of a course to compare',
    F + 'version-rename-patch-warning': 'needs two versions of a course to compare',
    **{F + f'count-{name}-warning': 'the format makes the count lint later work; the course stays valid'
       for name in ('lesson-n', 'lesson-word', 'lesson-of', 'lessons', 'objectives', 'percent', 'total')},
    F + 'local-cwd-rejected': RUNNER,
    F + 'local-git-required-rejected': RUNNER,
    F + 'local-nonempty-destination-rejected': RUNNER,
    F + 'local-destination-in-course-rejected': RUNNER,
    F + 'local-destination-escape-rejected': RUNNER,
    F + 'local-unreadable-rejected': RUNNER + '; readability is not among the validator duties for local sources',
    E + 'prep-copy-after-lesson-rejected': RUNNER,
    E + 'prep-validate-after-copy-rejected': RUNNER,
    E + 'prep-run-code-rejected': RUNNER,
    F + 'selection-silence-rejected': RUNNER,
    F + 'selection-cannot-ask-rejected': RUNNER,
    F + 'selection-invalid-rejected': RUNNER,
    F + 'selection-not-listed-rejected': RUNNER,
    F + 'path-absolute-rejected': RECORD,
    F + 'path-drive-rejected': RECORD,
    F + 'path-traversal-rejected': RECORD,
    F + 'path-trailing-slash-rejected': RECORD,
    F + 'path-local-source-recorded-rejected': RECORD,
    F + 'path-local-dot-rejected': RECORD,
    **{E + name: RUNS_CHECK for name in ('fixture-container-rejected', 'fixture-fail-passes-rejected',
                                         'fixture-pass-fails-rejected', 'safety-mutating-rejected',
                                         'safety-random-rejected', 'safety-secret-dump-rejected',
                                         'safety-unhelpful-rejected')},
}


def test_register_cases_are_all_swept_or_explained():
    cases, _ = register()
    swept = {item.anchor for item in SWEEP}
    assert not swept & NOT_BUILT.keys()
    assert swept | NOT_BUILT.keys() == cases.keys()
    for item in SWEEP:
        assert item.requirement in cases[item.anchor], item.id


@pytest.mark.parametrize('item', SWEEP, ids=lambda item: item.id)
def test_register_case_reports_exactly_its_rule(tmp_path, item):
    _, enforcers = register()
    for rule in item.errors + item.warnings:
        if rule.startswith('schema-'):
            # A schema finding names the file type; that schema must enforce the governing requirement.
            kind = rule.removeprefix('schema-')
            assert 'schema' in enforcers[item.requirement] or c.FILE_RULES[kind] == item.requirement, item.id
        else:
            assert rule in REPORTED_UNDER.get(item.anchor, (item.requirement,)), item.id
    root = tmp_path / item.folder
    shutil.copytree(ROOT / 'examples/quickstart', root)
    for edit in item.edits:
        edit(root)
    findings = c.check_course(root)
    assert located_rules(findings, 'error') == sorted(item.errors), findings
    assert located_rules(findings, 'warning') == sorted(item.warnings), findings
    assert all('req-record-replay-data' not in f.message for f in findings)


def located_rules(findings, severity):
    """One rule per fault: a schema can report several keywords for one value at one location."""
    chosen = [f for f in findings if f.severity == severity]
    schema_locations = {(f.rule, f.path) for f in chosen if f.rule.startswith('schema-')}
    return sorted([rule for rule, _ in schema_locations] + [f.rule for f in chosen if not f.rule.startswith('schema-')])


# Faults of the same kinds as register cases, built the same way, that the register does not list.
SIBLINGS = {
    'call-repeated-in-one-lesson': (('req-call-ids-unique',), (), sub(
        'lessons/intro.md', 'first?\n', 'first?\n  - id: choose-tool\n    ask: Which tool next?\n')),
    'objective-repeated-in-one-lesson': (('req-objective-ids-unique',), (), sub(
        'lessons/finish.md', 'id: agent-explained', 'id: agent-passes')),
    'check-repeated-as-text-and-mapping': (('req-lesson-frontmatter',), (), sub(
        'lessons/make.md', 'checks: [agent-runs]', 'checks: [agent-runs, {id: agent-runs}]')),
    'lesson-id-not-kebab': (('req-kebab-ids',), (), move('lessons/make.md', 'lessons/Make.md'),
                            sub('COURSE.md', 'lessons/make.md', 'lessons/Make.md')),
    'source-sibling-link-cycle': (('req-local-materialisation',), (), local_source(), mkdir('examples/app/a'),
                                  mkdir('examples/app/b'), link('examples/app/a/to-b', '../b'),
                                  link('examples/app/b/to-a', '../a')),
    'source-nested-link-cycle': (('req-local-materialisation',), (), local_source(),
                                 link('examples/app/src/deep/up', '../..')),
    'source-shared-directory-links': ((), (), local_source(), mkdir('examples/app/a'), mkdir('examples/app/b'),
                                      link('examples/app/a/to-src', '../src'), link('examples/app/b/to-src', '../src')),
    'source-inner-file-link': ((), (), local_source(), link('examples/app/src/alias.py', 'main.py')),
    'missing-rubric-beside-unrelated-rubric': (('req-lesson-id-and-stage', 'req-rubric'), (),
                                               remove('tutor/finish.rubric.md'),
                                               put('tutor/unrelated.rubric.md', '---\npass: 1 of 1\n---\n- A criterion\n')),
    'missing-rubric-beside-unrelated-key': (('req-lesson-id-and-stage', 'req-rubric'), (), *QUIZ_BASELINE,
                                            remove('tutor/finish.rubric.md'), put('tutor/unrelated.quiz.yaml', QUIZ_KEY)),
    'missing-key-beside-unrelated-key': (('req-evidence-kinds', 'req-lesson-id-and-stage'), (), *QUIZ_BASELINE,
                                         remove('tutor/make.quiz.yaml'), put('tutor/unrelated.quiz.yaml', QUIZ_KEY)),
    'course-folder-in-single-quotes': ((), ('req-command-path',), sub(
        'checks/checks.yaml', '"$AGENT_COURSE_DIR/checks/final_check.py"', "'$AGENT_COURSE_DIR/checks/final_check.py'")),
    'course-folder-braced-unquoted': ((), ('req-command-path',), sub(
        'checks/checks.yaml', '"$AGENT_COURSE_DIR/checks/final_check.py"', '${AGENT_COURSE_DIR}/checks/final_check.py')),
    'course-folder-braced-quoted': ((), (), sub(
        'checks/checks.yaml', '"$AGENT_COURSE_DIR/checks/final_check.py"', '"${AGENT_COURSE_DIR}/checks/final_check.py"')),
}


@pytest.mark.parametrize(('errors', 'warnings', 'edits'), [(e, w, x) for e, w, *x in SIBLINGS.values()],
                         ids=SIBLINGS.keys())
def test_sibling_fault_reports_exactly_its_rule(quickstart, errors, warnings, edits):
    for edit in edits:
        edit(quickstart)
    findings = c.check_course(quickstart)
    assert located_rules(findings, 'error') == sorted(errors), findings
    assert located_rules(findings, 'warning') == sorted(warnings), findings
