# QMAS User Guide — working copy

Draft English copy of the published guide at <https://marconip2026.github.io/qmas-user-guide/>. It lives in this folder so the older guide at the repository root stays untouched. This is not a deployment.

Version: `2026-11-13-draft`

The public guide is https://marconip2026.github.io/qmas-user-guide/. This branch is a draft in `marconip2023/guidline` and is not that site.

The same `content/modules/*.json` files generate:

- the website (`index.html` and one folder per module)
- per-module Markdown and one combined Markdown file
- per-module PDFs and one combined PDF

Notion working hub for the 12 English module pages: <https://app.notion.com/p/4139c62c39fc8198ac49e172050cf65b>

## What is included

Fourteen modules. Twelve keep the published pages and 98 screenshot slots. Factory Audit and Test Plan are extra Help Center pages with no screenshots.

Help Center additions from 2026-11-13 are appended. They are marked source-documented, dev-verified, or gap. They do not replace earlier steps, captions, or reviewed images.

Reviewed inventory screenshots, 45 of 98. Fifty-three slots are still pending. The 13 Nov 2026 batch added 12 of those slots plus one Factory validation image that is not part of the 98. Those new files are 1280×800 desktop captures cropped to 1280×714. They are not high-resolution. Matching 1920 files were 1.5× upscales and were not used. The earlier 33 reviewed files were not replaced.

Reviewed replacement screenshots, 45 inventory files:

- Product Testing: all 9 published slots, including the refined order-details image
- Getting started: all 3 slots
- Product Management: 10 of 11 slots
- Product Profile: 11 slots from the first reviewed batch (Document, Shipping Detail, empty Compliance Data, the in-progress Test Data form, the empty Certificate Data form, and part of Quality Requirement)
- Document Management: list only
- Supplier Management: list, company overview, contact, and the Next validation state
- Factory Management: list, overview, scale, and contact
- Document Review: list, default Create Job form, and default Create Job for Supplier form

Supplementary, not one of the 98: `factory-management/required-validation.jpg` shows required Contact person, email type, and email address after **Next**, not Submit.

These slots were not captured. Each stays an explicit placeholder and is not a picture of the missing state:

- `product-management/img/08-product-added.jpg` — needs a real product create
- `product-profile/img/08-test-data-filled.jpg` and `09-test-data-saved.jpg` — need a real saved Test Data record
- `product-profile/img/22-requirement-list.jpg` — needs a real Apply Template

Every other slot keeps the written step and shows **Image pending privacy review**. Published screenshot files are not copied, embedded, or linked.

The Product Profile captions follow the reviewed captures: Shipping Detail is 0.00 / N/A, Compliance Data is the empty state, the Test Data shot is an in-progress form (Export Market Africa and + Add '[UAT TEST]'), Quality Requirement shows one redacted row rather than an empty tab, and Add Requirement has Type and Name empty with Mandatory checked. Later profile shots are still to come.

## Dev-verified text updates (9 Nov 2026)

These are the only instruction changes. They were confirmed on `qmas-dev.icw.io` while the replacement screenshots were captured. Broader planning notes are not written into the guide.

- Settings opens from the account avatar. The menu includes Logout. The old “gear icon” wording is removed, including the eFiling FAQ that pointed at it.
- Home shows TicMate’s five workflow shortcuts in the order on the dev screen: AI Assessment, AI Insight, CPSC eFiling, Product Testing, Document Review.
- The Product Management list documents the verified filters: Product Category, Customer Product Category, Product Number, Status, Created By, Team, sort, and Reset. The reviewed list screenshot has those filters and no data rows.
- The supplier card body in `05-supplier-shipping.jpg` is intentionally blank.
- The product profile left menu includes QR Code. The Document tab also has Sort and Reset. This copy does not add a QR Code procedure.
- Related Product shows Unlink on the reviewed screenshot, so the create-product step names that control.
- Factory (optional) and Additional Info were already in the published create-product steps and match the dev screenshot.
- Product Profile wording next to the first reviewed batch matches those captures. It does not treat the empty Compliance Data tab as a saved table, and it does not say data was removed.

Attention and Business Overview stay in the Home steps. The reviewed Home crop shows the workflow shortcuts, not those sections.

## Build and check

From this folder:

```bash
python3 scripts/import_published_source.py --source /path/to/qmas-user-guide --images /path/to/reviewed-root
python3 scripts/build.py
python3 -m unittest tests/test_exports.py
python3 scripts/validate.py
```

`import_published_source.py` reads published text only. It never copies screenshot files from the source tree. Re-running it reapplies the dev-verified edits. `--images` must be a folder of `<module>/img/<file>.jpg` reviewed replacements.

`build.py` writes the site, `export/markdown/`, `export/print/`, and `export/pdf/`. Use `--skip-pdf` to rebuild text only.

`validate.py` extracts PDF text with `pdftotext`, counts embedded images with `pdfimages`, and checks that rendered page edges are not clipped. It needs `google-chrome`, `poppler-utils`, and `pillow`.

Open the site from this folder:

```bash
python3 -m http.server 8765
```

Then open `http://127.0.0.1:8765/`.

## Layout

- `content/modules/` — canonical guide text
- `content/published-text-blocks.json` — text extracted from the published pages, used by tests
- `content/reviewed-images.json` — sha256 allowlist for replacement screenshots
- `assets/reviewed/` — the only screenshot files in this working copy
- `assets/site.css` — page and print styles, inlined by the build
- `export/markdown/` — per-module and combined Markdown, with reviewed images under `images/`
- `export/pdf/` — per-module and combined PDFs
