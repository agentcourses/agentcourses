"""Read the parts of a Markdown file that the format gives meaning to."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import yaml
from markdown_it import MarkdownIt

_PARSER = MarkdownIt("commonmark")
_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")


class FrontmatterError(ValueError):
    """The file has no frontmatter, or it is not a YAML mapping."""


@dataclass
class Block:
    """A heading, paragraph or list. Code blocks are dropped, so headings inside them never count."""

    kind: str
    line: int
    level: int = 0
    text: str = ""
    links: list[str] = field(default_factory=list)
    items: list[list[Block]] = field(default_factory=list)


def split_frontmatter(text: str) -> tuple[dict, str, int]:
    """Return the frontmatter mapping, the body and the body's first line number."""
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("the file must start with a --- line")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            try:
                data = yaml.safe_load("".join(lines[1:index]))
            except yaml.YAMLError as error:
                raise FrontmatterError(f"the frontmatter is not valid YAML: {error}") from error
            if not isinstance(data, dict):
                raise FrontmatterError("the frontmatter must be a YAML mapping")
            return data, "".join(lines[index + 1 :]), index + 2
    raise FrontmatterError("the frontmatter has no closing --- line")


def parse(body: str, first_line: int = 1) -> list[Block]:
    tokens = _PARSER.parse(body)
    blocks, _ = _blocks(tokens, 0, None, first_line - 1)
    return blocks


def links(body: str) -> list[str]:
    """Every link target in the body, outside code."""
    found = []
    for token in _PARSER.parse(body):
        for child in token.children or []:
            if child.type == "link_open":
                found.append(str(child.attrGet("href")))
    return found


def is_relative(href: str) -> bool:
    return not href.startswith("#") and not _SCHEME.match(href)


def sections(blocks: list[Block]) -> tuple[dict[str, list[Block]], list[tuple[str, int]]]:
    """Split top-level blocks by level-two heading. Also return every level-two heading in order."""
    found: dict[str, list[Block]] = {}
    order: list[tuple[str, int]] = []
    current: list[Block] | None = None
    for block in blocks:
        if block.kind == "heading" and block.level == 2:
            order.append((block.text, block.line))
            current = found.setdefault(block.text, [])
        elif current is not None:
            current.append(block)
    return found, order


def item_links(item: list[Block]) -> list[str]:
    """Links written directly in a list item, not in any list nested inside it."""
    return [href for block in item if block.kind == "paragraph" for href in block.links]


def _blocks(tokens, index, close, offset):
    out: list[Block] = []
    while index < len(tokens):
        token = tokens[index]
        line = token.map[0] + 1 + offset if token.map else 0
        if close and token.type == close:
            return out, index + 1
        if token.type == "heading_open":
            out.append(Block("heading", line, level=int(token.tag[1]), text=tokens[index + 1].content.strip()))
            index += 3
        elif token.type == "paragraph_open":
            inline = tokens[index + 1]
            hrefs = [str(c.attrGet("href")) for c in inline.children or [] if c.type == "link_open"]
            out.append(Block("paragraph", line, text=inline.content, links=hrefs))
            index += 3
        elif token.type in ("bullet_list_open", "ordered_list_open"):
            items, index = _items(tokens, index + 1, token.type.replace("_open", "_close"), offset)
            out.append(Block("list", line, items=items, level=1 if token.type.startswith("ordered") else 0))
        else:
            index += 1
    return out, index


def _items(tokens, index, close, offset):
    items = []
    while tokens[index].type != close:
        if tokens[index].type == "list_item_open":
            item, index = _blocks(tokens, index + 1, "list_item_close", offset)
            items.append(item)
        else:
            index += 1
    return items, index + 1
