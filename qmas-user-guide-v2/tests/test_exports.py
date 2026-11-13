"""Text-level checks for the working copy. Run after scripts/build.py."""

from __future__ import annotations

import json
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
        self.assertEqual(len(inventory), 50)
        self.assertEqual(set(supplementary), {
            ("factory-management", "required-validation.jpg"),
            ("qc-inspection", "supplemental-step1-requirement-blank.jpg"),
            ("qc-inspection", "supplemental-3rd-party-tab.jpg"),
            ("qc-inspection", "supplemental-draft-tab.jpg"),
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
            self.assertNotIn("github.io", text)
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
        self.assertNotIn("github.io", combined)

    def test_only_allowlisted_rasters_are_stored(self):
        allowed = {
            ROOT / "assets" / "reviewed" / slug / filename
            for slug, filename in self.reviewed
        }
        allowed.update(
            ROOT / "export" / "markdown" / "images" / slug / filename
            for slug, filename in self.reviewed
        )
        found = []
        for path in ROOT.rglob("*"):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
                found.append(path)
                self.assertIn(path.resolve(), {item.resolve() for item in allowed})
        self.assertEqual(len(found), 108)

    def test_site_pages_exist_without_remote_screenshots(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn(self.catalog["notion_working_hub"], index)
        self.assertIn("Working copy draft", index)
        for module in self.modules:
            page = (ROOT / module["slug"] / "index.html").read_text(encoding="utf-8")
            self.assertIn(module["title"], page)
            self.assertNotIn("github.io", page)
            self.assertNotIn("gear icon", plain(page))
            self.assertIn('lang="en"', page)
        for block in self.blocks["product-testing"]:
            if block in SECTION_HEADINGS or "←" in block:
                continue
            self.assertIn(block, module_plain(self.by_slug["product-testing"], self.titles))


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
