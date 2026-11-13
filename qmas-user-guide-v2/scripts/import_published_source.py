"""Read the published QMAS guide text and write canonical content JSON.

Usage:
  python3 scripts/import_published_source.py \\
    --source /path/to/qmas-user-guide \\
    --images /path/to/reviewed-root

The source tree is the published guide repository. Only text is read from it.
Screenshot files under that tree are never copied. Reviewed replacements come
from --images, laid out as <slug>/img/<file>.jpg.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dev_verified import apply_dev_verified
from htmltree import find_first, normalized_text, parse_html
from textutil import collapse, jpeg_size, module_plain, plain, sha256_file

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
MODULES = CONTENT / "modules"
REVIEWED = ROOT / "assets" / "reviewed"

ORDER = [
    "product-testing",
    "getting-started",
    "product-management",
    "product-profile",
    "test-plan",
    "efiling",
    "supplier-management",
    "factory-management",
    "factory-audit",
    "document-management",
    "qc-inspection",
    "internal-qc-inspection",
    "document-review",
    "ai-insight",
]

GROUPS = [
    {
        "heading": "Product Testing",
        "app_href": "https://qmas.icw.io/product-testing",
        "items": [{"slug": "product-testing", "label": "Request a quotation (Create Job)"}],
    },
    {
        "heading": "Getting started",
        "items": [{"slug": "getting-started", "label": "Home, settings and company profile"}],
    },
    {
        "heading": "Product Management",
        "app_href": "https://qmas.icw.io/product/list",
        "items": [
            {"slug": "product-management", "label": "Create and edit a product"},
            {
                "slug": "product-profile",
                "label": "Every tab of the product profile (Document, Compliance Data, Quality Requirement, Packaging…)",
            },
            {"slug": "test-plan", "label": "Request a Test Plan (Help Center, 2024)"},
            {"slug": "efiling", "label": "Submit eFiling to CPSC"},
        ],
    },
    {
        "heading": "Supplier & Factory Management",
        "app_href": "https://qmas.icw.io/supplier-manager/suppliers",
        "items": [
            {"slug": "supplier-management", "label": "Create a supplier"},
            {"slug": "factory-management", "label": "Create a factory"},
            {"slug": "factory-audit", "label": "Request a Factory Audit quotation (Help Center, 2024)"},
        ],
    },
    {
        "heading": "Document Management",
        "app_href": "https://qmas.icw.io/document-management",
        "items": [{"slug": "document-management", "label": "Upload a document"}],
    },
    {
        "heading": "QC Inspection",
        "app_href": "https://qmas.icw.io/inspection",
        "items": [{"slug": "qc-inspection", "label": "Get a QC inspection quote via ICW"}],
    },
    {
        "heading": "Internal QC Inspection",
        "app_href": "https://qmas.icw.io/inspection/internal/list",
        "items": [{"slug": "internal-qc-inspection", "label": "Start an internal inspection"}],
    },
    {
        "heading": "Document Review",
        "app_href": "https://qmas.icw.io/document-review",
        "items": [
            {"slug": "document-review", "label": "Upload documents for lab review"},
            {"slug": "document-review", "label": "Ask a supplier to upload for lab review"},
            {"slug": "document-review", "label": "Ask a supplier to upload for your own review"},
        ],
    },
    {
        "heading": "AI Insight",
        "items": [{"slug": "ai-insight", "label": "Run an AI Risk Screening"}],
    },
]

VERSION = "2026-11-13-draft"
PUBLISHED = [slug for slug in ORDER if slug not in {"test-plan", "factory-audit"}]
NOTION_HUB = "https://app.notion.com/p/4139c62c39fc8198ac49e172050cf65b"
SOURCE_SITE = "https://marconip2026.github.io/qmas-user-guide/"


def inline_node(node) -> str:
    parts = []
    for child in node.children:
        if isinstance(child, str):
            parts.append(child)
        else:
            parts.append(render_inline(child))
    return collapse("".join(parts))


def render_inline(node) -> str:
    if node.tag in {"b", "strong"}:
        return f"**{inline_node(node)}**"
    if node.tag == "span":
        classes = node.cls()
        inner = inline_node(node)
        if "ghost" in classes:
            return f"[[ghost:{inner}]]"
        if "btn" in classes:
            return f"[[btn:{inner}]]"
        return inner
    if node.tag == "a":
        label = inline_node(node)
        href = node.attrs.get("href", "")
        return f"[{label}]({href})"
    if node.tag == "br":
        return " "
    return inline_node(node)


def element_children(node):
    return [child for child in node.children if not isinstance(child, str)]


def figure_block(node) -> dict:
    image = next(child for child in element_children(node) if child.tag == "img")
    caption = next(child for child in element_children(node) if child.tag == "figcaption")
    filename = image.attrs["src"].split("/")[-1]
    return {
        "img": filename,
        "alt": image.attrs.get("alt", ""),
        "caption": inline_node(caption),
    }


def table_block(node) -> dict:
    rows = []
    for row in element_children(node):
        if row.tag != "tr":
            continue
        cells = [inline_node(cell) for cell in element_children(row) if cell.tag in {"th", "td"}]
        if cells:
            rows.append(cells)
    return {"table": rows}


def list_block(node) -> dict:
    return {"list": [inline_node(item) for item in element_children(node) if item.tag == "li"]}


def blocks_from(nodes) -> list:
    blocks = []
    for node in nodes:
        if isinstance(node, str):
            continue
        if node.tag == "p":
            blocks.append(inline_node(node))
        elif node.tag in {"ul", "ol"} and "overview" not in node.cls():
            blocks.append(list_block(node))
        elif node.tag == "table":
            blocks.append(table_block(node))
        elif node.tag == "figure":
            blocks.append(figure_block(node))
        elif node.tag == "div" and "tip" in node.cls():
            blocks.append(inline_node(node))
        elif node.tag in {"h2", "h3"}:
            continue
        else:
            raise SystemExit(f"unexpected product-testing block <{node.tag}>")
    return blocks


def parse_product_testing(path: Path) -> dict:
    root = parse_html(path.read_text(encoding="utf-8"))
    main = find_first(root, "main")
    children = element_children(main)
    title = next(inline_node(node) for node in children if node.tag == "h1")
    purpose = next(inline_node(node) for node in children if "sub" in node.cls())
    meta_node = next(node for node in children if "meta" in node.cls())
    meta_bits = [child for child in meta_node.children if not isinstance(child, str)]
    meta = []
    for index in range(0, len(meta_bits), 2):
        meta.append([inline_node(meta_bits[index]), inline_node(meta_bits[index + 1])])
    overview_node = next(node for node in children if "overview" in node.cls())
    overview = [inline_node(item) for item in element_children(overview_node)]
    steps = []
    tips = []
    mode = None
    current = None
    for node in children:
        if node.tag == "h2":
            heading = inline_node(node)
            mode = {"Overview": "overview", "Step-by-step": "steps", "Tips": "tips"}.get(heading)
            current = None
            continue
        if mode == "steps" and node.tag == "h3":
            current = {"h": inline_node(node), "body": []}
            steps.append(current)
            continue
        if mode == "steps" and current is not None:
            current["body"].extend(blocks_from([node]))
        elif mode == "tips":
            tips.extend(blocks_from([node]))
    return {
        "slug": "product-testing",
        "source_path": "product-testing/",
        "origin": "handwritten-html",
        "tab_title": "Product Testing Guide",
        "title": title,
        "purpose": purpose,
        "meta": meta,
        "overview": overview,
        "steps": steps,
        "tips": tips,
        "faq": [],
    }


def load_json_module(source: Path, slug: str) -> dict:
    data = json.loads((source / "guides" / f"{slug}.json").read_text(encoding="utf-8"))
    module = {
        "slug": slug,
        "source_path": f"{slug}/",
        "origin": "guides-json",
    }
    module.update(data)
    return module


def published_blocks(path: Path) -> list[str]:
    root = parse_html(path.read_text(encoding="utf-8"))
    main = find_first(root, "main")
    blocks = []

    def add(text: str):
        cleaned = collapse(text)
        if not cleaned or cleaned in {"← All guides", "All guides"}:
            return
        blocks.append(cleaned)

    def walk(node):
        if isinstance(node, str):
            return
        classes = node.cls()
        if node.tag == "div" and "tip" in classes:
            add(normalized_text(node))
            return
        if node.tag == "div" and "meta" in classes:
            for child in node.children:
                if not isinstance(child, str) and child.tag in {"b", "span"}:
                    add(normalized_text(child))
            return
        if node.tag in {"h1", "h2", "h3", "p", "li", "figcaption", "dt", "dd", "th", "td"}:
            add(normalized_text(node))
            return
        if node.tag == "img":
            add(node.attrs.get("alt", ""))
            return
        for child in node.children:
            walk(child)

    walk(main)
    return blocks


PROFILE_SUPERSEDED = {
    "Document tab.",
    "Shipping Detail tab.",
    "Search legislation and test items by keyword.",
    "A completed Test Data record with the report linked.",
    "Saved test data.",
    "Empty Quality Requirement tab: Add Requirement, Test Plan (AI) and the ⋯ menu.",
    "Add Requirement with Type, Name and Mandatory.",
    "Legislation, Test Item & Citation (required): type a keyword such as “lead” and pick the test item.",
    "Click Confirm. The record appears in the Test Data table with its export market, legislation, test item, citation, report ID and issue party.",
}


def skipped(slug: str, block: str) -> bool:
    if block in {"Overview", "Step-by-step", "Tips", "FAQ"}:
        return True
    if slug == "product-profile" and block in PROFILE_SUPERSEDED:
        return True
    if "gear icon" in block or "github.io" in block or "marconip2026.github.io" in block:
        return True
    exact = {
        ("getting-started", "The top bar has analytics, messages, notifications, settings, help and credits."),
        ("getting-started", "TicMate asks “What would you like to do today?” and lists quick workflows:"),
        ("getting-started", "QMAS dev, 4 Nov 2026"),
        ("product-management", "QMAS dev, 4 Nov 2026"),
    }
    return (slug, block) in exact


def assert_coverage(modules: dict[str, dict], blocks_by_slug: dict[str, list[str]]):
    missing = []
    for slug, blocks in blocks_by_slug.items():
        haystack = module_plain(modules[slug])
        for block in blocks:
            if skipped(slug, block):
                continue
            if block not in haystack:
                missing.append((slug, block))
    if missing:
        preview = "\n".join(f"{slug}: {block[:180]}" for slug, block in missing[:12])
        raise SystemExit(f"{len(missing)} published text blocks missing from content:\n{preview}")


def copy_reviewed(modules: dict[str, dict], images_root: Path) -> list[dict]:
    if REVIEWED.exists():
        for stale in REVIEWED.rglob("*"):
            if stale.is_file():
                stale.unlink()
    records = []
    for slug in PUBLISHED:
        for block in image_blocks(modules[slug]):
            filename = block["img"]
            if block.get("availability") == "not-captured":
                source = images_root / slug / "img" / filename
                if source.exists():
                    raise SystemExit(f"refusing to publish not-captured image {slug}/{filename}")
                continue
            source = images_root / slug / "img" / filename
            if not source.exists():
                continue
            target = REVIEWED / slug / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            width, height = jpeg_size(target)
            records.append({
                "slug": slug,
                "file": filename,
                "sha256": sha256_file(target),
                "width": width,
                "height": height,
                "bytes": target.stat().st_size,
            })
    return records


def image_blocks(module: dict):
    for step in module["steps"]:
        for block in step["body"]:
            if isinstance(block, dict) and "img" in block:
                yield block
    for tip in module.get("tips") or []:
        if isinstance(tip, dict) and "img" in tip:
            yield tip


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    modules = {}
    blocks = {}
    for slug in PUBLISHED:
        page = source / slug / "index.html"
        if slug == "product-testing":
            modules[slug] = parse_product_testing(page)
        else:
            modules[slug] = load_json_module(source, slug)
        blocks[slug] = published_blocks(page)
    apply_dev_verified(modules)
    assert_coverage(modules, blocks)
    MODULES.mkdir(parents=True, exist_ok=True)
    for slug, module in modules.items():
        (MODULES / f"{slug}.json").write_text(
            json.dumps(module, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    (CONTENT / "published-text-blocks.json").write_text(
        json.dumps(blocks, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    records = copy_reviewed(modules, args.images.resolve())
    (CONTENT / "reviewed-images.json").write_text(
        json.dumps({"version": VERSION, "images": records}, indent=2) + "\n",
        encoding="utf-8",
    )
    catalog = {
        "title": "QMAS User Guide",
        "version": VERSION,
        "status": "working-copy-draft",
        "language": "en",
        "source_site": SOURCE_SITE,
        "notion_working_hub": NOTION_HUB,
        "groups": GROUPS,
        "order": ORDER,
    }
    (CONTENT / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    image_count = sum(1 for module in modules.values() for _block in image_blocks(module))
    print(f"modules {len(modules)} image slots {image_count} reviewed files {len(records)}")


if __name__ == "__main__":
    main()
