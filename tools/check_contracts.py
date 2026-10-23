"""Internal candidate proof harness, not a public validator or qualified runner."""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import stat
import struct
import sys
import tempfile
import unicodedata

from jsonschema import Draft202012Validator, FormatChecker
from markdown_it import MarkdownIt
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource
import yaml


KINDS = ('course', 'lesson', 'checks', 'feedback', 'lock', 'record', 'event', 'rubric')
ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ('1.0.0-rc.1', '1.0.0-rc.2')
CURRENT = '1.0.0-rc.2'


DIALECT = 'https://json-schema.org/draft/2020-12/schema'


class ContractError(ValueError):
    """A contract rule prevents a complete, trustworthy result."""


@dataclass(frozen=True)
class Finding:
    rule: str
    path: str
    message: str
    severity: str


def refuse_retrieval(uri):
    raise NoSuchResource(ref=uri)


def schema_registry(root: Path, candidate: str | None = None):
    """Meta-validate all payloads and resolve references only from local resources."""
    manifest = json.loads((root / 'schemas/manifest.json').read_text())
    ownership = set()
    candidates = set()
    inventories = [manifest]
    for entry in manifest.get('retained', []):
        if (entry.get('status') != 'retained-unfrozen' or
            entry.get('manifest_path') != f"schemas/history/{entry.get('candidate')}/manifest.json" or
            not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', entry.get('source_commit', ''))):
            raise ContractError('schema-manifest: invalid retained inventory')
        retained_path = authored_path(root, entry['manifest_path'], rule='schema-manifest')
        retained_manifest = json.loads(retained_path.read_bytes())
        if retained_manifest.get('candidate') != entry['candidate'] or retained_manifest.get('retained'):
            raise ContractError('schema-manifest: retained candidate mismatch')
        inventories.append(retained_manifest)
    for inventory in inventories:
        candidate_name = inventory['candidate']
        if candidate_name in candidates:
            raise ContractError('schema-manifest: duplicate candidate')
        candidates.add(candidate_name)
        releases = inventory['releases']
        if len(releases) != 1 or releases[0]['candidate'] != candidate_name:
            raise ContractError('schema-manifest: candidate must have one release')
        for entry in releases[0]['schemas']:
            name = Path(entry['path']).name
            expected = f'schemas/{candidate_name}/{name}' if inventory is manifest and manifest.get('retained') else f'schemas/{name}'
            if entry['path'] != expected or entry['path'] in ownership:
                raise ContractError('schema-manifest: unsafe or duplicate payload ownership')
            ownership.add(entry['path'])
    actual = {path.relative_to(root).as_posix() for path in (root / 'schemas').rglob('*.schema.json')}
    if actual != ownership:
        raise ContractError('schema-manifest: unlisted or missing schema payload')
    candidate = manifest['candidate'] if candidate is None else candidate
    if candidate != manifest['candidate']:
        retained = [entry for entry in manifest.get('retained', []) if entry['candidate'] == candidate]
        if len(retained) != 1:
            raise ContractError('schema-manifest: unsupported candidate ' + candidate)
        manifest_path = authored_path(root, retained[0]['manifest_path'], rule='schema-manifest')
        if not manifest_path.is_relative_to((root / 'schemas').resolve()):
            raise ContractError('schema-manifest: retained manifest outside schemas')
        manifest = json.loads(manifest_path.read_bytes())
        if manifest['candidate'] != candidate:
            raise ContractError('schema-manifest: retained candidate mismatch')
    if manifest['dialect'] != DIALECT:
        raise ContractError('schema-dialect: expected Draft 2020-12')
    schemas = {}
    registry = Registry(retrieve=refuse_retrieval)
    releases = [r for r in manifest['releases'] if r['candidate'] == manifest['candidate']]
    if len(releases) != 1:
        raise ContractError('schema-manifest: candidate must have one release')
    for entry in releases[0]['schemas']:
        path = (root / entry['path']).resolve()
        if not path.is_relative_to(root.resolve() / 'schemas'):
            raise ContractError('schema-manifest: payload outside schemas')
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != entry['sha256']:
            raise ContractError('schema-hash: ' + entry['path'])
        schema = json.loads(payload)
        kind = path.name.removesuffix('.schema.json')
        expected = f"https://agentcourses.io/schemas/{manifest['candidate']}/{kind}.schema.json"
        if schema['$id'] != entry['id'] or entry['id'] != expected or schema['$schema'] != DIALECT:
            raise ContractError('schema-id: ' + entry['path'])
        Draft202012Validator.check_schema(schema)
        if kind in schemas:
            raise ContractError('schema-manifest: duplicate type')
        schemas[kind] = schema
        registry = registry.with_resource(schema['$id'], Resource.from_contents(schema))
    if set(schemas) != set(KINDS):
        raise ContractError('schema-manifest: expected eight types')

    def check_refs(value, resolver):
        if isinstance(value, dict):
            if '$ref' in value:
                resolver.lookup(value['$ref'])
            for child in value.values():
                check_refs(child, resolver)
        elif isinstance(value, list):
            for child in value:
                check_refs(child, resolver)
    for schema in schemas.values():
        check_refs(schema, registry.resolver(schema['$id']))
    return schemas, registry


@lru_cache(maxsize=2)
def default_registry(candidate=None):
    return schema_registry(ROOT, candidate)


class UniqueSafeLoader(yaml.SafeLoader):
    """Safe YAML without implicit timestamps, duplicate keys or recursive aliases."""


UniqueSafeLoader.yaml_implicit_resolvers = {
    key: [(tag, rx) for tag, rx in values if tag != 'tag:yaml.org,2002:timestamp']
    for key, values in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ContractError('yaml-mapping: duplicate or non-string key')
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def decode_yaml(text: str):
    try:
        value = yaml.load(text, Loader=UniqueSafeLoader)
        # JSON conversion refuses cycles, non-finite numbers, sets and opaque YAML types.
        json.dumps(value, allow_nan=False)
        return value
    except (yaml.YAMLError, ValueError, TypeError, RecursionError) as error:
        raise ContractError('yaml-syntax: ' + str(error)) from error


def decode_markdown(text: str):
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip('\n') != '---':
        raise ContractError('frontmatter: missing opening delimiter')
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip('\n') == '---'), None)
    if end is None:
        raise ContractError('frontmatter: missing closing delimiter')
    data = decode_yaml(''.join(lines[1:end]))
    if not isinstance(data, dict):
        raise ContractError('frontmatter: expected mapping')
    return data, ''.join(lines[end + 1:])


# The requirement that governs each file type's own shape, including whether it can be read.
FILE_RULES = dict(course='req-course-frontmatter', lesson='req-lesson-frontmatter',
                  checks='req-check-declaration', feedback='req-closed-hooks',
                  rubric='req-rubric', event='req-record-event-fields',
                  lock='req-record-lock', record='req-record-fields')


def _semantic_shape(kind, data, *, central=True):
    """Check comparisons and keyed uniqueness that JSON Schema cannot express."""
    findings = []

    def error(message, rule=None):
        findings.append(Finding(rule or FILE_RULES[kind], '', message, 'error'))

    def unique(items, key, rule=None):
        values = [key(item) for item in items]
        if len(values) != len(set(values)):
            error('duplicate identifiers', rule)

    def judge(value):
        if value['met'] > value['of']:
            error('met exceeds of')

    if kind == 'course' and central:
        if 'checks' in data:
            findings += _semantic_shape('checks', data['checks'])
        if 'feedback' in data:
            findings += _semantic_shape('feedback', data['feedback'])
    if kind == 'rubric':
        k, n = map(int, data['pass'].split(' of '))
        if k > n:
            error('pass numerator exceeds denominator')
    if kind == 'checks':
        unique(data, lambda v: v['id'])
    if kind == 'feedback' and 'questions' in data:
        unique(data['questions'], lambda v: v['id'])
    if kind == 'lesson':
        unique(data.get('checks', []), lambda v: v if isinstance(v, str) else v['id'])
        # Call and objective ids are unique across the course, and so within one lesson too.
        unique(data.get('calls', []), lambda v: v['id'], 'req-call-ids-unique')
        unique(data.get('objectives', []), lambda v: v['id'], 'req-objective-ids-unique')
    if kind == 'event' and data['kind'] == 'explain-judged':
        judge(data)
    if kind == 'lock':
        names = [v['name'] for v in data['courses']]
        if names != sorted(set(names), key=lambda v: v.encode()):
            error('course names must be unique and byte-sorted')
    if kind == 'record':
        for segment in [data, *data['history']]:
            for name in ('calls', 'objectives'):
                unique(segment[name], lambda v: (v['lesson'], v['id']))
            for lesson in segment['lessons'].values():
                if 'explain' in lesson:
                    judge(lesson['explain'])
        destinations = [v['destination'] for v in data['consent']]
        if destinations != sorted(set(destinations), key=lambda v: v.encode()):
            error('consent destinations must be unique and byte-sorted')
        unique(data['declined'], lambda v: (v['destination'], v['hook'], v['lesson']))
    return findings


def _unknown_fields(kind, data, schema, registry, path=''):
    if '$ref' in schema:
        resolved = registry.resolver().lookup(schema['$ref'])
        schema = resolved.contents
    findings = []
    if isinstance(data, dict):
        properties = schema.get('properties', {})
        if properties and schema.get('additionalProperties', True) is True:
            for key in data.keys() - properties.keys():
                findings.append(Finding('req-unknown-keys', path + '/' + key, 'unknown field ignored', 'warning'))
        for key in data.keys() & properties.keys():
            findings += _unknown_fields(kind, data[key], properties[key], registry, path + '/' + key)
    if isinstance(data, list) and 'items' in schema:
        for i, value in enumerate(data):
            findings += _unknown_fields(kind, value, schema['items'], registry, path + '/' + str(i))
    return findings


def validate_frontmatter(kind: str, data: Mapping[str, object], *, candidate=None) -> list[Finding]:
    return _validate(kind, data, default_registry(candidate))


TIME_FORMATS = FormatChecker(formats=[])


@TIME_FORMATS.checks('date-time', raises=ValueError)
def utc_time(value):
    """Assert the contract's UTC spelling and a real Gregorian date and time."""
    if not isinstance(value, str):
        return True  # The schema's type assertion handles other values.
    if not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z', value):
        return False
    datetime.fromisoformat(value[:-1] + '+00:00')
    return True


def _validate(kind, data, context):
    if kind not in KINDS:
        return [Finding('schema-kind', kind, 'unknown schema kind', 'error')]
    schemas, registry = context
    validator = Draft202012Validator(schemas[kind], registry=registry, format_checker=TIME_FORMATS)
    findings = [Finding('schema-' + kind, '/'.join(map(str, e.absolute_path)), f'[{e.validator}] {e.message}', 'error')
                for e in validator.iter_errors(data)]
    if not findings:
        findings += _semantic_shape(kind, data, central=schemas['course']['$id'].split('/')[-2] == CURRENT)
        if kind in ('course', 'lesson', 'checks', 'feedback', 'rubric'):
            findings += _unknown_fields(kind, data, schemas[kind], registry)
    return findings


MARKDOWN = MarkdownIt('commonmark')


def text_bytes(payload):
    return payload.decode('utf-8').replace('\r\n', '\n')


def included(path: str):
    parts = path.split('/')
    return not any(p in ('.git', '.DS_Store') for p in parts) and parts[0] not in ('.agents', '_site')


def authored_path(root: Path, name: str, *, rule='req-record-replay-data'):
    path = root / name
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(root.resolve()).as_posix()
        if not included(relative):
            raise ValueError('excluded target')
        # Every component a metadata link traverses must also be identity-included.
        current = root
        for part in Path(name).parts:
            current = current / part
            if current.is_symlink():
                target = current.resolve(strict=True).relative_to(root.resolve()).as_posix()
                if not included(target):
                    raise ValueError('excluded metadata link')
        return resolved
    except (OSError, RuntimeError, ValueError) as error:
        raise ContractError(rule + ': unsafe or missing metadata ' + name) from error


def read_authored(root, name, *, rule='req-record-replay-data'):
    return text_bytes(authored_path(root, name, rule=rule).read_bytes())


def sections(body):
    tokens = MARKDOWN.parse(body)
    headings = []
    for i, token in enumerate(tokens):
        if token.type == 'heading_open' and token.tag == 'h2':
            headings.append((tokens[i+1].content, i))
    result = {}
    for i, (name, start) in enumerate(headings):
        end = headings[i+1][1] if i+1 < len(headings) else len(tokens)
        result.setdefault(name, []).append(tokens[start+3:end])
    return tokens, result


def links(tokens):
    for token in tokens:
        for child in token.children or []:
            if child.type in ('link_open', 'image'):
                yield child.attrGet('href') or child.attrGet('src')


def ordered_lessons(section):
    if len(section) != 1:
        raise ContractError('req-lesson-list: exactly one Lessons section required')
    tokens = section[0]
    lists = [t for t in tokens if t.type == 'ordered_list_open']
    if len(lists) != 1 or lists[0].level != 0:
        raise ContractError('req-lesson-list: exactly one ordered list required')
    items = []
    for i, token in enumerate(tokens):
        if token.type == 'list_item_open':
            if token.level != 1:
                raise ContractError('req-lesson-list: nested lesson item')
            end = next(j for j in range(i+1, len(tokens)) if tokens[j].type == 'list_item_close' and tokens[j].level == token.level)
            targets = list(links(tokens[i+1:end]))
            if len(targets) != 1 or not re.fullmatch(r'lessons/[^/]+\.md', targets[0]):
                raise ContractError('req-lesson-list: each item needs one lesson target')
            items.append(Path(targets[0]).stem)
    if not items or len(set(items)) != len(items):
        raise ContractError('req-lesson-list: empty or duplicate list')
    return items


def project_link(target):
    value = target.removeprefix('project:')
    path, sep, fragment = value.partition('#')
    path = unquote(path, errors='strict')
    if not path or path.startswith('/') or '\\' in path or '?' in path or any(p in ('', '.', '..') for p in path.split('/')) or any(ord(c)<32 or ord(c)==127 for c in path):
        raise ContractError('req-project-lines: invalid project path')
    end = None
    if sep:
        match = re.fullmatch(r'L([1-9][0-9]*)(?:-L([1-9][0-9]*))?', fragment)
        if not match or int(match[1]) > int(match[2] or match[1]):
            raise ContractError('req-project-lines: invalid line range')
        end = int(match[2] or match[1])
    return path, end


def _candidate_guard(root, course, candidate):
    if candidate not in CANDIDATES:
        raise ContractError('req-format-identifier: unsupported candidate ' + str(candidate))
    if candidate == CURRENT:
        if course.get('format') != CURRENT:
            raise ContractError('req-format-identifier: expected format "1.0.0-rc.2"')
        if any((root / name).exists() or (root / name).is_symlink()
               for name in ('checks/checks.yaml', 'feedback.yaml')):
            raise ContractError('req-mixed-declarations: legacy declaration file present')


def _course_header(root, candidate):
    try:
        course, body = decode_markdown(read_authored(root, 'COURSE.md'))
        _candidate_guard(root, course, candidate)
        errors = [f for f in validate_frontmatter('course', course, candidate=candidate) if f.severity == 'error']
        if errors:
            raise ContractError('; '.join(f.rule + ': ' + f.message for f in errors))
        return course, body
    except (OSError, UnicodeError) as error:
        raise ContractError('req-course-frontmatter: unreadable COURSE.md') from error


def course_metadata(root: Path, *, candidate: str = CURRENT) -> tuple[Mapping, Mapping, Mapping, tuple[int, int]]:
    course, body = _course_header(root, candidate)
    _, parts = sections(body)
    order = ordered_lessons(parts.get('Lessons', []))
    lessons = {name: decode_markdown(read_authored(root, f'lessons/{name}.md'))[0] for name in order}
    checkfile = root / 'checks/checks.yaml'
    checks = course.get('checks', []) if candidate == CURRENT else (decode_yaml(read_authored(root, 'checks/checks.yaml')) if checkfile.is_symlink() or checkfile.exists() else [])
    rubric, _ = decode_markdown(read_authored(root, f'tutor/{order[-1]}.rubric.md'))
    k, n = map(int, rubric['pass'].split(' of '))
    return course, lessons, {v['id']: v for v in checks}, (k, n)


def catalogue_summary(root: Path, *, candidate: str = CURRENT) -> Mapping[str, object]:
    course, _ = _course_header(root, candidate)
    return {key: course[key] for key in ('name', 'description', 'version', 'license', 'compatibility', 'spec') if key in course}


def _starter_base(candidate):
    return 'assets/starter' if candidate == CURRENT else 'starter'


def _resource_role(root, source, candidate):
    if candidate == CURRENT and source.is_relative_to((root / 'tutor').resolve()):
        raise ContractError('req-resource-roles: tutor material is not learner source')
    if candidate == CURRENT and source.is_relative_to((root / 'scripts/fixtures').resolve()):
        raise ContractError('req-resource-roles: check fixtures are not learner source')


def _project_source(root, selection, candidate):
    name = _starter_base(candidate) if selection == 'starter' else selection[2:]
    source = authored_path(root, name, rule='req-project-field' if selection == 'starter' else 'req-local-materialisation')
    _resource_role(root, source, candidate)
    if not source.is_dir():
        raise ContractError('req-project-field: project source must be a directory')
    try:
        for child in source.rglob('*'):
            _resource_role(root, child.resolve(), candidate)
        entries, files = walk_source(source)
    except (OSError, RuntimeError) as error:
        raise ContractError('req-project-field: unreadable or unsafe project source') from error
    if not (files if selection == 'starter' else entries):
        raise ContractError('req-project-field: project source must be non-empty')
    return source


def resolve_project(root: Path, selection: str | None, *, candidate: str = CURRENT) -> Path | None:
    course, _ = _course_header(root, candidate)
    options = course.get('project', 'own')
    options = options if isinstance(options, list) else [options]
    if selection is None or selection not in options:
        raise ContractError('req-project-selection: supply an explicitly selected project option')
    if selection == 'own':
        return None
    if selection == 'starter' or selection.startswith('./'):
        return _project_source(root, selection, candidate)
    raise ContractError('req-project-selection: remote source is unavailable offline')


def starter_sources(root: Path, *, lesson_id: str | None = None, candidate: str = CURRENT) -> Mapping[str, bytes]:
    _, body = _course_header(root, candidate)
    if lesson_id is None:
        source = _project_source(root, 'starter', candidate)
        result = {}
        def collect(directory, prefix=''):
            for path in sorted(directory.iterdir()):
                name = prefix + path.name
                if path.is_dir():
                    collect(path, name + '/')
                elif path.is_file():
                    result[name] = path.read_bytes()
        try:
            collect(source)
        except (OSError, RuntimeError) as error:
            raise ContractError('req-starter-files: unreadable starter source') from error
        return result
    _, parts = sections(body)
    if lesson_id not in ordered_lessons(parts.get('Lessons', [])):
        raise ContractError('req-starter-files: unknown lesson ' + lesson_id)
    try:
        lesson, _ = decode_markdown(read_authored(root, f'lessons/{lesson_id}.md'))
    except (OSError, UnicodeError) as error:
        raise ContractError('req-starter-files: unreadable lesson') from error
    errors = [f for f in validate_frontmatter('lesson', lesson, candidate=candidate) if f.severity == 'error']
    if errors:
        raise ContractError('req-starter-files: invalid lesson')
    result = {}
    for name in lesson.get('starter', []):
        base = authored_path(root, _starter_base(candidate), rule='req-starter-files')
        source = authored_path(root, _starter_base(candidate) + '/' + name, rule='req-starter-files')
        _resource_role(root, source, candidate)
        if not source.is_relative_to(base) or not source.is_file():
            raise ContractError('req-starter-files: entry must be a contained file')
        try:
            result[name] = source.read_bytes()
        except OSError as error:
            raise ContractError('req-starter-files: unreadable starter source') from error
    return result


def copy_starter(files: Mapping[str, bytes], destination: Path) -> None:
    destination = Path(destination)
    targets = []
    try:
        for name, payload in files.items():
            _path_check(name)
            if Path(name).is_absolute() or re.match(r'^[A-Za-z]:', name) or not isinstance(payload, bytes):
                raise ValueError('invalid starter entry')
            path = destination / name
            if path.exists() or path.is_symlink():
                raise ValueError('destination collision: ' + name)
            for parent in path.parents:
                if parent == destination.parent:
                    break
                if parent.is_symlink() or parent.exists() and not parent.is_dir():
                    raise ValueError('unsafe destination parent')
            if any(name.startswith(other + '/') or other.startswith(name + '/') for other in files if other != name):
                raise ValueError('overlapping starter entries')
            targets.append((path, payload))
        # Probe absent names on their actual filesystem: case folding and other
        # aliases cannot be inferred portably from strings or Path.resolve().
        probes = {}
        for path, _ in targets:
            anchor = path.parent
            while not anchor.exists():
                anchor = anchor.parent
            state = anchor.stat()
            key = (state.st_dev, state.st_ino)
            if key not in probes:
                probes[key] = (anchor, [])
            probes[key][1].append(path.relative_to(anchor))
        for anchor, names in probes.values():
            with tempfile.TemporaryDirectory(prefix='.agent-courses-copy-', dir=anchor) as temporary:
                for name in names:
                    probe = Path(temporary) / name
                    probe.parent.mkdir(parents=True, exist_ok=True)
                    # Exclusive placeholders detect both leaf and ancestor
                    # aliases before any learner destination receives payloads.
                    with probe.open('xb'):
                        pass
    except (ContractError, OSError, ValueError) as error:
        raise ContractError('req-starter-copy: ' + str(error)) from error
    for path, payload in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)


COURSE_HEADINGS = ('Outcome', 'Lessons', 'Before you start', 'Project')
LESSON_HEADINGS = ('Goal', 'Build', 'Hints', 'Quiz', 'Explain back')
KEBAB_ID = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
# Files in tutor/ that name a lesson by its id.
TUTOR_SUFFIXES = ('.rubric.md', '.quiz.yaml')
# The course folder's path may contain spaces, so its expansion belongs inside double quotes.
COURSE_DIR_EXPANSION = re.compile(r'\$(?:AGENT_COURSE_DIR\b|\{AGENT_COURSE_DIR\})')


def unquoted_expansion(command):
    """Whether a command expands the course folder anywhere outside double quotes."""
    quote, i = None, 0
    while i < len(command):
        char = command[i]
        if char == '\\' and quote != "'":
            i += 2  # An escaped character is literal.
            continue
        if char in '"\'' and quote in (None, char):
            quote = None if quote else char
        elif quote != '"' and COURSE_DIR_EXPANSION.match(command, i):
            return True
        i += 1
    return False


def walk_source(source):
    """Follow a project source the way it is copied; return its entry and file counts.

    Links are followed into directories, so a link back to a directory still being
    walked is a cycle, wherever the two directories sit.
    """
    counts = {'entries': 0, 'files': 0}
    active, finished = set(), set()

    def visit(directory):
        active.add(directory)
        for entry in sorted(directory.iterdir()):
            counts['entries'] += 1
            resolved = entry.resolve(strict=True)
            if not resolved.is_relative_to(source):
                raise ContractError('unsafe local source entry')
            if resolved.is_dir():
                if resolved in active:
                    raise ContractError('local source link cycle')
                if resolved not in finished:
                    visit(resolved)
            elif resolved.is_file():
                counts['files'] += 1
            else:
                raise ContractError('unsafe local source entry')
        active.discard(directory)
        finished.add(directory)

    visit(source)
    return counts['entries'], counts['files']


def quiz_options(section):
    """Count the options under each question of a Quiz section's one numbered list."""
    starts = [i for i, t in enumerate(section) if t.type == 'ordered_list_open' and t.level == 0]
    if len(starts) != 1:
        raise ContractError('quiz must be one numbered list')
    end = next(i for i in range(starts[0], len(section))
               if section[i].type == 'ordered_list_close' and section[i].level == 0)
    counts = []
    for token in section[starts[0]:end]:
        if token.type == 'list_item_open' and token.level == 1:
            counts.append(0)
        elif token.type == 'list_item_open' and token.level == 3:
            counts[-1] += 1
    return counts


def check_quiz_key(key, options):
    """Check a decoded quiz key against the option count of each question."""
    if not isinstance(key, list) or len(key) != len(options):
        raise ContractError('quiz key needs one entry per question, in order')
    for entry, count in zip(key, options):
        if not isinstance(entry, dict) or 'answer' not in entry or not isinstance(entry.get('why'), str):
            raise ContractError('quiz key entry needs an answer and a why')
        answer = entry['answer']
        if type(answer) is not int or not 0 <= answer < count:
            raise ContractError(f'quiz answer {answer!r} is not one of {count} option positions')


def check_course(root: Path, *, candidate: str = CURRENT) -> list[Finding]:
    """Check authored syntax and relationships; never execute a course command.

    Each fault is reported once: as a schema finding when one file's shape is wrong,
    otherwise under the requirement that governs it. When a file cannot be read or
    fails its shape, the checks that depend on its content are skipped rather than
    reported as further faults.
    """
    root = Path(root)
    findings = []

    def report(rule, path, message, severity='error'):
        findings.append(Finding(rule, str(root / path), message, severity))

    def present(name):
        path = root / name
        return path.is_symlink() or path.exists()

    def load(name, kind, markdown=True):
        """Return a file's valid data and body, or None for data after reporting its fault."""
        rule = FILE_RULES[kind]
        try:
            text = read_authored(root, name, rule=rule)
            data, body = decode_markdown(text) if markdown else (decode_yaml(text), '')
        except (ContractError, OSError, UnicodeError) as error:
            report(rule, name, str(error))
            return None, ''
        if kind == 'course':
            try:
                _candidate_guard(root, data, candidate)
            except ContractError as error:
                report(str(error).split(':')[0], name, str(error))
                return None, body
        shaped = validate_frontmatter(kind, data, candidate=candidate)
        findings.extend(Finding(f.rule, str(root / name) + (':' + f.path if f.path else ''), f.message, f.severity) for f in shaped)
        if any(f.severity == 'error' for f in shaped):
            return None, body
        return data, body

    def headings(parts, required, recognised, path, rule):
        for heading in recognised:
            count = len(parts.get(heading, []))
            if count > 1 or (heading in required and count != 1):
                expected = 'once' if heading in required else 'at most once'
                report(rule, path, f'{heading}: expected {expected}')

    def lesson_order(parts, lesson_files):
        """Return the listed lesson ids and whether they are the course's exact order."""
        if len(parts.get('Lessons', [])) != 1:
            return [], False  # The heading rule has already reported the missing or repeated heading.
        try:
            listed = ordered_lessons(parts['Lessons'])
        except ContractError as error:
            report('req-lesson-list', 'COURSE.md', str(error))
            return [], False
        if set(listed) != lesson_files:
            report('req-lesson-list', 'COURSE.md', 'listed lessons must match lesson files exactly')
            return listed, False
        return listed, True

    def misnamed_tutor_files(lesson_ids):
        """Report tutor files whose name is not a lesson id."""
        for suffix in TUTOR_SUFFIXES:
            for path in sorted((root / 'tutor').glob('*' + suffix)):
                lesson_id = path.name.removesuffix(suffix)
                if lesson_id not in lesson_ids:
                    report('req-lesson-id-and-stage', f'tutor/{path.name}', f'names no lesson: {lesson_id}')

    def check_goal_links(path, lesson_parts):
        for goal in lesson_parts.get('Goal', []):
            for target in links(goal):
                if target.startswith(('https:', 'project:')):
                    continue
                try:
                    relative = unquote(urlsplit(target).path) or 'COURSE.md'
                    resolved = authored_path(root, relative, rule='req-course-links')
                except ContractError:
                    continue  # The general link check reports unsafe or missing targets.
                if resolved.is_relative_to(root.resolve() / 'tutor'):
                    report('req-course-links', path, 'tutor link in Goal')

    def check_quiz(name, path, section):
        key_path = f'tutor/{name}.quiz.yaml'
        try:
            options = quiz_options(section)
            if not options or any(count not in range(2, 6) for count in options):
                raise ContractError('each question needs two to five options')
        except ContractError as error:
            report('req-evidence-kinds', path, str(error))
            return
        if not (root / key_path).is_file():
            report('req-evidence-kinds', key_path, 'missing quiz key')
            return
        try:
            check_quiz_key(decode_yaml(read_authored(root, key_path, rule='req-evidence-kinds')), options)
        except (ContractError, OSError, UnicodeError) as error:
            report('req-evidence-kinds', key_path, str(error))

    def check_rubric(name):
        rubric_path = f'tutor/{name}.rubric.md'
        if not (root / rubric_path).is_file():
            report('req-rubric', rubric_path, 'missing final rubric')
            return
        rubric, body = load(rubric_path, 'rubric')
        if rubric is None:
            return
        criteria = sum(t.type == 'list_item_open' and t.level == 1 for t in MARKDOWN.parse(body))
        if criteria != int(rubric['pass'].split(' of ')[1]):
            report('req-rubric', rubric_path, 'criteria count differs from denominator')

    def check_project_source(option):
        rule = 'req-project-field' if option == 'starter' else 'req-local-materialisation'
        try:
            _project_source(root, option, candidate)
        except (ContractError, OSError, RuntimeError) as error:
            actual = 'req-resource-roles' if str(error).startswith('req-resource-roles:') else rule
            report(actual, 'COURSE.md', str(error))

    def check_baseline_link(source, relative, end):
        """Check a project link against a local source as the course holds it."""
        try:
            base = authored_path(root, source, rule='req-local-materialisation')
        except ContractError:
            return  # The project-source check reports a missing or unsafe source once.
        try:
            file = (base / relative).resolve(strict=True)
            if not file.is_relative_to(base) or not file.is_file():
                raise ContractError('target is not a file inside the source')
            if end and end > len(text_bytes(file.read_bytes()).splitlines()):
                raise ContractError('line range ends after the last line')
        except (ContractError, OSError, RuntimeError, UnicodeError) as error:
            raise ContractError(f'req-local-link-timing: missing or out-of-bounds local target {relative}') from error

    def check_link(path, target, visible, options):
        if target.startswith('https:'):
            return
        if target.startswith('project:'):
            relative, end = project_link(target)
            for option in options:
                if option.startswith('./'):
                    check_baseline_link(option[2:], relative, end)
                elif option.startswith(('gh:', 'git+https:')):
                    report('req-local-link-timing', path, 'Git baseline unavailable offline', 'warning')
            return
        split = urlsplit(target)
        relative = unquote(split.path)
        if split.scheme or relative.startswith('/') or '\\' in relative:
            raise ContractError('invalid course link')
        resolved = authored_path(root, relative or 'COURSE.md', rule='req-course-links')
        if visible and resolved.is_relative_to(root.resolve() / 'tutor'):
            raise ContractError('tutor link in course page')

    if not (root / 'COURSE.md').is_file():
        report('req-folder-and-name', 'COURSE.md', 'course folder requires COURSE.md')
        return findings
    course, body = load('COURSE.md', 'course')
    if course is None:
        return findings
    if root.name != course['name']:
        report('req-folder-and-name', 'COURSE.md', 'folder name must equal course name')
    tokens, parts = sections(body)
    headings(parts, {'Outcome', 'Lessons'}, COURSE_HEADINGS, 'COURSE.md', 'req-course-headings')
    lesson_files = {p.stem for p in (root / 'lessons').glob('*.md')}
    listed, order_known = lesson_order(parts, lesson_files)
    misnamed_tutor_files(lesson_files | set(listed))

    checks = {}
    checks_known = True
    declaration_path = 'COURSE.md' if candidate == CURRENT else 'checks/checks.yaml'
    fixture_base = 'scripts/fixtures' if candidate == CURRENT else 'checks/fixtures'
    if candidate == CURRENT:
        checks = {check['id']: check for check in course.get('checks', [])}
    elif present('checks/checks.yaml'):
        declared, _ = load('checks/checks.yaml', 'checks', markdown=False)
        checks_known = declared is not None
        checks = {check['id']: check for check in declared or []}
    for check_id, check in checks.items():
        if check.get('kind', 'command') == 'command':
            for outcome in ('pass', 'fail'):
                if not (root / fixture_base / check_id / outcome).is_dir():
                    report('req-check-rules', declaration_path, f'{check_id}: missing {outcome} project fixture')
            if unquoted_expansion(check['run']):
                report('req-command-path', declaration_path,
                       f'{check_id}: write the course folder expansion in double quotes', 'warning')
    if candidate != CURRENT and present('feedback.yaml'):
        load('feedback.yaml', 'feedback', markdown=False)

    calls_seen, objectives_seen, used = set(), set(), set()
    stages = []
    lessons_valid = True
    references_known = True
    # Lesson-list targets have their own rule, including missing and unsafe targets.
    list_tokens = {id(token) for section in parts.get('Lessons', []) for token in section}
    documents = [('COURSE.md', [t for t in tokens if id(t) not in list_tokens], True)]
    for name in [n for n in listed if n in lesson_files] + sorted(lesson_files - set(listed)):
        path = f'lessons/{name}.md'
        if not KEBAB_ID.fullmatch(name) or len(name) > 64:
            report('req-kebab-ids', path, 'lesson identifier must be a kebab id of 1 to 64 characters')
        elif name == 'explain-back':
            report('req-explain-back-reserved', path, 'lesson identifier is reserved')
        lesson, body = load(path, 'lesson')
        if lesson is None:
            lessons_valid = False
            continue
        stage = lesson['stage']
        stages.append(stage)
        body_tokens, lesson_parts = sections(body)
        required = {'Goal'}
        if stage in ('practise', 'build'):
            required.add('Build')
        if stage == 'demonstrate':
            required.add('Explain back')
        headings(lesson_parts, required, LESSON_HEADINGS, path, 'req-lesson-heading-cardinality')
        if stage != 'demonstrate' and 'Explain back' in lesson_parts:
            report('req-lesson-heading-cardinality', path, 'Explain back requires demonstrate')
        documents.append((path, body_tokens, False))
        check_goal_links(path, lesson_parts)

        refs = {v if isinstance(v, str) else v['id'] for v in lesson.get('checks', [])}
        used |= refs
        if checks_known and refs - checks.keys():
            references_known = False
            report('req-lesson-frontmatter', path, 'unknown check: ' + ', '.join(sorted(refs - checks.keys())))
        for field, seen, rule in (('calls', calls_seen, 'req-call-ids-unique'),
                                  ('objectives', objectives_seen, 'req-objective-ids-unique')):
            for value in lesson.get(field, []):
                if value['id'] in seen:
                    report(rule, path, 'duplicate id: ' + value['id'])
                seen.add(value['id'])
        for objective in lesson.get('objectives', []):
            selector = objective['by']
            explain_back_elsewhere = selector == 'explain-back' and stage != 'demonstrate'
            check_elsewhere = selector != 'explain-back' and selector not in refs
            if explain_back_elsewhere or check_elsewhere:
                report('req-objective-ids-unique', path,
                       'objective evidence must be a same-lesson check or final explain-back')
        if lesson.get('starter'):
            try:
                starter_sources(root, lesson_id=name, candidate=candidate)
            except (ContractError, OSError, RuntimeError) as error:
                rule = 'req-resource-roles' if str(error).startswith('req-resource-roles:') else 'req-starter-files'
                report(rule, path, str(error))
        if len(lesson_parts.get('Quiz', [])) == 1:
            check_quiz(name, path, lesson_parts['Quiz'][0])
        if stage == 'demonstrate':
            check_rubric(name)

    if order_known and lessons_valid:
        if not stages or stages[-1] != 'demonstrate' or stages.count('demonstrate') != 1:
            report('req-final-demonstrate', 'COURSE.md', 'last lesson must be the only demonstrate lesson')
        if references_known:
            for check_id in sorted(checks.keys() - used):
                report('req-check-declaration', declaration_path, check_id + ': check is unused', 'warning')
    # A lesson listing an undeclared check shows the declarations are incomplete, so fixtures are not judged unused.
    if checks_known and references_known and (root / fixture_base).is_dir():
        for folder in sorted((root / fixture_base).iterdir()):
            if folder.is_dir() and folder.name not in checks:
                report('req-check-rules', f'{fixture_base}/{folder.name}', 'fixtures for an undeclared check', 'warning')

    options = course.get('project', 'own')
    options = options if isinstance(options, list) else [options]
    for option in options:
        if option == 'starter' or option.startswith('./'):
            check_project_source(option)
    for path, doc_tokens, visible in documents:
        for target in links(doc_tokens):
            try:
                check_link(path, target, visible, options)
            except (ContractError, OSError, UnicodeError, ValueError) as error:
                message = str(error)
                own_rule = message.startswith(('req-project-lines:', 'req-local-link-timing:'))
                report(message.split(':')[0] if own_rule else 'req-course-links', path, message)
    return findings


def _path_check(path):
    try:
        if len(path.encode('utf-8')) > 1024:
            raise ValueError('path too long')
        for part in path.split('/'):
            if (part in ('', '.', '..') or len(part.encode('utf-8')) > 255 or
                unicodedata.normalize('NFC', part) != part or '\\' in part or
                any(ord(c) < 32 or ord(c) == 127 for c in part)):
                raise ValueError('invalid component')
    except (UnicodeError, ValueError) as error:
        raise ContractError('invalid-path: ' + repr(path)) from error


def _capture(root):
    """Capture raw bytes without following links and detect concurrent changes."""
    root = Path(root)
    if not root.is_dir() or not (root/'COURSE.md').is_file() or (root/'COURSE.md').is_symlink():
        raise ContractError('not-a-course: regular COURSE.md required')
    entries = {}
    observed = {}

    def stamp(path):
        s = path.lstat()
        return (s.st_dev,s.st_ino,s.st_mode,s.st_size,s.st_mtime_ns,s.st_ctime_ns)

    def walk(directory, prefix=''):
        before = stamp(directory)
        names = list(directory.iterdir())
        active = [p for p in names if included(prefix+p.name)]
        for path in active:
            name = prefix+path.name
            _path_check(name)
            state = stamp(path)
            mode=state[2]
            if stat.S_ISLNK(mode):
                try:
                    payload=os.readlink(path).encode('utf-8')
                except UnicodeError as error:
                    raise ContractError('invalid-link: '+name) from error
                if not payload or len(payload)>4096 or b'\0' in payload:
                    raise ContractError('invalid-link: '+name)
                entries[name]=('l',payload)
            elif stat.S_ISREG(mode):
                entries[name]=('f',path.read_bytes())
            elif stat.S_ISDIR(mode):
                walk(path,name+'/')
            else:
                raise ContractError('special-file: '+name)
            if state != stamp(path):
                raise ContractError('unstable-source: '+name)
            observed[path]=state
        if not active and prefix:
            entries[prefix[:-1]]=('d',b'')
        if before != stamp(directory):
            raise ContractError('unstable-source: '+prefix)
        observed[directory]=before
    try:
        walk(root)
        if any(stamp(p)!=state for p,state in observed.items()):
            raise ContractError('unstable-source: tree changed during capture')
    except OSError as error:
        raise ContractError('unreadable: '+str(error)) from error
    return entries


def _digest_entries(entries):
    """Shared framing for physical trees and portable listing vectors."""
    paths = set()
    for path in entries:
        _path_check(path)
        parts=path.split('/')
        paths.update('/'.join(parts[:i]) for i in range(1,len(parts)+1))
    folded = {}
    for path in paths:
        key=unicodedata.normalize('NFC',path.casefold())
        if key in folded and folded[key]!=path:
            raise ContractError('case-collision: '+path)
        folded[key]=path
    if 'COURSE.md' not in entries or entries['COURSE.md'][0]!='f':
        raise ContractError('not-a-course: regular COURSE.md required')
    digest=hashlib.sha256(b'agent-courses-identity-1\n')
    for path,(kind,payload) in sorted(entries.items(),key=lambda item:item[0].encode()):
        if kind=='f':
            try:
                payload.decode('utf-8')
                if b'\0' not in payload:
                    payload=payload.replace(b'\r\n',b'\n')
            except UnicodeError:
                pass
        elif kind=='l':
            try:
                payload.decode('utf-8')
            except UnicodeError as error:
                raise ContractError('invalid-link: '+path) from error
            if not payload or len(payload)>4096 or b'\0' in payload:
                raise ContractError('invalid-link: '+path)
        elif kind!='d':
            raise ContractError('special-file: '+path)
        encoded=path.encode()
        digest.update(kind.encode()+struct.pack('>Q',len(encoded))+encoded+struct.pack('>Q',len(payload))+payload)
    return 'sha256:'+digest.hexdigest()


def course_digest(root: Path) -> str:
    return _digest_entries(_capture(root))


@dataclass(frozen=True)
class RetainedCourse:
    """Caller-supplied interpretation context; this value does not authenticate provenance."""
    root: Path
    candidate: str


def _retained(identity, roots):
    """Validate metadata from the same captured bytes used for hashing."""
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',identity):
        raise ContractError('req-record-replay-data: malformed identity '+identity)
    if identity not in roots:
        raise ContractError('req-record-replay-data: missing retained source '+identity)
    retained = roots[identity]
    if not isinstance(retained, RetainedCourse):
        raise ContractError('req-record-replay-data: missing retained candidate provenance for ' + identity + '; supply the original installation candidate')
    if retained.candidate not in CANDIDATES:
        raise ContractError('req-record-replay-data: unsupported retained candidate provenance for ' + identity + '; supply the original installation candidate')
    root=Path(retained.root)
    candidate=retained.candidate
    try:
        if any(p.is_symlink() for p in [root,*root.parents]):
            raise ContractError('symlink archive component')
        entries=_capture(root)
        if _digest_entries(entries)!=identity:
            raise ContractError('retained identity mismatch')
        # A disposable tree lets the same authoring checker inspect immutable captured bytes.
        with tempfile.TemporaryDirectory(prefix='ac-contract-') as temporary:
            frozen=Path(temporary)/root.name
            frozen.mkdir()
            for name,(kind,payload) in entries.items():
                path=frozen/name
                path.parent.mkdir(parents=True,exist_ok=True)
                if kind=='f':
                    path.write_bytes(payload)
                elif kind=='l':
                    path.symlink_to(payload.decode())
                else:
                    path.mkdir(exist_ok=True)
            errors=[f for f in check_course(frozen, candidate=candidate) if f.severity=='error']
            if errors:
                if errors[0].rule == 'req-format-identifier':
                    raise ContractError('invalid rc.2 format identifier')
                if errors[0].rule == 'req-mixed-declarations':
                    raise ContractError('mixed declarations')
                raise ContractError('; '.join(f.rule+': '+f.message for f in errors))
            return course_metadata(frozen, candidate=candidate)
    except (OSError,ContractError,UnicodeError) as error:
        if str(error) in ('invalid rc.2 format identifier', 'mixed declarations'):
            raise ContractError('req-record-replay-data: ' + str(error) + ' for ' + identity) from error
        raise ContractError('req-record-replay-data: '+identity+': '+str(error)) from error


def _no_duplicate_json(pairs):
    value={}
    for key,item in pairs:
        if key in value:
            raise ContractError('duplicate JSON key')
        value[key]=item
    return value


def decode_events(raw: bytes):
    events,findings=[],[]
    lines=raw.split(b'\n')
    for index,line in enumerate(lines):
        if not line and index==len(lines)-1:
            continue
        try:
            if len(line)>4096:
                raise ContractError('line exceeds 4096 bytes')
            value=json.loads(line.decode('utf-8'),object_pairs_hook=_no_duplicate_json,
                             parse_constant=lambda value: (_ for _ in ()).throw(ContractError('non-JSON number')))
            faults=validate_frontmatter('event',value)
            if any(f.severity=='error' for f in faults):
                raise ContractError('; '.join(f.message for f in faults))
            events.append(value)
        except (ValueError,UnicodeError) as error:
            partial=index==len(lines)-1 and not raw.endswith(b'\n')
            findings.append(Finding('event-partial' if partial else 'req-record-event-line',str(index+1),str(error),'warning' if partial else 'error'))
    return events,findings


def _empty_record():
    return dict(spec='1.0',course=None,version=None,snapshot=None,generation=0,history=[],project=None,position=None,lessons={},calls=[],objectives=[],consent=[],declined=[])


def _project_option(project):
    return project['source'] if project['kind'] in ('git','local') else project['kind']


def replay(events: Sequence[Mapping], snapshot_roots: Mapping[str, RetainedCourse], *,
           receipt_status: Callable[[int, Mapping, int], str]) -> Mapping:
    """Internal deterministic oracle over complete protected synthetic history.

    Operation admission and filesystem durability require independent host proof.
    Refused lines emit diagnostics separately; required-source failures return no record.
    """
    record=_empty_record()
    occurrences=set()
    course=lessons=checks=rubric=None
    lessonkinds={'lesson-started','step-entered','call-put','call-decided','check-run','hint-given','explain-judged','lesson-completed','lesson-skipped'}
    known=lessonkinds|{'course-started','course-upgraded','project-chosen','consent-changed'}
    for index,event in enumerate(events):
        if any(f.severity=='error' for f in validate_frontmatter('event',event)):
            continue
        kind=event['kind']
        if kind not in known:
            continue
        repeated=False
        if kind=='call-decided' and event.get('provenance')=='verified':
            occurrence=event['receipt']['occurrence']
            repeated=occurrence in occurrences
            occurrences.add(occurrence)
        if kind=='course-started':
            if record['course'] is not None:
                continue
            course,lessons,checks,rubric=_retained(event['snapshot'],snapshot_roots)
            if event['course']!=course['name'] or event['version']!=course['version']:
                raise ContractError('req-record-replay-data: start metadata mismatch '+event['snapshot'])
            record.update(course=event['course'],version=event['version'],snapshot=event['snapshot'],generation=1)
            continue
        if record['course'] is None:
            continue
        if kind=='course-upgraded':
            if event['from']!=record['snapshot'] or event['to']==event['from']:
                continue
            target,newlessons,newchecks,newrubric=_retained(event['to'],snapshot_roots)
            options=target.get('project','own')
            options=options if isinstance(options,list) else [options]
            if target['name']!=record['course'] or target['version']!=event['version'] or record['project'] and _project_option(record['project']) not in options:
                raise ContractError('req-record-upgrade: incompatible committed target '+event['to'])
            record['history'].append(copy.deepcopy({k:record[k] for k in ['version','snapshot','generation','position','lessons','calls','objectives']}))
            record.update(version=event['version'],snapshot=event['to'],generation=record['generation']+1,position=None,lessons={},calls=[],objectives=[])
            course,lessons,checks,rubric=target,newlessons,newchecks,newrubric
            continue
        if kind in lessonkinds:
            if event['snapshot']!=record['snapshot'] or event['generation']!=record['generation']:
                continue
            lessonid=event['lesson']
            if lessonid not in lessons:
                continue
            lesson=lessons[lessonid]
            if kind=='lesson-started':
                entry=record['lessons'].setdefault(lessonid,{'status':'started'})
                if entry['status']!='passed':
                    entry['status']='started'
                    entry.pop('at',None)
                record['position']={'lesson':lessonid,'step':'goal'}
                continue
            if lessonid not in record['lessons']:
                continue
            entry=record['lessons'][lessonid]
            refs={v if isinstance(v,str) else v['id']: True if isinstance(v,str) else v.get('required',True) for v in lesson.get('checks',[])}
            callids={v['id'] for v in lesson.get('calls',[])}
            if kind in ('call-put','call-decided'):
                callid=event['call']
                if callid not in callids:
                    continue
                call=next((v for v in record['calls'] if v['lesson']==lessonid and v['id']==callid),None)
                if kind=='call-put':
                    if call is None:
                        record['calls'].append(dict(id=callid,lesson=lessonid,state='open'))
                    else:
                        call.clear()
                        call.update(id=callid,lesson=lessonid,state='open')
                    continue
                if call is None or call['state']!='open' or repeated:
                    continue
                status=None
                if event['by']=='learner':
                    status=receipt_status(index,event,record['generation'])
                    if status not in ('verified','unverified','rejected'):
                        raise ContractError('req-record-replay-interface: invalid receipt callback outcome')
                    if status=='rejected':
                        continue
                    if event['provenance']=='unverified':
                        status='unverified'
                call.update(state='decided',by=event['by'])
                if status:
                    call['provenance']=status
            elif kind=='step-entered':
                record['position']={'lesson':lessonid,'step':event['step']}
            elif kind=='check-run':
                checkid=event['check']
                if checkid not in refs:
                    continue
                expected='observed' if checks[checkid].get('kind','command')=='observe' else 'checked'
                if event['result'] in ('pass','fail') and event['evidence']!=expected:
                    continue
                value=entry.setdefault('checks',{}).setdefault(checkid,{'last':event['result'],'runs':0})
                value['last']=event['result']
                value['runs']+=int(event['result'] in ('pass','fail'))
            elif kind=='explain-judged':
                if lesson['stage']!='demonstrate' or event['of']!=rubric[1]:
                    continue
                entry['explain']={'met':event['met'],'of':event['of'],'passed':event['met']>=rubric[0]}
            elif kind=='lesson-skipped':
                if entry['status'] not in ('passed','skipped'):
                    entry.update(status='skipped',at=event['at'])
            elif kind=='lesson-completed':
                if entry['status']=='passed':
                    continue
                def passed(checkid):
                    return entry.get('checks',{}).get(checkid,{}).get('last')=='pass'
                if any(required and not passed(checkid) for checkid,required in refs.items()):
                    continue
                if lesson['stage']=='demonstrate' and not entry.get('explain',{}).get('passed'):
                    continue
                entry.update(status='passed',at=event['at'])
                ready=all(any(v['id']==callid and v['lesson']==lessonid and v['state']=='decided' and v.get('by')=='learner' and v.get('provenance')=='verified' for v in record['calls']) for callid in callids)
                if ready:
                    for objective in lesson.get('objectives',[]):
                        by=objective['by']
                        if by=='explain-back':
                            evidence='explained'
                            ok=entry.get('explain',{}).get('passed',False)
                        else:
                            evidence='observed' if checks[by].get('kind','command')=='observe' else 'checked'
                            ok=passed(by)
                        if ok:
                            record['objectives'].append(dict(id=objective['id'],lesson=lessonid,evidence=evidence,by=by,at=event['at'],snapshot=record['snapshot']))
        elif kind=='project-chosen':
            options=course.get('project','own')
            options=options if isinstance(options,list) else [options]
            if record['project'] is None and _project_option(event['project']) in options:
                record['project']=copy.deepcopy(event['project'])
        elif kind=='consent-changed':
            destination=event['destination']
            if event['state']=='declined':
                if event['lesson'] not in lessons:
                    continue
                value={k:event[k] for k in ('destination','hook','lesson')}
                if value not in record['declined']:
                    record['declined'].append(value)
            else:
                record['consent']=[v for v in record['consent'] if v['destination']!=destination]+[{'destination':destination,'state':event['state']}]
                record['consent'].sort(key=lambda v:v['destination'].encode())
    return record


def identity_vectors(root: Path):
    """Run fixed public vectors, distinguishing unavailable facilities from passes."""
    directory=root/'examples/identity-vectors'
    manifest=json.loads((directory/'manifest.json').read_text())
    outcomes=[]
    for vector in manifest['vectors']:
        status='passed'
        actual=None
        try:
            source=directory/manifest['roots'][vector['root']]['path']
            if 'listing' in vector['requires']:
                entries=_capture(source)
                for change in vector['changes']:
                    name=change['path']
                    op=change['op']
                    if op=='write':
                        entries[name]=('f',bytes.fromhex(change['bytes_hex']) if 'bytes_hex' in change else change['text'].encode())
                    elif op=='symlink':
                        entries[name]=('l',bytes.fromhex(change['target_hex']) if 'target_hex' in change else change['target'].encode())
                    elif op=='remove':
                        entries={p:v for p,v in entries.items() if p!=name and not p.startswith(name+'/')}
                    else:
                        raise ContractError('vector-operation: unsupported listing '+op)
                actual=_digest_entries(entries)
            else:
                with tempfile.TemporaryDirectory(prefix='ac-identity-') as temporary:
                    tree=Path(temporary)/'course'
                    shutil.copytree(source,tree,symlinks=True)
                    try:
                        for change in vector['changes']:
                            path=tree/change['path']
                            op=change['op']
                            _path_check(change['path'])
                            path.parent.mkdir(parents=True,exist_ok=True)
                            if op=='write':
                                path.write_bytes(bytes.fromhex(change['bytes_hex']) if 'bytes_hex' in change else change['text'].encode())
                            elif op=='mkdir':
                                path.mkdir(parents=True,exist_ok=True)
                            elif op=='symlink':
                                path.symlink_to(change['target'])
                            elif op=='remove':
                                if path.is_dir() and not path.is_symlink():
                                    shutil.rmtree(path)
                                else:
                                    path.unlink()
                            elif op=='fifo':
                                os.mkfifo(path)
                            elif op=='chmod':
                                path.chmod(int(change['mode'],8))
                            else:
                                raise ContractError('vector-operation: '+op)
                        if 'unprivileged-reads' in vector['requires']:
                            unreadable=next(tree/v['path'] for v in vector['changes'] if v['op']=='chmod')
                            try:
                                unreadable.read_bytes()
                            except PermissionError:
                                pass
                            else:
                                status='not-run'
                                actual='unprivileged reads unavailable'
                        if status!='not-run':
                            actual=course_digest(tree)
                    finally:
                        for change in vector['changes']:
                            if change['op']=='chmod' and (tree/change['path']).exists():
                                (tree/change['path']).chmod(0o600)
        except ContractError as error:
            actual=str(error).split(':',1)[0]
        except (OSError,NotImplementedError) as error:
            status='not-run'
            actual=str(error)
        expected=vector.get('expected_digest',vector.get('expected_error'))
        if status!='not-run' and actual!=expected:
            status='failed'
        outcomes.append(dict(case=vector['case'],rule=vector['rule'],status=status,expected=expected,actual=actual))
    return outcomes


def matches_expected(finding, expected):
    """Match a labelled schema location/keyword or a requirement-level finding."""
    if not isinstance(expected, dict):
        return False
    if finding.rule != expected.get('rule') or finding.path != expected.get('path'):
        return False
    if 'keyword' in expected:
        return finding.message.startswith('[' + expected['keyword'] + '] ')
    return finding.rule.startswith('req-')


def check_repository(root: Path):
    findings=[]
    try:
        context=schema_registry(root)
    except Exception as error:
        return [Finding('schema-registry',str(root/'schemas'),str(error),'error')]
    manifest_candidate=json.loads((root/'schemas/manifest.json').read_text())['candidate']
    contexts={manifest_candidate:context}
    cases_path=root/'fixtures/schema/cases.json'
    try:
        cases=json.loads(cases_path.read_text())
        for case in cases:
            candidate=case.get('candidate',manifest_candidate)
            if candidate not in contexts:
                contexts[candidate]=schema_registry(root,candidate)
            result=_validate(case['kind'],case['data'],contexts[candidate])
            errors=[f for f in result if f.severity=='error']
            if case['outcome']=='rejected':
                valid=any(matches_expected(f, case['finding']) for f in errors)
            else:
                valid=not errors and (case['outcome']!='warning' or any(f.rule=='req-unknown-keys' for f in result))
            if not valid:
                findings.append(Finding(case['requirement'],str(cases_path),case['case']+': expected '+case['outcome'],'error'))
    except (OSError,ValueError,KeyError) as error:
        findings.append(Finding('schema-cases',str(cases_path),str(error),'error'))
    for result in identity_vectors(root):
        if result['status']!='passed':
            findings.append(Finding(result['rule'],result['case'],str(result),'error' if result['status']=='failed' else 'warning'))
    inventory_path=root/'examples/manifest.json'
    if not inventory_path.is_file():
        findings.append(Finding('example-inventory',str(inventory_path),'reviewed example inventory is required','error'))
    else:
        try:
            inventory=json.loads(inventory_path.read_bytes())
            for entry in inventory['courses']:
                source=authored_path(root,entry['path'],rule='example-inventory')
                if course_digest(source) != entry['identity']:
                    findings.append(Finding('example-identity',str(source),'reviewed example identity mismatch','error'))
                else:
                    findings+=check_course(source,candidate=entry['candidate'])
        except (OSError,ValueError,KeyError) as error:
            findings.append(Finding('example-inventory',str(inventory_path),str(error),'error'))
    return findings


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--example',type=Path)
    parser.add_argument('--candidate', choices=CANDIDATES, default=None)
    args=parser.parse_args(argv)
    explicit = list(argv) if argv is not None else sys.argv[1:]
    if args.candidate is not None and any(value == '--root' or value.startswith('--root=') for value in explicit):
        parser.error('--candidate cannot override --root inventory provenance')
    if not args.root.is_dir():
        parser.error('--root must be an existing repository directory')
    if args.example is not None and not args.example.is_dir():
        parser.error('--example must be an existing course directory')
    try:
        findings=check_course(args.example, candidate=args.candidate or CURRENT) if args.example else check_repository(args.root)
    except (OSError,ValueError) as error:
        findings=[Finding('contract-input',str(args.example or args.root),str(error),'error')]
    for finding in findings:
        print(f'{finding.severity}: {finding.rule}: {finding.path}: {finding.message}')
    errors=sum(f.severity=='error' for f in findings)
    warnings=sum(f.severity=='warning' for f in findings)
    print(f'contracts: {errors} errors, {warnings} warnings')
    return 1 if errors else 0


if __name__=='__main__':
    raise SystemExit(main())
