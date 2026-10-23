"""Resource preparation has explicit selection and refuses before any collision write."""
import pytest
from tools import check_contracts as c
from test_candidates import prepare, edit, invoke, exact, FILES


def test_project_and_lesson_sources(course):
    root=prepare(course)
    edit(root,project='starter')
    exact(root,set(),case='project-and-lesson-sources')
    assert c.starter_sources(root)==FILES
    assert c.starter_sources(root,lesson_id='make')=={'plan/README.md':FILES['plan/README.md']}
    assert c.starter_sources(root,lesson_id='intro')=={}


def test_selection_is_explicit(course):
    root=prepare(course,provenance=True)
    resolver=getattr(c,'resolve_project',None)
    assert callable(resolver), 'selection-is-explicit: absent resolver'
    for choice in [None,'unknown']:
        with pytest.raises(c.ContractError,match='^req-project-selection:'):resolver(root,choice)
    assert resolver(root,'own') is None
    assert resolver(root,'starter')==(root/'assets/starter').resolve()


def test_collision_keeps_all_bytes(tmp_path):
    copier=getattr(c,'copy_starter',None)
    assert callable(copier), 'collision-keeps-all-bytes: absent copy helper'
    destination=tmp_path/'work'
    destination.mkdir()
    (destination/'keep.txt').write_bytes(b'original\n')
    before={p.relative_to(destination).as_posix():p.read_bytes() for p in destination.rglob('*') if p.is_file()}
    with pytest.raises(c.ContractError,match='^req-starter-copy:'):
        copier({'a-new.txt':b'new','keep.txt':b'replacement'},destination)
    assert {p.relative_to(destination).as_posix():p.read_bytes() for p in destination.rglob('*') if p.is_file()}==before
    copier({'new.txt':b'new'},destination)
    assert (destination/'new.txt').read_bytes()==b'new'


@pytest.mark.parametrize('entry',['../escape','/absolute','C:/drive','a/../../escape'])
def test_copy_refuses_unsafe_paths_before_writing(tmp_path,entry):
    copier=getattr(c,'copy_starter',None)
    assert callable(copier),'unsafe-copy: absent copy helper'
    destination=tmp_path/'work';destination.mkdir()
    with pytest.raises(c.ContractError,match='^req-starter-copy:'):
        copier({'first.txt':b'first',entry:b'unsafe'},destination)
    assert list(destination.iterdir())==[]


def test_starter_follows_contained_directory_link(course):
    root=prepare(course)
    source=root/'assets/starter'
    (source/'linked').symlink_to('plan',target_is_directory=True)
    loader=getattr(c,'starter_sources',None)
    assert callable(loader),'contained-starter-link: absent loader'
    assert loader(root)==dict(FILES,**{'linked/README.md':FILES['plan/README.md']})


@pytest.mark.parametrize('selection',['./tutor','starter'])
def test_tutor_material_is_not_learner_source(course,selection):
    import shutil
    root=prepare(course)
    if selection=='starter':
        shutil.rmtree(root/'assets/starter')
        (root/'assets/starter').symlink_to('../tutor',target_is_directory=True)
        lesson=root/'lessons/make.md'
        lesson.write_text(lesson.read_text().replace('plan/README.md','finish.rubric.md'))
        edit(root,project='own')
        expected={('req-resource-roles','error','lessons/make.md')}
    else:
        edit(root,project=selection)
        expected={('req-resource-roles','error','COURSE.md')}
    exact(root,expected,case='tutor-resource-boundary')
    edit(root,project=selection)
    with pytest.raises(c.ContractError,match='^req-resource-roles:'):
        c.resolve_project(root,selection)
    if selection=='starter':
        for lesson_id in [None,'make']:
            with pytest.raises(c.ContractError,match='^req-resource-roles:'):
                c.starter_sources(root,lesson_id=lesson_id)


def copy_inventory(root):
    """Include directories and links as well as every file's bytes."""
    import os
    return {path.relative_to(root).as_posix():
            ('link', os.readlink(path)) if path.is_symlink() else
            ('directory', None) if path.is_dir() else ('file', path.read_bytes())
            for path in root.rglob('*')}


def filesystem_aliases(root):
    probe = root / 'CaseProbe'
    probe.mkdir()
    try:
        return (root / 'caseprobe').exists()
    finally:
        probe.rmdir()


TARGET_ALIASES = [
    ('Name.txt', 'name.txt'),
    ('nested/Name.txt', 'nested/name.txt'),
    ('Folder/item.txt', 'folder/item.txt'),
    ('Name', 'name/child.txt'),
    ('nested/Name', 'nested/name/child.txt'),
]


@pytest.mark.parametrize('names', TARGET_ALIASES, ids=['files', 'nested-files', 'parent-alias', 'ancestor', 'nested-ancestor'])
@pytest.mark.parametrize('reverse', [False, True], ids=['forward', 'reverse'])
@pytest.mark.parametrize('existing_destination', [False, True], ids=['new-destination', 'existing-destination'])
def test_copy_target_aliases(tmp_path, names, reverse, existing_destination):
    aliases = filesystem_aliases(tmp_path)
    destination = tmp_path / 'work'
    if existing_destination:
        destination.mkdir()
        (destination / 'keep.txt').write_bytes(b'unchanged')
    entries = list(reversed(names)) if reverse else list(names)
    files = {'first-safe.txt': b'safe', **{name: name.encode() for name in entries}}
    before = copy_inventory(tmp_path)
    if aliases:
        with pytest.raises(c.ContractError, match='^req-starter-copy:'):
            c.copy_starter(files, destination)
        assert copy_inventory(tmp_path) == before
    else:
        c.copy_starter(files, destination)
        assert all((destination / name).read_bytes() == payload for name, payload in files.items())
        assert all(copy_inventory(tmp_path)[name] == entry for name, entry in before.items())


@pytest.mark.parametrize('existing, requested, directory', [
    ('Name', 'name', False),
    ('Name', 'name/child.txt', False),
    ('Name', 'name', True),
    ('nested/Name', 'nested/name', False),
    ('Folder/Name', 'folder/name', False),
], ids=['file', 'file-as-parent', 'directory', 'nested-file', 'nested-parent-alias'])
def test_copy_existing_aliases(tmp_path, existing, requested, directory):
    aliases = filesystem_aliases(tmp_path)
    destination = tmp_path / 'work'
    path = destination / existing
    path.parent.mkdir(parents=True)
    path.mkdir() if directory else path.write_bytes(b'unchanged')
    files = {'first-safe.txt': b'safe', requested: b'new'}
    before = copy_inventory(tmp_path)
    if aliases:
        with pytest.raises(c.ContractError, match='^req-starter-copy:'):
            c.copy_starter(files, destination)
        assert copy_inventory(tmp_path) == before
    else:
        c.copy_starter(files, destination)
        assert all((destination / name).read_bytes() == payload for name, payload in files.items())
        assert all(copy_inventory(tmp_path)[name] == entry for name, entry in before.items())


def test_copy_aliases_under_existing_directory(tmp_path):
    aliases = filesystem_aliases(tmp_path)
    destination = tmp_path / 'work'
    (destination / 'Folder').mkdir(parents=True)
    (destination / 'Folder/keep.txt').write_bytes(b'unchanged')
    files = {'first-safe.txt': b'safe', 'Folder/Name': b'one', 'folder/name': b'two'}
    before = copy_inventory(tmp_path)
    if aliases:
        with pytest.raises(c.ContractError, match='^req-starter-copy:'):
            c.copy_starter(files, destination)
        assert copy_inventory(tmp_path) == before
    else:
        c.copy_starter(files, destination)
        assert all((destination / name).read_bytes() == payload for name, payload in files.items())


def test_copy_distinct_files_through_parent_aliases(tmp_path):
    destination = tmp_path / 'work'
    files = {'Folder/first.txt': b'one', 'folder/second.txt': b'two'}
    c.copy_starter(files, destination)
    assert all((destination / name).read_bytes() == payload for name, payload in files.items())
    assert sum(path.is_file() for path in destination.rglob('*')) == 2
