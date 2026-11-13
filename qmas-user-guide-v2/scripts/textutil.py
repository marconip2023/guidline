"""Shared text helpers for the QMAS working-copy build."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

BUTTON_RE = re.compile(r"\[\[(btn|ghost):([^\]]+)\]\]")
GUIDE_RE = re.compile(r"\[\[guide:([a-z0-9-]+)(?:\|([^\]]+))?\]\]")
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
URL_RE = re.compile(r"https?://[^\s<&]+")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jpeg_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:2] != b"\xff\xd8":
        raise ValueError(f"not a jpeg: {path}")
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            raise ValueError(f"bad jpeg marker in {path} at {index}")
        marker = data[index + 1]
        index += 2
        if marker in (0xD8, 0xD9) or marker == 0x01 or 0xD0 <= marker <= 0xD7:
            continue
        if index + 2 > len(data):
            break
        length = int.from_bytes(data[index : index + 2], "big")
        if marker in (0xC0, 0xC1, 0xC2, 0xC3):
            height = int.from_bytes(data[index + 3 : index + 5], "big")
            width = int.from_bytes(data[index + 5 : index + 7], "big")
            return width, height
        index += length
    raise ValueError(f"no jpeg frame header in {path}")


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def inline_md(text: str, titles: dict[str, str] | None = None) -> str:
    def guide(match: re.Match[str]) -> str:
        slug = match.group(1)
        label = match.group(2) or (titles or {}).get(slug, slug)
        return f"[{label}]({slug}.md)"

    text = BUTTON_RE.sub(r"**\2**", text)
    text = GUIDE_RE.sub(guide, text)
    return text


def plain(text: str, titles: dict[str, str] | None = None) -> str:
    def guide(match: re.Match[str]) -> str:
        return match.group(2) or (titles or {}).get(match.group(1), match.group(1))

    text = BUTTON_RE.sub(r"\2", text)
    text = GUIDE_RE.sub(guide, text)
    text = MD_LINK_RE.sub(r"\1", text)
    text = text.replace("**", "")
    return collapse(text)


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def iter_content_strings(module: dict):
    yield module["title"]
    yield module["purpose"]
    for key, value in module["meta"]:
        yield key
        yield value
    for item in module["overview"]:
        yield item
    for step in module["steps"]:
        yield step["h"]
        for block in step["body"]:
            yield from iter_block_strings(block)
    for tip in module.get("tips") or []:
        if isinstance(tip, str):
            yield tip
        else:
            yield from iter_block_strings(tip)
    for question, answer in module.get("faq") or []:
        yield question
        yield answer


def iter_block_strings(block):
    if isinstance(block, str):
        yield block
        return
    if "list" in block:
        yield from block["list"]
        return
    if "olist" in block:
        yield from block["olist"]
        return
    if "table" in block:
        for row in block["table"]:
            yield from row
        return
    if "img" in block:
        yield block.get("caption") or ""
        alt = block.get("alt") or ""
        if alt and alt != block.get("caption"):
            yield alt
        if block.get("caption_note"):
            yield block["caption_note"]
        if block.get("pending_note"):
            yield block["pending_note"]
        return
    raise ValueError(f"unknown block: {block!r}")


def module_plain(module: dict, titles: dict[str, str] | None = None) -> str:
    parts = [plain(piece, titles) for piece in iter_content_strings(module) if piece]
    return "\n" + "\n".join(parts) + "\n"
