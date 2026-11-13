"""Build the working-copy site, Markdown, and PDFs from content JSON.

Usage:
  python3 scripts/build.py
  python3 scripts/build.py --skip-pdf
"""

from __future__ import annotations

import argparse
import html
import json
import re
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
    catalog["verification"] = json.loads((CONTENT / "verification.json").read_text(encoding="utf-8"))
    catalog["logo"] = json.loads((CONTENT / "logo.json").read_text(encoding="utf-8"))
    missing = [slug for slug in catalog["order"] if slug not in catalog["verification"]["modules"]]
    if missing:
        raise SystemExit(f"verification map missing: {', '.join(missing)}")
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
    parts.append(f"<h1>{html.escape(module['title'])}</h1>\n")
    if module.get("confidence") == "source-documented":
        parts.append(
            '<p class="draft-banner">Source-documented only, from the original Help Center. '
            "Not confirmed on the current QMAS dev site. No reviewed screenshots. "
            "Do not treat the labels below as current UI until they are checked.</p>\n"
        )
    parts.append(f'<p class="lede">{inline_html(module["purpose"], guide_prefix, titles)}</p>\n')
    parts.append(verification_html(module, catalog))
    parts.append(f'<p class="status-line">{html.escape(status)}</p>\n')
    used_ids = set()
    toc = ['<nav class="page-toc" aria-label="On this page"><ul>']
    step_ids = []
    for step in module["steps"]:
        base = re.sub(r"[^a-z0-9]+", "-", step["h"].lower()).strip("-")[:48] or "step"
        candidate = base
        number = 2
        while candidate in used_ids:
            candidate = f"{base}-{number}"
            number += 1
        used_ids.add(candidate)
        step_ids.append(candidate)
        toc.append(
            f'<li><a href="#{html.escape(candidate, quote=True)}">{html.escape(step["h"])}</a></li>'
        )
    toc.append("</ul></nav>\n")
    parts.append("".join(toc))
    parts.append("<h2>Overview</h2>\n<ol class=\"overview\">\n")
    for item in module["overview"]:
        parts.append(f"<li>{inline_html(item, guide_prefix, titles)}</li>\n")
    parts.append("</ol>\n")
    parts.append('<dl class="meta">\n')
    for key, value in module["meta"]:
        parts.append(f"<dt>{html.escape(key)}</dt><dd>{inline_html(value, guide_prefix, titles)}</dd>\n")
    parts.append("</dl>\n<h2>Step-by-step</h2>\n")
    for step, step_id in zip(module["steps"], step_ids):
        parts.append(f'<h3 id="{html.escape(step_id, quote=True)}">{html.escape(step["h"])}</h3>\n')
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
    parts.append(additions_html(module, guide_prefix, titles))
    return "".join(parts)


def additions_html(module, guide_prefix, titles) -> str:
    data = module.get("additions")
    if not data:
        return ""
    parts = [
        '<section class="additions">',
        "<h2>Help Center additions and remaining gaps</h2>",
        '<p>This section adds Help Center material and named gaps. It does not replace the steps above.</p>',
        '<details class="source-fold"><summary>How these labels are used</summary>',
        "<ul>",
        "<li><strong>Source-documented</strong> — written in the original Help Center. The last-edited date is given. That does not by itself prove the current QMAS UI.</li>",
        "<li><strong>Dev-verified</strong> — confirmed on qmas-dev.icw.io during guide work.</li>",
        "<li><strong>Gap</strong> — named as missing or too thin. Not current behaviour until checked on dev.</li>",
        "</ul><p>Reviewed screenshots remain 56 of 98. Forty-two inventory slots are still pending. Six supplementary images are not part of the 98. Unreviewed screenshots were not copied.</p></details>",
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


def asset_href(home: str, path: str) -> str:
    return path if home == "./" else f"{home}{path}"


def verification_sources_html(catalog) -> str:
    home = catalog["verification"]["help_center_home"]
    index = catalog["verification"]["user_guide_index"]
    return (
        "<p>Help Center home: "
        f'<a href="{html.escape(home["url"], quote=True)}">{html.escape(home["title"])}</a>'
        f' (last edited {html.escape(home["edited"])}). '
        "User Guide index: "
        f'<a href="{html.escape(index["url"], quote=True)}">{html.escape(index["title"])}</a>'
        f' (last edited {html.escape(index["edited"])}). '
        "Public icw-io addresses for individual articles were not verified, so those links use app.notion.com.</p>"
    )


def visible_lead(record) -> str:
    lead = record["lead"]
    prefix = f"{record['label']}."
    if lead.startswith(prefix):
        return lead[len(prefix):].lstrip()
    return lead


def verification_html(module, catalog) -> str:
    record = catalog["verification"]["modules"][module["slug"]]
    if record["articles"]:
        items = "".join(
            "<li>"
            f'<a href="{html.escape(article["url"], quote=True)}">{html.escape(article["title"])}</a>'
            f' (last edited {html.escape(article["edited"])}). {html.escape(article["covers"])}'
            "</li>"
            for article in record["articles"]
        )
        articles = f"<ul>{items}</ul>"
    else:
        articles = "<p>No Help Center article is the source of the steps on this page.</p>"
    return (
        f'<aside class="verify verify-{html.escape(record["status"])}">'
        f'<p><strong>{html.escape(record["label"])}.</strong> {html.escape(visible_lead(record))}</p>'
        '<details class="source-fold"><summary>Source and verification</summary>'
        f'<p>{html.escape(record["note"])}</p>'
        f"{articles}"
        f"{verification_sources_html(catalog)}"
        "</details></aside>\n"
    )


def verification_md(module, catalog) -> str:
    record = catalog["verification"]["modules"][module["slug"]]
    home = catalog["verification"]["help_center_home"]
    index = catalog["verification"]["user_guide_index"]
    lines = [
        "## Source and verification",
        "",
        f"**{record['label']}.** {visible_lead(record)}",
        "",
        record["note"],
        "",
    ]
    if record["articles"]:
        for article in record["articles"]:
            lines.append(
                f"- [{article['title']}]({article['url']}) (last edited {article['edited']}). {article['covers']}"
            )
        lines.append("")
    else:
        lines.append("No Help Center article is the source of the steps on this page.")
        lines.append("")
    lines.append(
        f"Help Center home: [{home['title']}]({home['url']}) (last edited {home['edited']}). "
        f"User Guide index: [{index['title']}]({index['url']}) (last edited {index['edited']}). "
        "Public icw-io addresses for individual articles were not verified, so those links use app.notion.com."
    )
    lines.append("")
    return "\n".join(lines)


def shell_header(home: str, catalog, current_slug: str | None) -> str:
    logo = catalog["logo"]
    published = catalog["source_site"]
    links = [
        f'<li><a href="{html.escape(home, quote=True)}"'
        + (' aria-current="page"' if current_slug == "home" else "")
        + ">Home</a></li>"
    ]
    for slug in catalog["order"]:
        record = catalog["verification"]["modules"][slug]
        href = asset_href(home, f"{slug}/")
        current = ' aria-current="page"' if slug == current_slug else ""
        links.append(
            f'<li><a href="{html.escape(href, quote=True)}"{current}>{html.escape(record["nav"])}</a></li>'
        )
    logo_note = html.escape(catalog["logo"]["note"])
    return f"""<a class="skip-link visually-hidden" href="#content">Skip to content</a>
<header class="site-header">
  <div class="header-inner">
    <a class="site-logo" href="{html.escape(home, quote=True)}">
      <img src="{html.escape(asset_href(home, logo["file"]), quote=True)}" alt="{html.escape(logo["alt"])}" width="{logo["width"]}" height="{logo["height"]}">
      <span>QMAS User Guide</span>
    </a>
    <nav class="site-nav" aria-label="Primary">
      <button class="menu-button" type="button" popovertarget="site-menu" popovertargetaction="toggle" aria-controls="site-menu">
        <svg aria-hidden="true" width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M1 3h14v1.5H1zm0 4.25h14v1.5H1zM1 11.5h14V13H1z"/></svg>
        <span>Guides</span>
      </button>
      <ul id="site-menu" class="site-menu" popover="auto">
        {''.join(links)}
      </ul>
    </nav>
  </div>
  <p class="edition"><span class="edition-draft">Updated working draft</span> <a href="{html.escape(published, quote=True)}">Existing published version</a></p>
</header>"""


def shell_footer(catalog) -> str:
    published = catalog["source_site"]
    logo = catalog["logo"]
    return (
        '<footer class="site-footer">'
        "<p>Updated working draft. This page is not deployed. "
        f'Existing published version: <a href="{html.escape(published, quote=True)}">{html.escape(published)}</a>.</p>'
        f"<p>{html.escape(logo['note'])}</p>"
        "</footer>"
    )


SHELL_SCRIPT = """
<script>
if (!Object.hasOwn(HTMLElement.prototype, "popover")) {
  var polyfill = document.createElement("script");
  polyfill.src = "https://unpkg.com/@oddbird/popover-polyfill@latest/dist/popover.min.js";
  document.head.appendChild(polyfill);
}
</script>
<script>
(function () {
  var header = document.querySelector(".site-header");
  var inner = header && header.querySelector(".header-inner");
  var menu = document.getElementById("site-menu");
  if (!header || !inner || !menu) return;
  var seen = false;
  var lastWidth = 0;
  function layout() {
    var width = inner.clientWidth;
    var grown = width > lastWidth + 0.5;
    var collapsed = !header.classList.contains("is-wide");
    lastWidth = width;
    if (collapsed && seen && !grown) return;
    seen = true;
    var open = typeof menu.showPopover === "function" && menu.matches(":popover-open");
    header.classList.add("is-measuring", "is-wide");
    menu.removeAttribute("popover");
    var fits = inner.scrollWidth <= inner.clientWidth;
    if (!fits) {
      header.classList.remove("is-wide");
      menu.setAttribute("popover", "auto");
      if (open) {
        try { menu.showPopover(); } catch (err) {}
      }
    }
    requestAnimationFrame(function () { header.classList.remove("is-measuring"); });
  }
  var observer = new ResizeObserver(layout);
  observer.observe(header);
  observer.observe(menu);
  layout();
})();
</script>
"""


def page(title: str, body: str, home: str, crumb: str | None, catalog, current_slug: str | None) -> str:
    if crumb:
        crumb_html = (
            '<nav class="crumb" aria-label="Breadcrumb"><ol>'
            f'<li><a href="{html.escape(home, quote=True)}">All guides</a></li>'
            f"<li><span aria-current=\"page\">{html.escape(crumb)}</span></li>"
            "</ol></nav>\n"
        )
    else:
        crumb_html = ""
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
{shell_header(home, catalog, current_slug)}
<main id="content" tabindex="-1">
{crumb_html}{body}
</main>
{shell_footer(catalog)}
{SHELL_SCRIPT}
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
    labels = {}
    app_for = {}
    for group in catalog["groups"]:
        slugs = []
        for item in group["items"]:
            labels.setdefault(item["slug"], item["label"])
            slugs.append(item["slug"])
        if group.get("app_href") and slugs:
            primary = slugs[0]
            if len(slugs) == 1 or primary in {"product-management", "supplier-management"}:
                app_for[primary] = group["app_href"]
    home_groups = [
        ("Getting Started", ["getting-started"]),
        ("Product & Compliance", ["product-management", "product-profile", "efiling", "ai-insight", "test-plan"]),
        ("Supplier & Factory", ["supplier-management", "factory-management"]),
        ("Testing & Inspection", ["product-testing", "qc-inspection", "internal-qc-inspection", "factory-audit"]),
        ("Documents", ["document-management", "document-review"]),
    ]
    grouped = [slug for _, slugs in home_groups for slug in slugs]
    if sorted(grouped) != sorted(module["slug"] for module in modules):
        raise SystemExit("home groups do not match the 14 modules")
    groups = []
    for heading, slugs in home_groups:
        cards = []
        for slug in slugs:
            module = next(entry for entry in modules if entry["slug"] == slug)
            record = catalog["verification"]["modules"][slug]
            badge = ""
            if record["status"] == "source-only":
                badge = '<span class="tag tag-warn">Source-only, not on the published site</span>'
            app = ""
            if slug in app_for:
                app = (
                    f'<a class="app-link" href="{html.escape(app_for[slug], quote=True)}">Open in QMAS</a>'
                )
            cards.append(
                "<li>"
                f'<a class="guide-card" href="{html.escape(slug, quote=True)}/">'
                f'<span class="guide-card-title">{html.escape(record["nav"])}</span>'
                f'<span class="guide-card-text">{html.escape(labels[slug])}</span>'
                f"{badge}</a>{app}</li>"
            )
        anchor = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
        groups.append(
            f'<section class="guide-group" aria-labelledby="{anchor}">'
            f'<h2 id="{anchor}">{html.escape(heading)}</h2>'
            f'<ul class="guide-cards" role="list">{"".join(cards)}</ul></section>\n'
        )
    published = catalog["source_site"]
    rows = []
    for module in modules:
        record = catalog["verification"]["modules"][module["slug"]]
        if record["articles"]:
            links = "<br>".join(
                f'<a href="{html.escape(article["url"], quote=True)}">{html.escape(article["title"])}</a>'
                f' ({html.escape(article["edited"])})'
                for article in record["articles"]
            )
        else:
            links = "No Help Center article for these steps"
        rows.append(
            "<tr>"
            f'<td><a href="{html.escape(module["slug"], quote=True)}/">{html.escape(module["title"])}</a></td>'
            f'<td>{html.escape(record["label"])}</td>'
            f"<td>{links}</td>"
            "</tr>"
        )
    help_home = catalog["verification"]["help_center_home"]
    guide_index = catalog["verification"]["user_guide_index"]
    related = []
    for item in catalog.get("related_resources", []):
        related.append(
            f'<a href="{html.escape(item["href"], quote=True)}">{html.escape(item["label"])}</a>. {html.escape(item["note"])}'
        )
    related_html = " ".join(related)
    body = f"""
<h1>QMAS User Guide</h1>
<p class="lede">Choose a module. These are the 14 existing guides.</p>
<p class="draft-notice">Working copy draft. Not deployed. Existing published version: <a href="{html.escape(published, quote=True)}">{html.escape(published)}</a>.</p>
{''.join(groups)}
<p class="related-line">Related: <a href="{html.escape(catalog["notion_working_hub"], quote=True)}">Notion working hub</a>. {related_html} <a href="combined/">Read all guides in one page</a>.</p>
<details class="source-fold">
<summary>Source and verification</summary>
<p>Working copy draft {html.escape(catalog["version"])}. Reviewed screenshots remain 56 of 98. Forty-two inventory slots are still pending. Six supplementary images are not part of the 98. Factory Audit and Test Plan have no screenshots and are not on the existing published site.</p>
<p>The original 12 modules keep their published steps. A reviewed screenshot means that part is current UI verified. Help Center text is marked on the module and is not the source of every step. Factory Audit and the standalone Test Plan are source-only and not dev-verified. Where a page is mixed, the create path can be current UI verified while a later quote or accept flow is still older Help Center wording.</p>
<p>Help Center home: <a href="{html.escape(help_home["url"], quote=True)}">{html.escape(help_home["title"])}</a> (last edited {html.escape(help_home["edited"])}). User Guide index: <a href="{html.escape(guide_index["url"], quote=True)}">{html.escape(guide_index["title"])}</a> (last edited {html.escape(guide_index["edited"])}). Public icw-io addresses for individual articles were not verified, so the table uses app.notion.com.</p>
<div class="table-wrap" tabindex="0" role="region" aria-label="Source and verification">
<table>
<caption class="visually-hidden">Source and verification for the 14 modules</caption>
<thead><tr><th scope="col">Module</th><th scope="col">Verification</th><th scope="col">Help Center article</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>
</div>
</details>
"""
    return page("QMAS User Guide (working copy draft)", body, "./", None, catalog, "home").replace(
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
        f"> Updated working draft {catalog['version']}. This file is not deployed. Existing published version: {catalog['source_site']}",
        "",
        verification_md(module, catalog).rstrip(),
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
        "Reviewed screenshots remain 56 of 98. Forty-two inventory slots are still pending. Six supplementary images are not part of the 98. Unreviewed screenshots were not copied.",
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
        f"> Updated working draft {catalog['version']}. This file is not deployed. Existing published version: {catalog['source_site']}",
        "",
        f"Notion working hub: {catalog['notion_working_hub']}",
        "",
    ]
    for item in catalog.get("related_resources", []):
        lines.append(f"{item['label']}: {item['href']}. {item['note']}")
        lines.append("")
    lines.extend([
        "## Contents",
        "",
    ])
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
            module["title"],
            catalog,
            module["slug"],
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
        catalog,
        None,
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
            catalog,
            module["slug"],
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
        + "".join(
            f"<p>{html.escape(item['label'])}: <a href=\"{html.escape(item['href'], quote=True)}\">{html.escape(item['href'])}</a>. {html.escape(item['note'])}</p>"
            for item in catalog.get("related_resources", [])
        )
    )
    (print_dir / "qmas-user-guide.html").write_text(
        page(catalog["title"], cover + "\n".join(combined_print_articles), "../../", None, catalog, None),
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
