"""Build the working-copy site, Markdown, and PDFs from content JSON.

Usage:
  python3 scripts/build.py
  python3 scripts/build.py --skip-pdf
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from textutil import (
    BUTTON_RE,
    GUIDE_RE,
    URL_RE,
    collapse,
    inline_md,
    jpeg_size,
    sha256_file,
    yaml_quote,
)

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content"
CSS = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
CHROME = "/opt/google/chrome/chrome" if Path("/opt/google/chrome/chrome").exists() else (
    shutil.which("google-chrome") or shutil.which("google-chrome-stable")
)


def load():
    catalog = json.loads((CONTENT / "catalog.json").read_text(encoding="utf-8"))
    modules = []
    additions = {}
    additions_path = CONTENT / "reconciliation.json"
    if additions_path.exists():
        additions = json.loads(additions_path.read_text(encoding="utf-8"))
    for slug in catalog["order"]:
        module = json.loads((CONTENT / "modules" / f"{slug}.json").read_text(encoding="utf-8"))
        if slug in additions:
            module["additions"] = additions[slug]
        modules.append(module)
    reviewed = json.loads((CONTENT / "reviewed-images.json").read_text(encoding="utf-8"))
    by_key = {}
    for record in reviewed["images"]:
        path = ROOT / "assets" / "reviewed" / record["slug"] / record["file"]
        if not path.exists():
            raise SystemExit(f"missing reviewed image {path}")
        if sha256_file(path) != record["sha256"]:
            raise SystemExit(f"reviewed image hash mismatch: {record['slug']}/{record['file']}")
        if jpeg_size(path) != (record["width"], record["height"]):
            raise SystemExit(f"reviewed image size mismatch: {record['slug']}/{record['file']}")
        by_key[(record["slug"], record["file"])] = record
    titles = {module["slug"]: module["title"] for module in modules}
    return catalog, modules, by_key, titles


def inline_html(text: str, guide_prefix: str, titles: dict[str, str]) -> str:
    placeholders = []

    def hold(snippet: str) -> str:
        placeholders.append(snippet)
        return f"\x00{len(placeholders) - 1}\x00"

    def button(match):
        kind, label = match.group(1), match.group(2)
        css = "ui-label ghost" if kind == "ghost" else "ui-label"
        return hold(f'<span class="{css}">{html.escape(label)}</span>')

    def guide(match):
        slug = match.group(1)
        label = match.group(2) or titles.get(slug, slug)
        href = f"{guide_prefix}{slug}/"
        return hold(f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>')

    def link(match):
        label, href = match.group(1), match.group(2)
        return hold(f'<a href="{html.escape(href, quote=True)}">{html.escape(label)}</a>')

    import re
    text = BUTTON_RE.sub(button, text)
    text = GUIDE_RE.sub(guide, text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", link, text)
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)

    def autolink(match):
        raw = match.group(0)
        url = raw.rstrip(").,;]")
        tail = html.escape(raw[len(url):])
        safe = html.escape(url, quote=True)
        return f'<a href="{safe}">{safe}</a>{tail}'

    escaped = URL_RE.sub(autolink, escaped)
    return re.sub(r"\x00(\d+)\x00", lambda match: placeholders[int(match.group(1))], escaped)


def image_html(module, block, reviewed, guide_prefix: str, first_image: dict) -> str:
    filename = block["img"]
    alt = block.get("alt") or block.get("caption") or filename
    caption = block.get("caption") or ""
    note = block.get("caption_note") or ""
    availability = block.get("availability")
    record = reviewed.get((module["slug"], filename))
    if availability == "not-captured":
        if record:
            raise SystemExit(f"not-captured slot has a file: {module['slug']}/{filename}")
        body = pending_box(filename, "", block.get("pending_note") or "", "not-captured")
    elif record:
        src = f"{guide_prefix}assets/reviewed/{module['slug']}/{filename}"
        priority = ""
        loading = ' loading="lazy" decoding="async"'
        if not first_image["used"]:
            priority = ' fetchpriority="high"'
            loading = ' decoding="async"'
            first_image["used"] = True
        body = (
            f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt)}" '
            f'width="{record["width"]}" height="{record["height"]}"{priority}{loading}>'
        )
    else:
        extra = alt if alt and alt != caption else ""
        body = pending_box(filename, extra, "Reviewed replacement image not available yet. Follow the written steps above.", "pending")
    note_html = f'<span class="caption-note">{html.escape(note)}</span>' if note else ""
    return (
        '<figure class="shot">'
        f"{body}"
        f"<figcaption>{html.escape(caption)}{note_html}</figcaption>"
        "</figure>\n"
    )


def pending_box(filename: str, alt: str, message: str, kind: str) -> str:
    title = "Not captured" if kind == "not-captured" else "Image pending privacy review"
    description = f"<p>{html.escape(alt)}</p>" if alt else ""
    return (
        f'<div class="pending {kind}">'
        f"<p><strong>{html.escape(title)}</strong></p>"
        f"<p>File name: <code>{html.escape(filename)}</code></p>"
        f"<p>{html.escape(message)}</p>"
        f"{description}"
        "</div>"
    )


def blocks_html(module, blocks, reviewed, guide_prefix, first_image) -> str:
    parts = []
    for block in blocks:
        if isinstance(block, str):
            parts.append(f"<p>{inline_html(block, guide_prefix, {})}</p>\n")
        elif "list" in block:
            items = "".join(f"<li>{inline_html(item, guide_prefix, {})}</li>" for item in block["list"])
            parts.append(f"<ul>{items}</ul>\n")
        elif "olist" in block:
            items = "".join(f"<li>{inline_html(item, guide_prefix, {})}</li>" for item in block["olist"])
            parts.append(f"<ol>{items}</ol>\n")
        elif "table" in block:
            parts.append(table_html(block["table"], guide_prefix))
        elif "img" in block:
            parts.append(image_html(module, block, reviewed, guide_prefix, first_image))
        else:
            raise SystemExit(f"unknown block in {module['slug']}")
    return "".join(parts)


def table_html(rows, guide_prefix: str) -> str:
    head, *body = rows
    label = ", ".join(head)
    header = "".join(f'<th scope="col">{inline_html(cell, guide_prefix, {})}</th>' for cell in head)
    body_html = ""
    for row in body:
        cells = "".join(f"<td>{inline_html(cell, guide_prefix, {})}</td>" for cell in row)
        body_html += f"<tr>{cells}</tr>"
    return (
        f'<div class="table-wrap" tabindex="0" role="region" aria-label="{html.escape(label)}">'
        "<table>"
        f"<thead><tr>{header}</tr></thead><tbody>{body_html}</tbody></table></div>\n"
    )


def article_html(module, reviewed, guide_prefix: str, catalog: dict, banner: bool) -> str:
    titles = {}
    first_image = {"used": False}
    reviewed_count = 0
    pending_count = 0
    not_captured = 0
    for block in iter_images(module):
        if block.get("availability") == "not-captured":
            not_captured += 1
        elif (module["slug"], block["img"]) in reviewed:
            reviewed_count += 1
        else:
            pending_count += 1
    if reviewed_count + pending_count + not_captured == 0 and module.get("confidence") == "source-documented":
        status = "Screenshot slots: none. This page does not include screenshots."
    elif not_captured:
        status = f"Screenshot slots: {reviewed_count} reviewed, {not_captured} explicitly not captured, {pending_count} still pending privacy review."
    elif pending_count and not reviewed_count:
        status = f"Screenshot slots: {pending_count} pending privacy review. The written steps are included."
    elif pending_count:
        status = f"Screenshot slots: {reviewed_count} reviewed and {pending_count} pending privacy review."
    else:
        status = f"Screenshot slots: {reviewed_count} reviewed replacement images."
    parts = []
    if banner:
        parts.append(
            '<p class="draft-banner">Working copy draft '
            f'{html.escape(catalog["version"])}. English text from the published QMAS User Guide, '
            "with dev-verified corrections from 9 Nov 2026. Unreviewed screenshots are omitted.</p>\n"
        )
    parts.append(f"<h1>{html.escape(module['title'])}</h1>\n")
    parts.append(f'<p class="lede">{inline_html(module["purpose"], guide_prefix, titles)}</p>\n')
    parts.append(f'<p class="status-line">{html.escape(status)}</p>\n')
    parts.append('<dl class="meta">\n')
    for key, value in module["meta"]:
        parts.append(f"<dt>{html.escape(key)}</dt><dd>{inline_html(value, guide_prefix, titles)}</dd>\n")
    parts.append("</dl>\n<h2>Overview</h2>\n<ol class=\"overview\">\n")
    for item in module["overview"]:
        parts.append(f"<li>{inline_html(item, guide_prefix, titles)}</li>\n")
    parts.append("</ol>\n<h2>Step-by-step</h2>\n")
    for step in module["steps"]:
        parts.append(f"<h3>{html.escape(step['h'])}</h3>\n")
        parts.append(blocks_html(module, step["body"], reviewed, guide_prefix, first_image))
    if module.get("tips"):
        parts.append("<h2>Tips</h2>\n")
        for tip in module["tips"]:
            if isinstance(tip, str):
                parts.append(f'<aside class="tip"><p>{inline_html(tip, guide_prefix, titles)}</p></aside>\n')
            else:
                parts.append(blocks_html(module, [tip], reviewed, guide_prefix, first_image))
    if module.get("faq"):
        parts.append('<h2>FAQ</h2>\n<dl class="faq">\n')
        for question, answer in module["faq"]:
            parts.append(
                f"<dt>{inline_html(question, guide_prefix, titles)}</dt>"
                f"<dd>{inline_html(answer, guide_prefix, titles)}</dd>\n"
            )
        parts.append("</dl>\n")
    if module.get("confidence") == "source-documented":
        parts.insert(0, (
            '<p class="draft-banner">Source-documented only, from the original Help Center. '
            "Not confirmed on the current QMAS dev site. No reviewed screenshots. "
            "Do not treat the labels below as current UI until they are checked.</p>\n"
        ))
    parts.append(additions_html(module, guide_prefix, titles))
    return "".join(parts)


def additions_html(module, guide_prefix, titles) -> str:
    data = module.get("additions")
    if not data:
        return ""
    parts = [
        '<section class="additions">',
        "<h2>Help Center additions and remaining gaps</h2>",
        '<aside class="callout"><p>This section adds Help Center material and named gaps. It does not replace the steps above.</p>',
        "<ul>",
        "<li><strong>Source-documented</strong> — written in the original Help Center. The last-edited date is given. That does not by itself prove the current QMAS UI.</li>",
        "<li><strong>Dev-verified</strong> — confirmed on qmas-dev.icw.io during guide work.</li>",
        "<li><strong>Gap</strong> — named as missing or too thin. Not current behaviour until checked on dev.</li>",
        "</ul><p>Reviewed screenshots remain 33 of 98. No new images were added. Unreviewed Help Center screenshots were not copied.</p></aside>",
    ]
    for section in data["sections"]:
        kind = section.get("kind", "source-documented")
        parts.append(f'<h3 class="kind-{html.escape(kind)}">{inline_html(section["h"], guide_prefix, titles)}</h3>\n')
        parts.append(blocks_html(module, section["body"], {}, guide_prefix, {"used": True}))
    parts.append(
        '<p class="reconcile-note">Help Center reconciliation 2026-11-13 (HKT). '
        "Original Help Center not edited. This draft is not the public guide at the marconip2026 site. "
        "No Dify upload.</p></section>\n"
    )
    return "".join(parts)


def iter_images(module):
    for step in module["steps"]:
        for block in step["body"]:
            if isinstance(block, dict) and "img" in block:
                yield block
    for tip in module.get("tips") or []:
        if isinstance(tip, dict) and "img" in tip:
            yield tip


def page(title: str, body: str, home: str, crumb: str | None) -> str:
    crumb_html = f'<p class="crumb"><a href="{html.escape(home, quote=True)}">All guides</a></p>\n' if crumb else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<style>
{CSS}
</style>
</head>
<body>
<a class="skip-link visually-hidden" href="#content">Skip to content</a>
<header class="site-header">
  <p class="site-mark"><a href="{html.escape(home, quote=True)}">QMAS User Guide</a></p>
  <p class="version-line">Working copy draft</p>
</header>
<main id="content" tabindex="-1">
{crumb_html}{body}
</main>
<footer class="site-footer"><p>Working copy for review. Not a replacement for the older guide at the repository root.</p></footer>
</body>
</html>
"""


def render_index(catalog, modules, reviewed) -> str:
    counts = {}
    for module in modules:
        reviewed_count = pending = missed = 0
        for block in iter_images(module):
            if block.get("availability") == "not-captured":
                missed += 1
            elif (module["slug"], block["img"]) in reviewed:
                reviewed_count += 1
            else:
                pending += 1
        counts[module["slug"]] = (reviewed_count, pending, missed)
    groups = []
    for group in catalog["groups"]:
        app = ""
        if group.get("app_href"):
            app = f'<a href="{html.escape(group["app_href"], quote=True)}">Open module</a>'
        items = []
        for item in group["items"]:
            reviewed_count, pending, missed = counts[item["slug"]]
            module = next(entry for entry in modules if entry["slug"] == item["slug"])
            if module.get("confidence") == "source-documented" and reviewed_count + pending + missed == 0:
                tag = '<span class="tag">Source-documented · no screenshots</span>'
            elif missed:
                tag = f'<span class="tag">{reviewed_count} reviewed, {missed} not captured</span>'
            elif pending and reviewed_count:
                tag = f'<span class="tag">{reviewed_count} reviewed, {pending} pending</span>'
            elif pending:
                tag = f'<span class="tag">Screenshots pending</span>'
            else:
                tag = f'<span class="tag reviewed">Reviewed screenshots</span>'
            items.append(
                f'<li><a href="{html.escape(item["slug"], quote=True)}/">{html.escape(item["label"])}</a> {tag}</li>'
            )
        groups.append(
            '<section class="module-group">'
            f"<h2>{html.escape(group['heading'])} {app}</h2><ul>{''.join(items)}</ul></section>\n"
        )
    body = f"""
<p class="draft-banner">Working copy draft {html.escape(catalog["version"])}. Fourteen English modules. The public guide stays on the marconip2026 site. This branch is not deployed. Reviewed screenshots remain 33 of 98. Factory Audit and Test Plan are source-documented only and have no screenshots.</p>
<p class="lede">Existing create-path steps, captions, and reviewed images are unchanged. A Help Center section was added on 2026-11-13. Source-documented text is not the same as dev-verified text.</p>
<p>The same 14 modules are in the <a href="{html.escape(catalog["notion_working_hub"], quote=True)}">Notion working hub</a>.</p>
<p><a href="combined/">Read all guides in one page</a></p>
{''.join(groups)}
"""
    return page("QMAS User Guide (working copy draft)", body, "./", None).replace(
        '<main id="content" tabindex="-1">',
        '<main id="content" class="wide" tabindex="-1">',
        1,
    )


def render_md(module, reviewed, catalog, titles) -> str:
    lines = [
        "---",
        f"title: {yaml_quote(module['title'])}",
        f"slug: {module['slug']}",
        "document_status: working-copy-draft",
        f"version: {catalog['version']}",
        "language: en",
        f"notion_working_hub: {catalog['notion_working_hub']}",
        f"confidence: {module.get('confidence', 'published-guide-plus-dev-verified-corrections')}",
        "image_policy: Reviewed replacement screenshots use a relative path. Other screenshots are explicit placeholders and are not linked.",
        "---",
        "",
        f"# {module['title']}",
        "",
        f"> Working copy draft {catalog['version']}. English text from the published QMAS User Guide. Unreviewed screenshots are omitted.",
        "",
        inline_md(module["purpose"], titles),
        "",
    ]
    for key, value in module["meta"]:
        lines.append(f"- **{key}:** {inline_md(value, titles)}")
    lines.extend(["", "## Overview", ""])
    for index, item in enumerate(module["overview"], 1):
        lines.append(f"{index}. {inline_md(item, titles)}")
    lines.extend(["", "## Step-by-step", ""])
    for step in module["steps"]:
        lines.append(f"### {step['h']}")
        lines.append("")
        lines.append(blocks_md(module, step["body"], reviewed, titles))
    if module.get("tips"):
        lines.extend(["## Tips", ""])
        for tip in module["tips"]:
            if isinstance(tip, str):
                lines.append(f"- {inline_md(tip, titles)}")
            else:
                lines.append(blocks_md(module, [tip], reviewed, titles).rstrip())
        lines.append("")
    if module.get("faq"):
        lines.extend(["## FAQ", ""])
        for question, answer in module["faq"]:
            lines.append(f"**Q: {inline_md(question, titles)}**")
            lines.append("")
            lines.append(f"A: {inline_md(answer, titles)}")
            lines.append("")
    lines.append(additions_md(module, titles).rstrip())
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def additions_md(module, titles) -> str:
    data = module.get("additions")
    if not data:
        return ""
    lines = [
        "## Help Center additions and remaining gaps",
        "",
        "This section adds Help Center material and named gaps. It does not replace the steps above.",
        "",
        "- **Source-documented** — written in the original Help Center. The last-edited date is given. That does not by itself prove the current QMAS UI.",
        "- **Dev-verified** — confirmed on qmas-dev.icw.io during guide work.",
        "- **Gap** — named as missing or too thin. Not current behaviour until checked on dev.",
        "",
        "Reviewed screenshots remain 33 of 98. No new images were added. Unreviewed Help Center screenshots were not copied.",
        "",
    ]
    for section in data["sections"]:
        lines.append(f"### {section['h']}")
        lines.append("")
        lines.append(blocks_md(module, section["body"], {}, titles).rstrip())
        lines.append("")
    lines.append(
        "Help Center reconciliation 2026-11-13 (HKT). Original Help Center not edited. "
        "This draft is not the public guide. No Dify upload."
    )
    return "\n".join(lines) + "\n"


def blocks_md(module, blocks, reviewed, titles) -> str:
    parts = []
    for block in blocks:
        if isinstance(block, str):
            parts.append(inline_md(block, titles) + "\n\n")
        elif "list" in block:
            parts.append("".join(f"- {inline_md(item, titles)}\n" for item in block["list"]) + "\n")
        elif "olist" in block:
            parts.append("".join(f"{index}. {inline_md(item, titles)}\n" for index, item in enumerate(block["olist"], 1)) + "\n")
        elif "table" in block:
            head, *rows = block["table"]
            parts.append("| " + " | ".join(inline_md(cell, titles) for cell in head) + " |\n")
            parts.append("|" + "---|" * len(head) + "\n")
            for row in rows:
                parts.append("| " + " | ".join(inline_md(cell, titles) for cell in row) + " |\n")
            parts.append("\n")
        elif "img" in block:
            parts.append(image_md(module, block, reviewed) + "\n")
        else:
            raise SystemExit(block)
    return "".join(parts)


def image_md(module, block, reviewed) -> str:
    filename = block["img"]
    alt = block.get("alt") or block.get("caption") or filename
    caption = block.get("caption") or ""
    lines = []
    record = reviewed.get((module["slug"], filename))
    if block.get("availability") == "not-captured":
        lines.append(f"> **Not captured:** `{filename}`")
        lines.append(">")
        lines.append(f"> {block.get('pending_note')}")
    elif record:
        lines.append(f"![{alt}](images/{module['slug']}/{filename})")
        lines.append("")
    else:
        lines.append(f"> **Image pending privacy review:** `{filename}`")
        lines.append(">")
        lines.append("> Reviewed replacement image not available yet. Follow the written steps above.")
        if alt and alt != caption:
            lines.append(">")
            lines.append(f"> Description: {alt}")
    if caption:
        lines.append("")
        lines.append(f"*{caption}*")
    if block.get("caption_note"):
        lines.append("")
        lines.append(block["caption_note"])
    return "\n".join(lines) + "\n"


def render_combined_md(catalog, modules, reviewed, titles) -> str:
    lines = [
        "---",
        f"title: {yaml_quote(catalog['title'])}",
        "document_status: working-copy-draft",
        f"version: {catalog['version']}",
        "language: en",
        f"notion_working_hub: {catalog['notion_working_hub']}",
        "image_policy: Per-module files and this combined file are generated from the same content JSON.",
        "---",
        "",
        f"# {catalog['title']}",
        "",
        f"> Working copy draft {catalog['version']}. Combined export of the 12 published English guides.",
        "",
        f"Notion working hub: {catalog['notion_working_hub']}",
        "",
        "## Contents",
        "",
    ]
    for module in modules:
        lines.append(f"- [{module['title']}](#{module['slug']})")
    lines.append("")
    for module in modules:
        body = render_md(module, reviewed, catalog, titles)
        body = body.split("---", 2)[-1].lstrip("\n")
        lines.append(body)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_text(catalog, modules, reviewed, titles):
    index = ROOT / "index.html"
    index.write_text(render_index(catalog, modules, reviewed), encoding="utf-8")
    markdown = ROOT / "export" / "markdown"
    images = markdown / "images"
    if images.exists():
        shutil.rmtree(images)
    images.mkdir(parents=True)
    for record_key, record in reviewed.items():
        slug, filename = record_key
        source = ROOT / "assets" / "reviewed" / slug / filename
        target = images / slug / filename
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    combined_body = [
        '<p class="draft-banner">Working copy draft '
        f'{html.escape(catalog["version"])}. Combined page generated from the same source as the per-module pages.</p>',
        f"<h1>{html.escape(catalog['title'])}</h1>",
        "<h2>Contents</h2><ol>",
    ]
    articles = []
    for module in modules:
        combined_body.append(f'<li><a href="#{html.escape(module["slug"], quote=True)}">{html.escape(module["title"])}</a></li>')
        article = article_html(module, reviewed, "../", catalog, banner=False)
        articles.append(f'<article class="module" id="{html.escape(module["slug"], quote=True)}">{article}</article>')
        page_html = page(
            f"{module['tab_title']} · QMAS User Guide (draft)",
            article_html(module, reviewed, "../", catalog, banner=True),
            "../",
            "All guides",
        )
        target = ROOT / module["slug"] / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(page_html, encoding="utf-8")
        (markdown / f"{module['slug']}.md").write_text(
            render_md(module, reviewed, catalog, titles),
            encoding="utf-8",
        )
    combined_body.append("</ol>")
    combined_html = page(
        "QMAS User Guide (combined draft)",
        "\n".join(combined_body + articles),
        "../",
        "All guides",
    )
    combined_dir = ROOT / "combined"
    combined_dir.mkdir(parents=True, exist_ok=True)
    (combined_dir / "index.html").write_text(combined_html, encoding="utf-8")
    (markdown / "qmas-user-guide.md").write_text(
        render_combined_md(catalog, modules, reviewed, titles),
        encoding="utf-8",
    )
    print_dir = ROOT / "export" / "print"
    print_dir.mkdir(parents=True, exist_ok=True)
    for module in modules:
        print_html = page(
            module["title"],
            article_html(module, reviewed, "../../", catalog, banner=True),
            "../../",
            None,
        )
        (print_dir / f"{module['slug']}.html").write_text(print_html, encoding="utf-8")
    combined_print_articles = []
    for module in modules:
        article = article_html(module, reviewed, "../../", catalog, banner=False)
        combined_print_articles.append(
            f'<article class="module" id="{html.escape(module["slug"], quote=True)}">{article}</article>'
        )
    cover = (
        '<p class="draft-banner">Working copy draft '
        f'{html.escape(catalog["version"])}. Combined PDF generated from the same content as the per-module PDFs.</p>'
        f"<h1>{html.escape(catalog['title'])}</h1>"
        f"<p>Notion working hub: {html.escape(catalog['notion_working_hub'])}</p>"
    )
    (print_dir / "qmas-user-guide.html").write_text(
        page(catalog["title"], cover + "\n".join(combined_print_articles), "../../", None),
        encoding="utf-8",
    )


def print_pdf(html_path: Path, pdf_path: Path):
    if not CHROME:
        raise SystemExit("google-chrome is not installed")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()
    profile = Path(f"/tmp/qmas-chrome-{html_path.stem}")
    if profile.exists():
        shutil.rmtree(profile)
    command = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--no-pdf-header-footer",
        "--hide-scrollbars",
        f"--user-data-dir={profile}",
        f"--print-to-pdf={pdf_path}",
        html_path.resolve().as_uri(),
    ]
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=90,
        )
    except subprocess.TimeoutExpired as exc:
        raise SystemExit(f"PDF timed out for {html_path.name}") from exc
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if result.returncode != 0 or not pdf_path.exists():
        raise SystemExit(f"PDF failed for {html_path.name}: {result.stderr[-500:]}")


def write_pdfs():
    print_dir = ROOT / "export" / "print"
    pdf_dir = ROOT / "export" / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    html_files = sorted(print_dir.glob("*.html"))
    for html_path in html_files:
        print_pdf(html_path, pdf_dir / f"{html_path.stem}.pdf")
        print("pdf", html_path.stem)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-pdf", action="store_true")
    args = parser.parse_args()
    catalog, modules, reviewed, titles = load()
    write_text(catalog, modules, reviewed, titles)
    if not args.skip_pdf:
        write_pdfs()


if __name__ == "__main__":
    main()
