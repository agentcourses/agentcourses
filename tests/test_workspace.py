from pathlib import Path
import importlib.util


def checker():
    spec = importlib.util.spec_from_file_location("check_docs", Path(__file__).parents[1] / "tools/check_docs.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_local_link(tmp_path):
    page = tmp_path / "site/src/content/docs/index.mdx"
    page.parent.mkdir(parents=True)
    page.write_text("---\ntitle: Foundation\n---\n[Broken](missing.md)\n")
    marker = tmp_path / "tools/document-stage.json"
    marker.parent.mkdir()
    marker.write_text('{"stage":"foundation"}')
    assert any(f["rule"] == "missing-link" for f in checker().check_tree(tmp_path, "foundation"))


import json
import subprocess
import sys
import pytest


def write(root, name, text):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def fixture(root, stage="foundation"):
    c = checker()
    for owner, names in c.GROUPS.items():
        if c.STAGES.index(owner) > c.STAGES.index(stage): continue
        for name in names:
            text = "# Source\n"
            if name.endswith(".mdx"): text = "---\ntitle: Test\n---\nTest page.\n"
            if name.endswith("manifest.json"): text = '{"vectors":[{"input":"sample.txt"}]}'
            write(root, name, text)
    write(root, "tools/document-stage.json", json.dumps({"stage": stage}))
    if c.STAGES.index(stage) >= c.STAGES.index("records"):
        write(root, "examples/identity-vectors/sample.txt", "sample")
    return c


def rules(c, root, floor="foundation"):
    return {f["rule"] for f in c.check_tree(root, floor)}


def test_document_stages(tmp_path):
    c = fixture(tmp_path)
    assert c.check_tree(tmp_path, "foundation") == []
    write(tmp_path, "docs/delivery/call-receipts.md", "# Experiment\n")
    assert c.check_tree(tmp_path, "foundation") == []
    c = fixture(tmp_path, "course")
    pending_register(tmp_path, "docs/delivery/contracts.md")
    assert c.check_tree(tmp_path, "foundation") == []
    c = fixture(tmp_path, "records")
    (tmp_path / "spec/identity.md").unlink()
    assert "required-file" in rules(c, tmp_path)
    c = fixture(tmp_path, "authors")
    for path in (tmp_path / "site/src/content/docs/authors").glob("*.mdx"): path.unlink()
    assert "required-file" in rules(c, tmp_path)


def test_missing_regressed_and_premature_stages(tmp_path):
    c = fixture(tmp_path)
    assert "stage-regression" in rules(c, tmp_path, "course")
    write(tmp_path, "spec/identity.md", "# Identity\n")
    assert "premature-activation" in rules(c, tmp_path)
    (tmp_path / "tools/document-stage.json").unlink()
    assert "missing-stage" in rules(c, tmp_path)
    write(tmp_path, "tools/document-stage.json", '{"stage":"typo"}')
    assert "invalid-stage" in rules(c, tmp_path)


@pytest.mark.parametrize("change", ["owner", "state", "question", "missing", "plain"])
def test_reject_pending_rows(tmp_path, change):
    c = fixture(tmp_path, "course")
    cells = ["identity", "records", "pending", "[Source](../../spec/format.md)", "Needs identity choice", "pending"]
    if change == "owner": cells[1] = "unknown"
    if change == "state": cells[2] = "probably"
    if change == "question": cells[0] = "course layout"
    if change == "missing": cells[4] = ""
    if change == "plain": cells[5] = "pending later"
    write(tmp_path, "docs/delivery/contracts.md", "| Question | Delivery owner | State | Source | Why waits | Normative |\n|---|---|---|---|---|---|\n|" + "|".join(cells) + "|\n")
    assert rules(c, tmp_path)


def test_records_reject_pending_and_missing_vectors(tmp_path):
    c = fixture(tmp_path, "records")
    write(tmp_path, "docs/delivery/contracts.md", "| Question | Delivery owner | State | Source | Why waits |\n|---|---|---|---|---|\n| identity | records | pending | source | waits |\n")
    (tmp_path / "examples/identity-vectors/sample.txt").unlink()
    assert {"pending-contract", "vector-input"} <= rules(c, tmp_path)


def test_spec_links(tmp_path):
    c = fixture(tmp_path, "course")
    write(tmp_path, "spec/format.md", '# Format\n\n<a id="course-folder"></a>\n\n## Course folder\n')
    index = tmp_path / "site/src/content/docs/index.mdx"
    start = index.read_text()
    for href in ("/specification/#format", "/specification/#format--course-folder", "../../../../spec/format.md#course-folder"):
        index.write_text(start + f"\n[Contract]({href})\n")
        assert c.check_tree(tmp_path, "foundation") == []
    for href, rule in (("/specification/#format--absent", "public-anchor"), ("/specification/#unknown", "public-anchor"), ("/runners/", "public-route"), ("../../../../spec/unknown.md", "missing-link"), ("../../../../docs/delivery/contracts.md", "private-register-link")):
        index.write_text(start + f"\n[Bad]({href})\n")
        assert rule in rules(c, tmp_path)
    index.write_text(start)
    mapping = c.site_map(tmp_path, "course", [])
    assert mapping["routes"] == ["/"]
    assert {"source": "spec/format.md", "anchor": "course-folder", "public": "/specification/#format--course-folder"} in mapping["anchors"]


def test_explicit_ids_and_frontmatter(tmp_path):
    c = fixture(tmp_path, "course")
    write(tmp_path, "spec/format.md", '# Format\n\n<a id="same"></a>\n<a id="same"></a>\n<a id="Bad_ID"></a>\n\n## Unanchored\n')
    write(tmp_path, "site/src/content/docs/index.mdx", "---\ntitle: [\n---\n")
    assert {"duplicate-anchor", "invalid-anchor", "missing-anchor", "frontmatter"} <= rules(c, tmp_path)


def test_baseline_from_nested_checkout(tmp_path, monkeypatch):
    c = fixture(tmp_path, "course")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test", "commit", "-qm", "Reviewed course"], check=True)
    nested = tmp_path / "nested"
    nested.mkdir()
    monkeypatch.setattr(c, "ROOT", nested)
    assert c.baseline_stage("HEAD") == "course"
    separate = tmp_path / "inspection"
    fixture(separate)
    assert c.main(["--root", str(separate), "--baseline-ref", "HEAD"]) == 1


def test_seed_exception_and_invalid_baseline():
    c = checker()
    assert c.baseline_stage("afe557fa0b7216b4981236179fc7996d7368b4a8") == "foundation"
    with pytest.raises(ValueError): c.baseline_stage("not-a-real-ref")


def test_site_map_is_source_only(tmp_path, capsys):
    c = fixture(tmp_path, "candidate")
    # Canonical export must not inspect composition or require generated guide pages.
    for group in ("authors", "runners", "candidate"):
        for name in c.GROUPS[group]: (tmp_path / name).unlink()
    write(tmp_path, "site/src/content/docs/index.mdx", "not frontmatter")
    assert c.main(["--root", str(tmp_path), "--site-map"]) == 0
    mapping = json.loads(capsys.readouterr().out)
    assert len(mapping["routes"]) == 9


def test_cli_missing_link_and_invalid_use(tmp_path):
    fixture(tmp_path)
    write(tmp_path, "README.md", "[Bad](absent.md)\n")
    tool = Path(__file__).parents[1] / "tools/check_docs.py"
    result = subprocess.run([sys.executable, str(tool), "--root", str(tmp_path)], capture_output=True, text=True)
    assert result.returncode == 1 and "missing-link" in result.stderr
    result = subprocess.run([sys.executable, str(tool), "--scope", "bad"], capture_output=True)
    assert result.returncode == 2


REGISTER_CELLS = {
    "docs/delivery/contracts.md": ("normative", "valid example", "invalid example", "reason", "owner review"),
    "spec/requirements.md": ("normative", "example"),
}


def pending_register(root, name, changes=None, omit=None):
    source = "../../spec/format.md" if name.startswith("docs/") else "format.md"
    row = {"question": "identity", "delivery owner": "records", "state": "pending", "source": f"[Source]({source})", "why waits": "Needs the records decision"}
    row.update({cell: "pending" for cell in REGISTER_CELLS[name]})
    row.update(changes or {})
    if omit: del row[omit]
    write(root, name, "| " + " | ".join(row) + " |\n|" + "|".join("---" for _ in row) + "|\n| " + " | ".join(row.values()) + " |\n")


@pytest.mark.parametrize("name,cell", [(name, cell) for name, cells in REGISTER_CELLS.items() for cell in cells])
@pytest.mark.parametrize("value", ["", "TBD", "claimed resolution", "Pending", None])
def test_pending_register_cells_require_literal_pending(tmp_path, name, cell, value):
    c = fixture(tmp_path, "course")
    if value is None: pending_register(tmp_path, name, omit=cell)
    else: pending_register(tmp_path, name, {cell: value})
    assert "pending-cell" in rules(c, tmp_path)


@pytest.mark.parametrize("name", REGISTER_CELLS)
def test_complete_literal_pending_register_passes(tmp_path, name):
    c = fixture(tmp_path, "course")
    pending_register(tmp_path, name)
    assert c.check_tree(tmp_path, "foundation") == []


def test_html_data_id_is_not_a_source_anchor(tmp_path):
    c = fixture(tmp_path, "course")
    write(tmp_path, "spec/format.md", '# Format\n\n<a data-id="fictional"></a>\n\n## Folder\n')
    findings = []
    mapping = c.site_map(tmp_path, "course", findings)
    assert not any(entry["anchor"] == "fictional" for entry in mapping["anchors"])
    assert any(item["rule"] == "missing-anchor" for item in findings)
    index = tmp_path / "site/src/content/docs/index.mdx"
    index.write_text(index.read_text() + "\n[False fragment](/specification/#format--fictional)\n")
    assert "public-anchor" in rules(c, tmp_path)


def test_adjacent_headings_each_require_their_own_anchor(tmp_path):
    c = fixture(tmp_path, "course")
    write(tmp_path, "spec/format.md", '# Format\n\n<a id="first"></a>\n## First\n## Second\n')
    assert "missing-anchor" in rules(c, tmp_path)
    write(tmp_path, "spec/format.md", '# Format\n\n<a id="first"></a>\n## First\n<a id="second"></a>\n## Second\n')
    assert c.check_tree(tmp_path, "foundation") == []


def test_real_html_ids_support_html_attribute_syntax(tmp_path):
    c = fixture(tmp_path, "course")
    write(tmp_path, "spec/format.md", '# Format\n\n<a ID = folder data-id="fictional" title=\'id="false"\'></a>\n\n## Folder\n\n## Inline <a id="inline"></a>\n')
    assert c.check_tree(tmp_path, "foundation") == []
    mapping = c.site_map(tmp_path, "course", [])
    assert {entry["anchor"] for entry in mapping["anchors"] if entry["source"] == "spec/format.md"} == {"", "folder", "inline"}


@pytest.mark.parametrize("form", ["inline", "block"])
@pytest.mark.parametrize("attribute", ["href", "src"])
@pytest.mark.parametrize("target,rule", [("/runnres/", "public-route"), ("../../../../spec/requirements.md", "private-register-link"), ("../../../../docs/delivery/contracts.md", "private-register-link")])
def test_html_links_use_the_same_target_rules(tmp_path, form, attribute, target, rule):
    c = fixture(tmp_path, "course")
    tag = "a" if attribute == "href" else "img"
    html = f'<{tag} {attribute} = "{target}">Target</{tag}>'
    if form == "inline": html = "Text " + html + "."
    else: html = "<div>\n" + html + "\n</div>"
    index = tmp_path / "site/src/content/docs/index.mdx"
    index.write_text(index.read_text() + "\n" + html + "\n")
    assert rule in rules(c, tmp_path)


@pytest.mark.parametrize("kind", ["fence", "span"])
def test_html_code_examples_do_not_export_source_anchors(tmp_path, kind):
    c = fixture(tmp_path, "course")
    html = '<a id="fictional"></a>'
    body = f'```html\n{html}\n```\n\n## Folder\n' if kind == "fence" else f'## Folder `{html}`\n'
    write(tmp_path, "spec/format.md", '# Format\n\n' + body)
    findings = []
    mapping = c.site_map(tmp_path, "course", findings)
    assert not any(entry["anchor"] == "fictional" for entry in mapping["anchors"])
    assert any(item["rule"] == "missing-anchor" for item in findings)


@pytest.mark.parametrize("kind", ["fence", "span"])
def test_html_code_examples_are_not_active_links(tmp_path, kind):
    c = fixture(tmp_path)
    html = '<a href="/runnres/">Route</a> <img src="../../../../spec/requirements.md">'
    example = f'```html\n{html}\n```' if kind == "fence" else f'`{html}`'
    index = tmp_path / "site/src/content/docs/index.mdx"
    index.write_text(index.read_text() + "\n" + example + "\n")
    assert c.check_tree(tmp_path, "foundation") == []
