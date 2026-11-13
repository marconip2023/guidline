"""Text-level checks for the working copy. Run after scripts/build.py."""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build import load, render_md  # noqa: E402
from textutil import EMAIL_RE, module_plain, plain  # noqa: E402

CONTENT = ROOT / "content"
SECTION_HEADINGS = {"Overview", "Step-by-step", "Tips", "FAQ"}
SKIP_EXACT = {
    ("getting-started", "The top bar has analytics, messages, notifications, settings, help and credits."),
    ("getting-started", "TicMate asks “What would you like to do today?” and lists quick workflows:"),
    ("getting-started", "QMAS dev, 4 Nov 2026"),
    ("product-management", "QMAS dev, 4 Nov 2026"),
}
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
    if block in SECTION_HEADINGS:
        return True
    if slug == "product-profile" and block in PROFILE_SUPERSEDED:
        return True
    if "gear icon" in block or "github.io" in block:
        return True
    return (slug, block) in SKIP_EXACT


class GuideContentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.modules, cls.reviewed, cls.titles = load()
        cls.by_slug = {module["slug"]: module for module in cls.modules}
        cls.blocks = json.loads((CONTENT / "published-text-blocks.json").read_text(encoding="utf-8"))

    def test_twelve_modules_and_ninety_eight_slots(self):
        self.assertEqual(len(self.modules), 14)
        slots = [block for module in self.modules for block in images(module) if block.get("counts_toward_98", True)]
        self.assertEqual(len(slots), 98)
        inventory = [key for key, record in self.reviewed.items() if record.get("counts_toward_98", True)]
        supplementary = [key for key, record in self.reviewed.items() if not record.get("counts_toward_98", True)]
        self.assertEqual(len(inventory), 56)
        self.assertEqual(set(supplementary), {
            ("factory-management", "required-validation.jpg"),
            ("factory-management", "supplemental-profile-certificate.jpg"),
            ("qc-inspection", "supplemental-step1-requirement-blank.jpg"),
            ("qc-inspection", "supplemental-3rd-party-tab.jpg"),
            ("qc-inspection", "supplemental-draft-tab.jpg"),
            ("supplier-management", "supplemental-profile-certificate.jpg"),
        })

    def test_published_text_is_still_present(self):
        missing = []
        for slug, blocks in self.blocks.items():
            haystack = module_plain(self.by_slug[slug], self.titles)
            for block in blocks:
                if skipped(slug, block):
                    continue
                if block not in haystack:
                    missing.append(f"{slug}: {block[:160]}")
        self.assertEqual(missing, [])

    def test_dev_verified_facts_are_in_the_guide(self):
        started = module_plain(self.by_slug["getting-started"], self.titles)
        products = module_plain(self.by_slug["product-management"], self.titles)
        profile = module_plain(self.by_slug["product-profile"], self.titles)
        efiling = module_plain(self.by_slug["efiling"], self.titles)
        self.assertIn("avatar (account control)", started)
        self.assertIn("I’m TicMate. What would you like to do today?", started)
        self.assertIn("Logout", started)
        self.assertIn("Signs you out of QMAS.", started)
        self.assertLess(
            started.index("CPSC eFiling"),
            started.index("Request product testing with your lab partner"),
        )
        self.assertIn("Product Category", products)
        self.assertIn("Customer Product Category", products)
        self.assertIn("No data rows are shown.", products)
        self.assertIn("intentionally blank", products)
        self.assertIn("not confirmation of a completed create", products)
        self.assertIn("Unlink", products)
        self.assertIn("QR Code", products)
        self.assertIn("QR Code", profile)
        self.assertIn("Sort and Reset", profile)
        self.assertIn("not an empty tab", profile.lower())
        self.assertIn("Type and Name empty", profile)
        self.assertIn("0.00 and N/A", profile)
        self.assertIn("+ Add '[UAT TEST]'", profile)
        self.assertIn("There is no data here", profile)
        self.assertNotIn("Empty Quality Requirement tab", profile)
        self.assertNotIn("Saved test data.", profile)
        self.assertNotIn("Search legislation and test items by keyword.", profile)
        self.assertNotIn(("product-profile", "08-test-data-filled.jpg"), self.reviewed)
        self.assertNotIn(("product-profile", "09-test-data-saved.jpg"), self.reviewed)
        self.assertNotIn(("product-profile", "22-requirement-list.jpg"), self.reviewed)
        self.assertEqual(self.by_slug["factory-audit"]["confidence"], "source-documented")
        self.assertEqual(self.by_slug["test-plan"]["confidence"], "source-documented")
        self.assertEqual(list(images(self.by_slug["factory-audit"])), [])
        self.assertEqual(list(images(self.by_slug["test-plan"])), [])
        audit = module_plain(self.by_slug["factory-audit"], self.titles)
        plan = module_plain(self.by_slug["test-plan"], self.titles)
        self.assertIn("Create Factory Audit Order", audit)
        self.assertIn("Source-documented only", audit)
        self.assertIn("TEST PLAN", plan)
        self.assertIn("Test Plan (AI)", plan)
        self.assertIn("avatar / account control", efiling)
        for module in self.modules:
            self.assertNotIn("gear icon", module_plain(module, self.titles))

    def test_not_captured_slot_has_no_file(self):
        self.assertNotIn(("product-management", "08-product-added.jpg"), self.reviewed)
        self.assertFalse((ROOT / "assets" / "reviewed" / "product-management" / "08-product-added.jpg").exists())

    def test_markdown_exports_match_the_source_and_hide_private_images(self):
        markdown = ROOT / "export" / "markdown"
        self.assertTrue((markdown / "qmas-user-guide.md").exists(), "run scripts/build.py first")
        for module in self.modules:
            path = markdown / f"{module['slug']}.md"
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text, render_md(module, self.reviewed, self.catalog, self.titles))
            published = "https://marconip2026.github.io/qmas-user-guide/"
            self.assertIn("Existing published version", text)
            self.assertIn(published, text)
            self.assertEqual(
                [url for url in __import__("re").findall(r"https://[^)\s]+", text) if "github.io" in url],
                [published],
            )
            self.assertNotIn("gear icon", text)
            self.assertNotIn("← All guides", text)
            self.assertNotIn("Skip to content", text)
            self.assertIsNone(EMAIL_RE.search(text))
            for block in images(module):
                filename = block["img"]
                if (module["slug"], filename) in self.reviewed:
                    self.assertIn(f"images/{module['slug']}/{filename}", text)
                    self.assertNotIn(f"**Image pending privacy review:** `{filename}`", text)
                elif block.get("availability") == "not-captured":
                    self.assertIn("Not captured", text)
                    self.assertNotIn(f"](images/{module['slug']}/{filename})", text)
                else:
                    self.assertIn(f"**Image pending privacy review:** `{filename}`", text)
                    self.assertNotIn(f"](images/{module['slug']}/{filename})", text)
        combined = (markdown / "qmas-user-guide.md").read_text(encoding="utf-8")
        for module in self.modules:
            self.assertIn(module["title"], combined)
        self.assertIn(self.catalog["notion_working_hub"], combined)
        published = "https://marconip2026.github.io/qmas-user-guide/"
        self.assertIn(published, combined)
        self.assertIn("Existing published version", combined)

    def test_only_allowlisted_rasters_are_stored(self):
        allowed = {
            ROOT / "assets" / "reviewed" / slug / filename
            for slug, filename in self.reviewed
        }
        allowed.update(
            ROOT / "export" / "markdown" / "images" / slug / filename
            for slug, filename in self.reviewed
        )
        allowed.add(ROOT / "assets" / "brand" / "qmas-logo.png")
        found = []
        for path in ROOT.rglob("*"):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                found.append(path)
                self.assertIn(path.resolve(), {item.resolve() for item in allowed})
        self.assertEqual(len(found), 125)

    def test_site_pages_exist_without_remote_screenshots(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(self.catalog["notion_working_hub"], index)
        self.assertIn("Working copy draft", index)
        self.assertIn("Updated working draft", index)
        published = "https://marconip2026.github.io/qmas-user-guide/"
        pages = [index]
        for module in self.modules:
            page = (ROOT / module["slug"] / "index.html").read_text(encoding="utf-8")
            pages.append(page)
            self.assertIn(module["title"], page)
            self.assertIn("Existing published version", page)
            self.assertIn(published, page)
            self.assertNotIn("gear icon", plain(page))
            self.assertIn('lang="en"', page)
            self.assertIn('alt="QMAS"', page)
            self.assertIn('width="60"', page)
            self.assertIn('height="24"', page)
            record = self.catalog["verification"]["modules"][module["slug"]]
            self.assertIn(record["label"], page)
            self.assertIn("Source and verification", page)
        self.assertIn("Source-only, not dev-verified", (ROOT / "factory-audit" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("Source-only, not dev-verified", (ROOT / "test-plan" / "index.html").read_text(encoding="utf-8"))
        testing = (ROOT / "product-testing" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Mixed.", testing)
        self.assertIn("Preliminary Accept", testing)
        self.assertIn("Final Quote", testing)
        self.assertLess(testing.index("<h1>"), testing.index("Mixed."))
        self.assertLess(testing.index("Mixed."), testing.index('aria-label="On this page"'))
        started = (ROOT / "getting-started" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Mixed.", started)
        self.assertIn("2024-04-02 15:23:02 HKT", started)
        self.assertIn("2026-11-04 11:18:27 HKT", testing)
        for page in pages:
            public_children = [
                url for url in re.findall(r"https://icw-io\.notion\.site/[^\"'\s<]+", page)
                if "QMAS-Help-Center-5cd9414da2474d16a7c405a3542fe4af" not in url
            ]
            self.assertEqual(public_children, [])
        for block in self.blocks["product-testing"]:
            if block in SECTION_HEADINGS or "←" in block:
                continue
            self.assertIn(block, module_plain(self.by_slug["product-testing"], self.titles))

    def test_internal_links_logo_and_responsive_header(self):
        import re
        from urllib.parse import unquote, urlparse

        css = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
        self.assertIn(".site-header.is-wide", css)
        self.assertIn("--heading: #111827", css)
        self.assertIn("h1 { color: var(--heading);", css)
        self.assertIn(".guide-card-title { color: var(--heading);", css)
        self.assertIn("a { color: var(--link);", css)
        self.assertGreaterEqual(_contrast("#111827", "#ffffff"), 7)
        self.assertGreaterEqual(_contrast("#1f2937", "#f7faff"), 7)
        self.assertGreaterEqual(_contrast("#4b5563", "#ffffff"), 4.5)
        self.assertGreaterEqual(_contrast("#0041b8", "#ffffff"), 4.5)
        self.assertIn("anchor(--menu-button bottom)", css)
        self.assertIn("inset-block-start: 4.75rem", css)
        self.assertIn("min-block-size: 44px", css)
        self.assertIn("@media (forced-colors: active)", css)
        pages = [ROOT / "index.html", ROOT / "combined" / "index.html"]
        pages.extend(ROOT / module["slug"] / "index.html" for module in self.modules)
        href_re = re.compile(r"""(?:href|src)=["']([^"']+)["']""")
        for path in pages:
            text = path.read_text(encoding="utf-8")
            self.assertIn('aria-label="Primary"', text)
            self.assertIn('popover="auto"', text)
            self.assertIn('popovertarget="site-menu"', text)
            self.assertIn('alt="QMAS"', text)
            self.assertIn("assets/brand/qmas-logo.png", text)
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        main = home.split("<main", 1)[1]
        self.assertLess(main.index("guide-card"), main.index('class="source-fold"'))
        self.assertEqual(home.count('class="guide-card"'), 14)
        for heading in (
            "Getting Started",
            "Product &amp; Compliance",
            "Supplier &amp; Factory",
            "Testing &amp; Inspection",
            "Documents",
        ):
            self.assertIn(heading, home)
        self.assertIn("QMAS Chatbot", home)
        self.assertIn("https://workflow-dev.icw.io/chat/QDSPY8f58691bu1P", home)
        self.assertIn("QMAS Chatbot 2.0", home)
        self.assertNotIn("QMAS Chatbot 3.0", home)
        self.assertIn("Source-only, not on the published site", home)
        for path in pages:
            text = path.read_text(encoding="utf-8")
            for raw in href_re.findall(text):
                if raw.startswith(("https://", "http://", "mailto:")):
                    self.assertTrue(raw.startswith("https://"), raw)
                    continue
                target, _, fragment = raw.partition("#")
                if not target:
                    self.assertIn(f'id="{fragment}"', text)
                    continue
                resolved = (path.parent / unquote(urlparse(target).path)).resolve()
                self.assertTrue(
                    resolved.exists() or (resolved / "index.html").exists(),
                    f"{path.name} -> {raw}",
                )


def _channel(value: str) -> float:
    number = int(value, 16) / 255
    return number / 12.92 if number <= 0.04045 else ((number + 0.055) / 1.055) ** 2.4


def _contrast(foreground: str, background: str) -> float:
    def luminance(hex_color: str) -> float:
        red, green, blue = hex_color[1:3], hex_color[3:5], hex_color[5:7]
        return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)

    lighter = max(luminance(foreground), luminance(background))
    darker = min(luminance(foreground), luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def images(module):
    for step in module["steps"]:
        for block in step["body"]:
            if isinstance(block, dict) and "img" in block:
                yield block
    for tip in module.get("tips") or []:
        if isinstance(tip, dict) and "img" in tip:
            yield tip


if __name__ == "__main__":
    unittest.main()
