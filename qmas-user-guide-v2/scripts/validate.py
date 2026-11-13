"""Check PDF text, embedded images, and page edges. Writes a validation report.

Usage:
  python3 scripts/validate.py
  python3 scripts/validate.py --artifacts /opt/cursor/artifacts
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build import load  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "export" / "pdf"


def run(command: list[str]) -> str:
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, text=True)
    return result.stdout


def pdf_text(path: Path) -> str:
    return run(["pdftotext", "-layout", str(path), "-"])


def pdf_pages(path: Path) -> int:
    info = run(["pdfinfo", str(path)])
    for line in info.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    raise RuntimeError(f"no page count for {path}")


def embedded_images(path: Path) -> int:
    listing = run(["pdfimages", "-list", str(path)])
    rows = [line for line in listing.splitlines() if line.strip() and line.strip()[0].isdigit()]
    return len(rows)


def edge_ink(png: Path) -> float:
    from PIL import Image

    image = Image.open(png).convert("RGB")
    width, height = image.size
    pixels = image.load()
    ink = 0
    seen = 0
    margin = 8
    for y in range(height):
        for x in range(width):
            if x < margin or y < margin or x >= width - margin or y >= height - margin:
                seen += 1
                red, green, blue = pixels[x, y]
                if red < 245 or green < 245 or blue < 245:
                    ink += 1
    return ink / seen if seen else 1


def copy_tree(source: Path, target: Path):
    if target.exists():
        shutil.rmtree(target)
    for path in source.rglob("*"):
        dest = target / path.relative_to(source)
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", type=Path, default=Path("/opt/cursor/artifacts"))
    args = parser.parse_args()
    catalog, modules, reviewed, _titles = load()
    problems = []
    lines = [
        "# QMAS working-copy validation",
        "",
        f"Version: {catalog['version']}",
        f"Modules: {len(modules)}",
        "Screenshot slots: 98",
        f"Reviewed inventory files: {sum(1 for record in reviewed.values() if record.get('counts_toward_98', True))}",
        f"Supplementary files not in the 98: {sum(1 for record in reviewed.values() if not record.get('counts_toward_98', True))}",
        "Pending slots keep their written steps and use an explicit placeholder.",
        "This batch is 1280×800 native desktop captures cropped to 1280×714. They are not high-resolution. 1920 files were 1.5× upscales and were not used.",
        "Not captured, and not treated as pictures of those states: Product Management `08-product-added.jpg`; Product Profile `08-test-data-filled.jpg`, `09-test-data-saved.jpg`, and `22-requirement-list.jpg`.",
        "",
        "## PDFs",
        "",
    ]
    expected_images = {}
    for module in modules:
        count = 0
        for step in module["steps"]:
            for block in step["body"]:
                if isinstance(block, dict) and "img" in block and (module["slug"], block["img"]) in reviewed:
                    count += 1
        for tip in module.get("tips") or []:
            if isinstance(tip, dict) and "img" in tip and (module["slug"], tip["img"]) in reviewed:
                count += 1
        expected_images[module["slug"]] = count
    slot_counts = {}
    for module in modules:
        slot_counts[module["slug"]] = sum(
            1
            for step in module["steps"]
            for block in step["body"]
            if isinstance(block, dict) and "img" in block
        ) + sum(1 for tip in module.get("tips") or [] if isinstance(tip, dict) and "img" in tip)
    expected_images["qmas-user-guide"] = len(reviewed)

    preview_dir = args.artifacts / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_targets = {
        "product-testing": [1, 2],
        "getting-started": [1],
        "product-management": [1, 2],
        "qmas-user-guide": [1],
    }
    for slug, expected in expected_images.items():
        path = PDF_DIR / f"{slug}.pdf"
        if not path.exists():
            problems.append(f"missing {path.name}")
            continue
        text = pdf_text(path)
        pages = pdf_pages(path)
        images = embedded_images(path)
        if pages < 1:
            problems.append(f"{slug} has no pages")
        if len(text.strip()) < 400:
            problems.append(f"{slug} extracted text is too short")
        if images != expected:
            problems.append(f"{slug} embedded images {images}, expected {expected}")
        if slug == "product-testing" and "Image pending privacy review" in text:
            problems.append("product-testing PDF still has a pending placeholder")
        if slug == "getting-started" and "Image pending privacy review" in text:
            problems.append("getting-started PDF still has a pending placeholder")
        if slug == "product-management" and "Not captured" not in text:
            problems.append("product-management PDF missing the not-captured notice")
        if slug not in {"product-testing", "getting-started", "product-management", "qmas-user-guide"}:
            slots = slot_counts.get(slug, 0)
            if slots == 0:
                if "Screenshot slots: none" not in text and "Source-documented only" not in text:
                    problems.append(f"{slug} PDF should say it has no screenshots")
            elif "Image pending privacy review" not in text and slots != expected:
                problems.append(f"{slug} PDF missing pending placeholder text")
        if slug == "qmas-user-guide":
            normalized = re.sub(r"\s+", " ", text)
            for module in modules:
                if module["title"] not in normalized:
                    problems.append(f"combined PDF missing title {module['title']}")
        if "gear icon" in text:
            problems.append(f"{slug} PDF still says gear icon")
        lines.append(f"- `{path.name}`: {pages} pages, {images} embedded images, {len(text)} extracted characters")
        if slug in preview_targets:
            for page in preview_targets[slug]:
                if page > pages:
                    continue
                prefix = preview_dir / f"preview_{slug}_p{page}"
                subprocess.run(
                    ["pdftoppm", "-png", "-r", "72", "-f", str(page), "-l", str(page), str(path), str(prefix)],
                    check=True,
                )
                pngs = list(preview_dir.glob(f"preview_{slug}_p{page}*.png"))
                if not pngs:
                    problems.append(f"no preview for {slug} page {page}")
                    continue
                ratio = edge_ink(pngs[0])
                if ratio > 0.02:
                    problems.append(f"{slug} page {page} edge ink {ratio:.3f} looks clipped")
                lines.append(f"  - preview `{pngs[0].name}`, edge ink {ratio:.4f}")

    lines.extend(["", "## Result", ""])
    if problems:
        lines.append("Failed:")
        lines.extend(f"- {problem}" for problem in problems)
    else:
        lines.append("Passed: searchable text, embedded-image counts, and page-edge checks.")
    report = "\n".join(lines) + "\n"
    args.artifacts.mkdir(parents=True, exist_ok=True)
    (args.artifacts / "validation-report.md").write_text(report, encoding="utf-8")
    (ROOT / "export" / "validation-report.md").write_text(report, encoding="utf-8")
    copy_tree(ROOT / "export" / "markdown", args.artifacts / "markdown")
    copy_tree(PDF_DIR, args.artifacts / "pdf")
    print(report)
    if problems:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
