"""Internal source checks and canonical public-link map. No build or writes are needed."""
import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt
import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("foundation", "course", "records", "authors", "runners", "candidate")
DOCS = "site/src/content/docs/"
GROUPS = {
    "foundation": ["tools/document-stage.json", DOCS + "index.mdx"],
    "course": [f"spec/{s}.md" for s in ("format", "execution", "consent", "requirements")],
    "records": ["spec/records.md", "spec/identity.md", "docs/delivery/call-receipts.md", "examples/identity-vectors/manifest.json"],
    "authors": [DOCS + f"authors/{s}.mdx" for s in ("quickstart", "best-practices", "checks", "explain-back")],
    "runners": [DOCS + f"{s}.mdx" for s in ("runners", "implementers/support", "implementers/conformance")],
    "candidate": [DOCS + "specification.mdx"],
}
STEMS = {"format": "course", "execution": "course", "consent": "course", "records": "records", "identity": "records"}
PENDING = {"receipts", "call events", "replay/recovery", "settlement", "followed-field", "identity", "schema addresses", "naming", "freeze qualification"}
OWNERS = {"course", "records", "schemas"}
PARSER = MarkdownIt("commonmark", {"html": True}).enable("table")
class HTMLAttributes(HTMLParser):
    def __init__(self):
        super().__init__()
        self.attributes = []

    def handle_starttag(self, tag, attrs):
        self.attributes.extend((name, value) for name, value in attrs if value is not None)


def html_attributes(fragment):
    parser = HTMLAttributes()
    parser.feed(fragment)
    return parser.attributes

def finding(rule, path, message):
    return {"rule": rule, "path": str(path), "message": message}


def marker(root):
    try:
        data = json.loads((root / "tools/document-stage.json").read_text())
    except FileNotFoundError:
        return None, [finding("missing-stage", "tools/document-stage.json", "Explicit stage marker required")]
    except (ValueError, OSError) as exc:
        return None, [finding("invalid-stage", "tools/document-stage.json", str(exc))]
    if not isinstance(data, dict) or set(data) != {"stage"} or data["stage"] not in STAGES:
        return None, [finding("invalid-stage", "tools/document-stage.json", "Expected exactly one recognised stage")]
    return data["stage"], []


def document_paths(root):
    paths = [root / p for p in ("README.md", "AGENTS.md", "REVIEW.md", "CLAUDE.md") if (root / p).is_file()]
    for directory in ("spec", "docs", "examples", DOCS):
        base = root / directory
        if base.exists():
            paths.extend(p for p in base.rglob("*") if p.suffix in (".md", ".mdx") and p.is_file())
    return sorted(set(paths))


def body_text(path, findings, root):
    text = path.read_text()
    if path.suffix == ".mdx" or text.startswith("---\n"):
        try:
            parts = text.split("---", 2)
            if not text.startswith("---\n") or len(parts) != 3:
                raise ValueError("Expected delimited YAML frontmatter")
            meta = yaml.safe_load(parts[1])
            if not isinstance(meta, dict) or not isinstance(meta.get("title"), str) or not meta["title"].strip():
                raise ValueError("Frontmatter needs a nonempty title")
            text = parts[2]
        except (yaml.YAMLError, ValueError) as exc:
            findings.append(finding("frontmatter", path.relative_to(root), str(exc)))
    return text


def tokens_and_ids(text):
    tokens = PARSER.parse(text)
    ids = []
    for t in tokens:
        if t.type == "html_block":
            ids.extend(value for name, value in html_attributes(t.content) if name == "id")
        for child in t.children or []:
            if child.type == "html_inline":
                ids.extend(value for name, value in html_attributes(child.content) if name == "id")
    return tokens, ids


def site_map(root, stage, findings):
    routes = ["/"]
    for owner in ("authors", "runners", "candidate"):
        if STAGES.index(stage) >= STAGES.index(owner):
            routes.extend("/" + p[len(DOCS):-4] + "/" for p in GROUPS[owner])
    anchors = []
    for stem, owner in STEMS.items():
        if STAGES.index(stage) < STAGES.index(owner):
            continue
        source = f"spec/{stem}.md"
        path = root / source
        if not path.is_file():
            continue
        text = body_text(path, findings, root)
        tokens, ids = tokens_and_ids(text)
        for ident in ids:
            if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", ident):
                findings.append(finding("invalid-anchor", source, f"Invalid explicit ID: {ident}"))
        if len(ids) != len(set(ids)):
            findings.append(finding("duplicate-anchor", source, "Explicit IDs must be unique within a source"))
        for i, token in enumerate(tokens):
            if token.type == "heading_open" and token.tag != "h1":
                line = token.map[0]
                candidates = []
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    for child in tokens[i + 1].children or []:
                        if child.type == "html_inline":
                            candidates.extend(value for name, value in html_attributes(child.content) if name == "id")
                previous = tokens[i - 1] if i else None
                preceding = []
                if previous and previous.type == "html_block" and previous.map and line - previous.map[1] <= 1:
                    preceding = [previous.content]
                elif previous and previous.type == "paragraph_close" and i >= 2:
                    inline = tokens[i - 2]
                    if inline.type == "inline" and inline.map and line - inline.map[1] <= 1:
                        children = inline.children or []
                        if all(child.type in ("html_inline", "softbreak", "hardbreak") or (child.type == "text" and not child.content.strip()) for child in children):
                            preceding = [child.content for child in children if child.type == "html_inline"]
                if not candidates:
                    preceding_ids = [value for fragment in preceding for name, value in html_attributes(fragment) if name == "id"]
                    candidates = preceding_ids[-1:]
                if not any(re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", ident) for ident in candidates):
                    findings.append(finding("missing-anchor", source, f"Heading at line {line+1} needs an explicit ID"))
        anchors.append({"source": source, "anchor": "", "public": f"/specification/#{stem}"})
        anchors.extend({"source": source, "anchor": ident, "public": f"/specification/#{stem}--{ident}"} for ident in ids)
    return {"stage": stage, "routes": routes, "anchors": anchors}


def table_rows(text):
    """Return Markdown table records keyed by their visible column titles."""
    rows, headers, cells, in_head = [], [], [], False
    for token in PARSER.parse(text):
        if token.type == "thead_open": in_head = True
        elif token.type == "thead_close": in_head = False
        elif token.type == "tr_open": cells = []
        elif token.type == "inline": cells.append(token.content.strip())
        elif token.type == "tr_close":
            if in_head: headers = [h.lower().replace("_", " ") for h in cells]
            else: rows.append(dict(zip(headers, cells)))
    return rows


def check_registers(root, stage, findings):
    if STAGES.index(stage) < STAGES.index("course"):
        return
    name = "spec/requirements.md"
    path = root / name
    if not path.is_file(): return
    for row in table_rows(path.read_text()):
        if "state" not in row:
            findings.append(finding("register-state", name, "Register rows require state and delivery owner"))
            continue
        owner = row.get("delivery owner", "").lower()
        state = row["state"].lower()
        if owner not in OWNERS or state not in ("resolved", "pending"):
            findings.append(finding("register-owner-state", name, "Unknown delivery owner or state"))
        if state == "pending":
            question = row.get("question", "").lower()
            if stage != "course" or owner != "records" or question not in PENDING or not row.get("source") or not row.get("why waits"):
                findings.append(finding("pending-contract", name, "Pending rows need a permitted records question, source and why waits; only course permits them"))
            needed = ("normative", "example")
            if any(row.get(key) != "pending" for key in needed):
                findings.append(finding("pending-cell", name, "Every unresolved register cell must contain literal pending"))
        elif state == "resolved":
            needed = ("normative", "example")
            if any(not row.get(key) or row[key].lower() == "pending" for key in needed):
                findings.append(finding("unresolved-register", name, "Resolved requirement lacks normative and example targets"))
            for key in needed:
                if not re.search(r"\[[^]]+\]\([^)]+\)", row.get(key, "")):
                    findings.append(finding("register-target", name, f"{key} requires a source link"))


def check_tree(root: Path, minimum_stage: str, *, source_only=False) -> list[dict[str, str]]:
    root = root.resolve()
    if minimum_stage not in STAGES:
        raise ValueError("Unknown minimum stage")
    declared, findings = marker(root)
    stage = max((declared or "foundation", minimum_stage), key=STAGES.index)
    if declared and STAGES.index(declared) < STAGES.index(minimum_stage):
        findings.append(finding("stage-regression", "tools/document-stage.json", f"Stage cannot fall below {minimum_stage}"))
    for owner, files in GROUPS.items():
        for name in files:
            if source_only and name not in {"tools/document-stage.json"} | {f"spec/{stem}.md" for stem in STEMS}:
                continue
            exists = (root / name).is_file()
            if STAGES.index(owner) <= STAGES.index(stage) and not exists:
                findings.append(finding("required-file", name, f"Required at {stage}"))
            elif STAGES.index(owner) > STAGES.index(stage) and exists and name != "docs/delivery/call-receipts.md":
                findings.append(finding("premature-activation", name, f"First allowed at {owner}"))
    manifest = root / "examples/identity-vectors/manifest.json"
    if not source_only and manifest.is_file() and STAGES.index(stage) >= STAGES.index("records"):
        try:
            data = json.loads(manifest.read_text())
            def inputs(value):
                if isinstance(value, dict):
                    for key, item in value.items():
                        if key in ("input", "input_path") and isinstance(item, str): yield item
                        else: yield from inputs(item)
                elif isinstance(value, list):
                    for item in value: yield from inputs(item)
            for item in inputs(data):
                target = (manifest.parent / item).resolve()
                if not target.is_relative_to(root) or not target.is_file():
                    findings.append(finding("vector-input", manifest.relative_to(root), f"Missing or unsafe vector input: {item}"))
        except (ValueError, OSError) as exc:
            findings.append(finding("vector-manifest", manifest.relative_to(root), str(exc)))
    mapping = site_map(root, stage, findings)
    public = {entry["public"] for entry in mapping["anchors"]}
    sources = {(entry["source"], entry["anchor"]) for entry in mapping["anchors"]}
    for path in document_paths(root):
        if source_only and path.relative_to(root).as_posix() not in {f"spec/{stem}.md" for stem in STEMS}:
            continue
        rel = path.relative_to(root)
        text = body_text(path, findings, root)
        tokens, _ = tokens_and_ids(text)
        links = []
        for token in tokens:
            for child in token.children or []:
                if child.type in ("link_open", "image"):
                    links.append(child.attrGet("href") or child.attrGet("src"))
                elif child.type == "html_inline":
                    links.extend(value for name, value in html_attributes(child.content) if name in ("href", "src"))
            if token.type == "html_block":
                links.extend(value for name, value in html_attributes(token.content) if name in ("href", "src"))
        for href in links:
            url = urlsplit(href)
            if url.scheme or url.netloc: continue
            address, fragment = unquote(url.path), unquote(url.fragment)
            if address.startswith("/"):
                if address.startswith("/specification/") and mapping["anchors"]:
                    if address != "/specification/" or (fragment and address + "#" + fragment not in public):
                        findings.append(finding("public-anchor", rel, f"Unknown specification target: {href}"))
                elif address not in mapping["routes"]:
                    findings.append(finding("public-route", rel, f"No active route: {href}"))
                continue
            target = (path.parent / address).resolve() if address else path.resolve()
            if str(rel).startswith(DOCS) and target.is_relative_to(root) and target.relative_to(root).as_posix() in ("spec/requirements.md", "docs/delivery/contracts.md"):
                findings.append(finding("private-register-link", rel, "Public guides cannot link to internal registers"))
                continue
            if not target.is_relative_to(root) or not target.is_file():
                findings.append(finding("missing-link", rel, f"Missing or unsafe local target: {href}"))
                continue
            target_name = target.relative_to(root).as_posix()
            if target_name.startswith("spec/") and target_name != "spec/requirements.md" and (target_name, fragment) not in sources:
                findings.append(finding("source-anchor", rel, f"Unknown canonical source target: {href}"))
            elif fragment and not target_name.startswith("spec/"):
                target_text = target.read_text()
                _, explicit = tokens_and_ids(target_text)
                implicit = {re.sub(r"[^\w -]", "", line.lstrip("# ").lower()).replace(" ", "-") for line in target_text.splitlines() if line.startswith("#")}
                if fragment not in set(explicit) | implicit:
                    findings.append(finding("missing-anchor", rel, f"Missing target fragment: {href}"))
    if not source_only:
        check_registers(root, stage, findings)
    return findings


def baseline_stage(ref):
    result = subprocess.run(["git", "show", f"{ref}:tools/document-stage.json"], cwd=ROOT, text=True, capture_output=True)
    if result.returncode == 0:
        try:
            data = json.loads(result.stdout)
            if set(data) == {"stage"} and data["stage"] in STAGES: return data["stage"]
        except (ValueError, TypeError): pass
        raise ValueError("Reviewed baseline has an invalid stage marker")
    listing = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref], cwd=ROOT, text=True, capture_output=True)
    seed = {"AGENTS.md", "CLAUDE.md", "REVIEW.md", "README.md", "LICENSE", "Makefile", ".gitignore", ".github/pull_request_template.md", ".github/workflows/gates.yml"}
    if listing.returncode == 0 and set(listing.stdout.splitlines()) == seed:
        return "foundation"
    raise ValueError("Baseline must contain a stage marker or be the reviewed nine-file seed")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--scope", choices=("present",) + STAGES, default="present")
    parser.add_argument("--baseline-ref")
    parser.add_argument("--site-map", action="store_true")
    args = parser.parse_args(argv)
    minimum = args.scope if args.scope != "present" else "foundation"
    if args.baseline_ref:
        try: minimum = max((minimum, baseline_stage(args.baseline_ref)), key=STAGES.index)
        except ValueError as exc:
            print(f"baseline-stage: {exc}", file=sys.stderr)
            return 1
    findings = check_tree(args.root, minimum, source_only=args.site_map)
    if findings:
        for item in findings:
            print(f'{item["path"]}: {item["rule"]}: {item["message"]}', file=sys.stderr)
        return 1
    if args.site_map:
        stage, _ = marker(args.root)
        print(json.dumps(site_map(args.root, max((stage, minimum), key=STAGES.index), [])))
    else:
        print(f"Checked {len(document_paths(args.root))} documents; stage {marker(args.root)[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
