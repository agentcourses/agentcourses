"""Example includes fail early in the source check and loudly in the site build.

The source check reports every invalid ExampleCode include as one finding. The build test
compiles the real component in a minimal Starlight project installed offline from the
pinned site lockfile. No course program is ever run.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("check_docs_for_includes", ROOT / "tools/check_docs.py")
check_docs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_docs)
DOCS = "site/src/content/docs/"
RULE = "example-source"
CASE = "case.mdx"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def page(title, body):
    return f"---\ntitle: {title}\n---\n\n{body}\n"


def tree(tmp_path, stage="foundation"):
    """A minimal checkable repository with two examples and links that escape them."""
    root = tmp_path / "repo"
    write(root / "tools/document-stage.json", json.dumps({"stage": stage}))
    write(root / DOCS / "index.mdx", page("Home", "Home."))
    demo = root / "examples/demo"
    write(demo / "a.txt", "alpha\n")
    write(demo / "nested/deep/b.py", "print(1)\n")
    write(demo / "empty.txt", "")
    write(demo / "blank.txt", " \n\t\n")
    write(root / "examples/other/b.txt", "beta\n")
    outside = tmp_path / "outside"
    write(outside / "a.txt", "outside\n")
    (demo / "inner.txt").symlink_to("a.txt")
    (demo / "leak.txt").symlink_to(outside / "a.txt")
    (root / "examples/linked").symlink_to(outside, target_is_directory=True)
    return root


def add_loops(root):
    """A file link and an example-directory link that each point at themselves."""
    (root / "examples/demo/loop.txt").symlink_to("loop.txt")
    (root / "examples/looped").symlink_to("looped", target_is_directory=True)


def tag(attributes):
    return f'<ExampleCode {attributes} lang="text" />'


def summary(findings, sources):
    """Reduce findings to (rule, path, source); a message naming no expected source stays whole."""
    return {(f["rule"], f["path"], next((s for s in sources if f["message"].startswith(s + ": ")), f["message"]))
            for f in findings}


INVALID = [
    ("missing-file", 'example="demo" file="absent.txt"', "demo", "absent.txt"),
    ("unknown-example", 'example="nowhere" file="a.txt"', "nowhere", "a.txt"),
    ("empty-file", 'example="demo" file="empty.txt"', "demo", "empty.txt"),
    ("blank-file", 'example="demo" file="blank.txt"', "demo", "blank.txt"),
    ("parent-traversal", 'example="demo" file="../other/b.txt"', "demo", "../other/b.txt"),
    ("absolute-path", 'example="demo" file="/etc/hosts"', "demo", "/etc/hosts"),
    ("dot-segment", 'example="demo" file="./a.txt"', "demo", "./a.txt"),
    ("backslash", 'example="demo" file="nested\\deep\\b.py"', "demo", "nested\\deep\\b.py"),
    ("unsafe-example", 'example="../demo" file="a.txt"', "../demo", "a.txt"),
    ("escaping-file-link", 'example="demo" file="leak.txt"', "demo", "leak.txt"),
    ("escaping-example-link", 'example="linked" file="a.txt"', "linked", "a.txt"),
    ("non-literal-file", 'example="demo" file={name}', "demo", "{name}"),
    ("non-literal-file-object", 'example="demo" file={{name: "a.txt"}}', "demo", '{{name: "a.txt"}}'),
    ("non-literal-file-call", 'example="demo" file={pick({path: "a.txt"}).path}', "demo", '{pick({path: "a.txt"}).path}'),
    ("non-literal-file-brace-string", 'example="demo" file={"}" + "a.txt"}', "demo", '{"}" + "a.txt"}'),
    ("non-literal-file-template", 'example="demo" file={`a.txt`}', "demo", "{`a.txt`}"),
    ("non-literal-file-comparison", 'example="demo" file={n > 1 ? "a.txt" : "b.txt"}', "demo", '{n > 1 ? "a.txt" : "b.txt"}'),
    ("non-literal-example-object", 'example={{id: "demo"}.id} file="a.txt"', '{{id: "demo"}.id}', "a.txt"),
    ("non-literal-example-template", 'example={`demo`} file="a.txt"', "{`demo`}", "a.txt"),
    ("spread-properties", '{...{example: "demo", file: "a.txt"}}', "", ""),
    ("file-link-loop", 'example="demo" file="loop.txt"', "demo", "loop.txt"),
    ("example-link-loop", 'example="looped" file="a.txt"', "looped", "a.txt"),
]


@pytest.mark.parametrize(("attributes", "example", "file"), [case[1:] for case in INVALID],
                         ids=[case[0] for case in INVALID])
def test_invalid_include_is_reported(tmp_path, attributes, example, file):
    root = tree(tmp_path)
    add_loops(root)
    write(root / DOCS / CASE, page("Case", tag(attributes)))
    source = f"{example}/{file}"
    actual = summary(check_docs.check_tree(root, "foundation"), {source})
    expected = {(RULE, DOCS + CASE, source)}
    assert actual == expected, (
        f"include findings differ: unexpected={sorted(actual - expected)} absent={sorted(expected - actual)}")


VALID = "\n\n".join([
    "import ExampleCode from '../../components/ExampleCode.astro';",
    '<ExampleCode example="demo" file="a.txt" lang="text" />',
    "<ExampleCode example='demo' file='nested/deep/b.py' lang='python' />",
    '<ExampleCode\n  example="demo"\n  file="inner.txt"\n  lang="text"\n/>',
    '<ExampleCode example="other" file="b.txt" lang="text"></ExampleCode>',
    '1. Indented in a list:\n\n   <ExampleCode example="demo" file="a.txt" lang="text" />',
    '```mdx\n<ExampleCode example="nowhere" file="x.txt" lang="text" />\n```',
    '~~~~\n<ExampleCode example="demo" file="absent.txt" lang="text" />\n~~~~',
    'Write `<ExampleCode example="nowhere" file="y.txt" lang="text" />` to show a file.',
    '<ExampleCode example="demo" file="a.txt" lang={"text"} />',
    '```jsx\n<ExampleCode example="demo" file={{name: "absent.txt"}} lang="text" />\n```',
    'Inline: `` <ExampleCode example={`nowhere`} file="z.txt" lang="text" /> `` stays prose.',
])


def test_valid_and_illustrative_includes_have_no_findings(tmp_path):
    root = tree(tmp_path)
    add_loops(root)
    write(root / DOCS / "valid.mdx", page("Valid", VALID))
    assert check_docs.check_tree(root, "foundation") == []
    write(root / DOCS / CASE, page("Case", tag('example="demo" file="absent.txt"')))
    assert check_docs.check_tree(root, "foundation", source_only=True) == []


def test_bad_includes_do_not_hide_other_findings(tmp_path):
    root = tree(tmp_path)
    add_loops(root)
    write(root / DOCS / CASE, page("Case", tag('example="demo" file="loop.txt"')))
    write(root / DOCS / "later.mdx", page("Later", tag('example="demo" file="absent.txt"')))
    write(root / DOCS / "other.mdx", page("Other", tag('example="demo" file="a.txt"') + "\n\nSee [gone](missing.md)."))
    loop, absent = "demo/loop.txt", "demo/absent.txt"
    actual = summary(check_docs.check_tree(root, "foundation"), {loop, absent})
    expected = {(RULE, DOCS + CASE, loop), (RULE, DOCS + "later.mdx", absent),
                ("missing-link", DOCS + "other.mdx", "Missing or unsafe local target: missing.md")}
    assert actual == expected, (
        f"include findings differ: unexpected={sorted(actual - expected)} absent={sorted(expected - actual)}")


def test_authors_scope_rejects_broken_include(tmp_path):
    root = tree(tmp_path, stage="authors")
    for name in ("format", "execution", "consent", "requirements", "records", "identity"):
        write(root / f"spec/{name}.md", f"# {name.title()}\n")
    write(root / "docs/delivery/call-receipts.md", "# Receipts\n")
    write(root / "examples/identity-vectors/manifest.json", "{}")
    for name in ("quickstart", "best-practices", "explain-back"):
        write(root / DOCS / f"authors/{name}.mdx", page(name, tag('example="demo" file="a.txt"')))
    write(root / DOCS / "authors/checks.mdx", page("Checks", tag('example="demo" file="absent.txt"')))
    result = subprocess.run([sys.executable, str(ROOT / "tools/check_docs.py"), "--root", str(root), "--scope", "authors"],
                            capture_output=True, text=True, timeout=60)
    found = set()
    for line in result.stderr.splitlines():
        path, rule, message = line.split(": ", 2)
        found.add((rule, path, message.split(": ", 1)[0]))
    expected = {(RULE, DOCS + "authors/checks.mdx", "demo/absent.txt")}
    assert result.returncode == 1 and found == expected, (
        f"authors-scope run exited {result.returncode} with findings {sorted(found)}")


@pytest.fixture(scope="module")
def site_project(tmp_path_factory):
    """A minimal Starlight project with the pinned site lockfile and the real component."""
    pnpm = shutil.which("pnpm")
    assert pnpm, "pnpm from the pinned site toolchain must be on PATH"
    project = tmp_path_factory.mktemp("include-site")
    for name in ("package.json", "pnpm-lock.yaml"):
        shutil.copyfile(ROOT / "site" / name, project / name)
    installed = subprocess.run([pnpm, "install", "--offline", "--frozen-lockfile"], cwd=project,
                               capture_output=True, text=True, timeout=300)
    assert installed.returncode == 0, installed.stdout + installed.stderr
    component = project / "src/components/ExampleCode.astro"
    component.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "site/src/components/ExampleCode.astro", component)
    assert component.read_bytes() == (ROOT / "site/src/components/ExampleCode.astro").read_bytes()
    examples = project / "examples"
    write(examples / "demo/a.py", "print('included')\n")
    write(examples / "demo/empty.txt", "")
    write(examples / "demo/blank.txt", " \n\t\n")
    write(project / "astro.config.mjs", "\n".join([
        "import { defineConfig } from 'astro/config';",
        "import starlight from '@astrojs/starlight';",
        "export default defineConfig({",
        f"  vite: {{ define: {{ 'import.meta.env.AC_EXAMPLES_ROOT': JSON.stringify({json.dumps(str(examples) + os.sep)}) }} }},",
        "  integrations: [starlight({ title: 'Include fixture' })],",
        "});",
    ]))
    write(project / "src/content.config.ts", "\n".join([
        "import { defineCollection } from 'astro:content';",
        "import { docsLoader } from '@astrojs/starlight/loaders';",
        "import { docsSchema } from '@astrojs/starlight/schema';",
        "export const collections = { docs: defineCollection({ loader: docsLoader(), schema: docsSchema() }) };",
    ]))
    return pnpm, project


def build(site_project, file):
    pnpm, project = site_project
    write(project / "src/content/docs/index.mdx", page("Fixture", "\n\n".join([
        "import ExampleCode from '../../components/ExampleCode.astro';",
        f'<ExampleCode example="demo" file="{file}" lang="text" />',
    ])))
    result = subprocess.run([pnpm, "exec", "astro", "build"], cwd=project, capture_output=True, text=True,
                            timeout=300, env={**os.environ, "ASTRO_TELEMETRY_DISABLED": "1"})
    return result, result.stdout + result.stderr


@pytest.mark.parametrize("file", ["empty.txt", "blank.txt"], ids=["empty", "blank"])
def test_component_rejects_empty_source(site_project, file):
    result, output = build(site_project, file)
    source = f"demo/{file}"
    words = " ".join(output.split())
    detail = words[words.find("[ERROR]"):][:400] if "[ERROR]" in words else words[-400:]
    assert result.returncode != 0 and f"ExampleCode: empty source: {source}" in output, (
        f"build of {source} exited {result.returncode} without the empty-source diagnostic; first error: {detail}")


def test_component_builds_valid_and_reports_missing(site_project):
    result, output = build(site_project, "a.py")
    assert result.returncode == 0, output
    assert "included" in (site_project[1] / "dist/index.html").read_text()
    result, output = build(site_project, "absent.py")
    assert result.returncode != 0 and "ExampleCode: missing or unsafe source: demo/absent.py" in output, output


PROSE_CONTEXTS = [
    ('escaped-backtick', 'Escaped tick: \\` is punctuation.\n\n', '\n\nLater `code`.'),
    ('paragraph-boundary', 'An unmatched ` tick.\n\n', '\n\nLater `code`.'),
]


@pytest.mark.parametrize(('prefix', 'suffix'), [case[1:] for case in PROSE_CONTEXTS],
                         ids=[case[0] for case in PROSE_CONTEXTS])
@pytest.mark.parametrize(('attributes', 'example', 'file'), [case[1:] for case in INVALID],
                         ids=[case[0] for case in INVALID])
def test_invalid_include_in_prose_context(tmp_path, attributes, example, file, prefix, suffix):
    root = tree(tmp_path)
    add_loops(root)
    write(root / DOCS / CASE, page('Case', prefix + tag(attributes) + suffix))
    source = f'{example}/{file}'
    actual = summary(check_docs.check_tree(root, 'foundation'), {source})
    expected = {(RULE, DOCS + CASE, source)}
    assert actual == expected, (
        f'include findings differ: unexpected={sorted(actual - expected)} absent={sorted(expected - actual)}')


ILLUSTRATION_TAG = '<ExampleCode example="nowhere" file="absent.txt" lang="text" />'
MDX_VALID = [
    ('comment', '{/* ' + ILLUSTRATION_TAG + ' */}'),
    ('string-expression', "{'" + ILLUSTRATION_TAG + "'}"),
    ('template-expression', '{`' + ILLUSTRATION_TAG + '`}'),
    ('escaped-tag', '\\' + ILLUSTRATION_TAG),
    ('entity-file', '<ExampleCode example="demo" file="nested&#x2f;deep/b.py" />'),
    ('entity-example', '<ExampleCode example="d&#101;mo" file="a.txt" />'),
    ('named-entity-file', '<ExampleCode example="demo" file="a&period;txt" />'),
    ('earlier-spread', '<ExampleCode {...props} example="demo" file="a.txt" />'),
    ('intervening-spread-overridden', '<ExampleCode example="nowhere" {...props} file="a.txt" example="demo" />'),
    ('later-file-literal', '<ExampleCode example="demo" file={name} file="a.txt" />'),
    ('later-example-literal', '<ExampleCode example={name} file="a.txt" example="demo" />'),
    ('throwing-expression', '{(() => { throw new Error("must not run"); })()}'),
]


@pytest.mark.parametrize('body', [case[1] for case in MDX_VALID], ids=[case[0] for case in MDX_VALID])
def test_mdx_literal_or_illustration_is_accepted(tmp_path, body):
    root = tree(tmp_path)
    write(root / DOCS / CASE, page('Case', body))
    assert check_docs.check_tree(root, 'foundation') == [], 'unexpected MDX include findings'


EFFECTIVE_INVALID = [
    ('later-spread', 'example="demo" file="a.txt" {...props}', '/'),
    ('intervening-spread', 'example="demo" {...props} file="a.txt"', '/a.txt'),
    ('only-example-restored', 'example="demo" file="a.txt" {...props} example="demo"', 'demo/'),
    ('later-file-expression', 'example="demo" file="a.txt" file={name}', 'demo/{name}'),
    ('later-example-expression', 'example="demo" file="a.txt" example={name}', '{name}/a.txt'),
]


@pytest.mark.parametrize(('attributes', 'source'), [case[1:] for case in EFFECTIVE_INVALID],
                         ids=[case[0] for case in EFFECTIVE_INVALID])
def test_effective_source_is_not_literal(tmp_path, attributes, source):
    root = tree(tmp_path)
    write(root / DOCS / CASE, page('Case', tag(attributes)))
    actual = summary(check_docs.check_tree(root, 'foundation'), {source})
    expected = {(RULE, DOCS + CASE, source)}
    assert actual == expected, f'effective source findings differ: {sorted(actual)}'


def test_mdx_parse_error_does_not_hide_other_documents(tmp_path):
    root = tree(tmp_path)
    write(root / DOCS / CASE, page('Case', '<ExampleCode example="demo" file={ />'))
    write(root / DOCS / 'later.mdx', page('Later', tag('example="demo" file="absent.txt"')))
    actual = summary(check_docs.check_tree(root, 'foundation'), {'/', 'demo/absent.txt'})
    assert actual == {(RULE, DOCS + CASE, '/'), (RULE, DOCS + 'later.mdx', 'demo/absent.txt')}
