"""Apply only the 9 Nov 2026 dev-verified corrections.

These edits are limited to facts confirmed while capturing the getting-started
and product-management screenshots. Broader gap-analysis items are not applied.
"""

from __future__ import annotations


def _replace(value: str, old: str, new: str, where: str) -> str:
    if old not in value:
        raise SystemExit(f"dev-verified replacement missed in {where}: {old}")
    return value.replace(old, new, 1)


def _walk_strings(value, old: str, new: str, where: str):
    if isinstance(value, str):
        if old not in value:
            return value, False
        return _replace(value, old, new, where), True
    if isinstance(value, list):
        found = False
        updated = []
        for item in value:
            item, hit = _walk_strings(item, old, new, where)
            found = found or hit
            updated.append(item)
        return updated, found
    if isinstance(value, dict):
        found = False
        updated = {}
        for key, item in value.items():
            item, hit = _walk_strings(item, old, new, where)
            found = found or hit
            updated[key] = item
        return updated, found
    return value, False


def _replace_in(module: dict, old: str, new: str):
    updated, found = _walk_strings(module, old, new, module.get("slug", "?"))
    if not found:
        raise SystemExit(f"dev-verified replacement missed in {module.get('slug', '?')}: {old}")
    module.clear()
    module.update(updated)


def _set_meta(module: dict, key: str, value: str):
    for pair in module["meta"]:
        if pair[0] == key:
            pair[1] = value
            return
    raise SystemExit(f"{module['slug']} has no meta key {key}")


def apply_dev_verified(modules: dict[str, dict]) -> None:
    started = modules["getting-started"]
    _replace_in(
        started,
        "The **top bar** has analytics, messages, notifications, settings, help and credits.",
        "The **top bar** has analytics, messages, notifications, the account avatar, help and credits.",
    )
    _replace_in(
        started,
        "**Settings** (gear icon) opens Company Profile, Password, Languages, Account Management and Assign TicMart Job.",
        "**Settings** opens from the **avatar** (account control) in the top bar. The menu includes Company Profile, Password, Languages, Account Management, Assign TicMart Job and Logout.",
    )
    _replace_in(
        started,
        "**TicMate** asks “What would you like to do today?” and lists quick workflows:",
        "**TicMate** says “I’m TicMate. What would you like to do today?” and lists these workflow shortcuts:",
    )
    home = started["steps"][0]["body"]
    workflows = home[1]["list"]
    assessment, insight, testing, review, efiling = workflows
    home[1]["list"] = [assessment, insight, efiling, testing, review]
    _replace_in(started, "Click the gear icon in the top bar:", "Click your **avatar** (account control) in the top bar:")
    table = started["steps"][1]["body"][1]["table"]
    if not any(row[0] == "Logout" for row in table):
        table.append(["Logout", "Signs you out of QMAS."])
    _replace_in(
        started,
        "Click the gear icon in the top bar, then Languages.",
        "Click your avatar (account control) in the top bar, then Languages.",
    )
    _replace_in(
        started,
        "Click the gear icon in the top bar, then Password.",
        "Click your avatar (account control) in the top bar, then Password.",
    )
    _replace_in(
        started,
        "Click the gear icon, then Company Profile (https://qmas.icw.io/company-profile).",
        "Click your avatar (account control), then Company Profile (https://qmas.icw.io/company-profile).",
    )
    _set_meta(started, "Checked against", "QMAS dev, 9 Nov 2026")
    for block in started["steps"][0]["body"]:
        if isinstance(block, dict) and block.get("img") == "01-home.jpg":
            block["caption_note"] = (
                "This reviewed screenshot shows the TicMate workflow shortcuts. "
                "Attention and Business Overview are described in the steps and are not in this crop."
            )
    for block in started["steps"][1]["body"]:
        if isinstance(block, dict) and block.get("img") == "02-settings-menu.jpg":
            block["caption_note"] = (
                "Menu opened from the account avatar: Company Profile, Password, Languages, "
                "Account Management, Assign TicMart Job and Logout."
            )

    products = modules["product-management"]
    step_open = products["steps"][0]["body"]
    filter_text = (
        "Filter the list with **Product Category**, **Customer Product Category**, **Product Number**, "
        "**Status**, **Created By** and **Team**. **Sort by Date modified** changes the order. "
        "**Reset** clears the filters."
    )
    if filter_text not in step_open:
        step_open.insert(1, filter_text)
    for block in step_open:
        if isinstance(block, dict) and block.get("img") == "01-list.jpg":
            block["caption_note"] = (
                "Reviewed screenshot of the list filters and column headers. No data rows are shown."
            )
    for block in products["steps"][2]["body"]:
        if isinstance(block, dict) and block.get("img") == "05-supplier-shipping.jpg":
            block["caption_note"] = (
                "The supplier card body in this screenshot is intentionally blank. "
                "Change Supplier and Edit this profile remain visible. "
                "The selected test supplier is shown on the Select supplier screenshot."
            )
    done = products["steps"][5]["body"]
    missing = (
        "The screenshot of that new row was not captured, because it would require creating a real product. "
        "The placeholder is not a picture of a finished create."
    )
    if missing not in done:
        done.insert(1, missing)
    for block in done:
        if isinstance(block, dict) and block.get("img") == "08-product-added.jpg":
            block["availability"] = "not-captured"
            block["pending_note"] = (
                "Not captured. A real product was not created for this screenshot, "
                "so this placeholder is not confirmation of a completed create."
            )
        if isinstance(block, dict) and block.get("img") == "09-product-profile.jpg":
            block["caption_note"] = (
                "Left menu includes Document, Shipping Detail, Compliance Data, Quality Requirement, "
                "AI Risk Screening, CPSC eFiling, Packaging Detail and QR Code. "
                "The Document tab shows New Folder, Upload, All, Archived, Type, Source, Checked, Sort and Reset."
            )
    qr_line = "The left menu also includes **QR Code**."
    if qr_line not in done:
        inserted = False
        for index, block in enumerate(done):
            if isinstance(block, str) and "Packaging Detail" in block:
                done.insert(index + 1, qr_line)
                inserted = True
                break
        if not inserted:
            raise SystemExit("product profile sentence missing")
    related = products["steps"][4]["body"]
    unlink = " **Unlink** removes a product from this step."
    if isinstance(related[0], str) and "Unlink" not in related[0]:
        related[0] = related[0].rstrip(".") + "." + unlink
    _set_meta(products, "Checked against", "QMAS dev, 9 Nov 2026")

    profile = modules["product-profile"]
    _replace_in(
        profile,
        "and search with **Search Files**.",
        "and search with **Search Files**. **Sort** and **Reset** sit with those filters.",
    )
    _replace_in(
        profile,
        "Document · Shipping Detail · Compliance Data · Quality Requirement · AI Risk Screening · CPSC eFiling · Packaging Detail",
        "Document · Shipping Detail · Compliance Data · Quality Requirement · AI Risk Screening · CPSC eFiling · Packaging Detail · QR Code",
    )
    if not any(item.startswith("**QR Code**") for item in profile["overview"]):
        profile["overview"].append("**QR Code** is also in the left menu. This guide does not yet describe that screen.")
    _replace_in(
        profile,
        "Create and edit a product: https://marconip2026.github.io/qmas-user-guide/product-management/",
        "Create and edit a product: [[guide:product-management|Product Management — Create and Edit a Product]]",
    )
    _replace_in(
        profile,
        "The pop-up and results are explained in the AI Insight guide: https://marconip2026.github.io/qmas-user-guide/ai-insight/",
        "The pop-up and results are explained in the [[guide:ai-insight|AI Insight]] guide.",
    )
    _replace_in(
        profile,
        "The full flow is in the eFiling guide: https://marconip2026.github.io/qmas-user-guide/efiling/",
        "The full flow is in the [[guide:efiling|eFiling]] guide.",
    )

    _replace_in(
        modules["efiling"],
        "Settings (gear icon) → Company Profile → CPSC eFiling - Certifier ID.",
        "Settings (avatar / account control) → Company Profile → CPSC eFiling - Certifier ID.",
    )
    _replace_in(
        modules["internal-qc-inspection"],
        "See https://marconip2026.github.io/qmas-user-guide/qc-inspection/ for screenshots.",
        "See the [[guide:qc-inspection|QC Inspection]] guide for those steps.",
    )
    _apply_profile_batch1(modules["product-profile"])


def _image(module: dict, filename: str) -> dict:
    for step in module["steps"]:
        for block in step["body"]:
            if isinstance(block, dict) and block.get("img") == filename:
                return block
    raise SystemExit(f"{module.get('slug')} missing image {filename}")


def _before_image(module: dict, filename: str, text: str):
    for step in module["steps"]:
        body = step["body"]
        for index, block in enumerate(body):
            if isinstance(block, dict) and block.get("img") == filename:
                if text not in body:
                    body.insert(index, text)
                return
    raise SystemExit(f"{module.get('slug')} missing image {filename}")


def _apply_profile_batch1(profile: dict):
    """Caption and nearby wording for the 9 Nov 2026 Product Profile batch.

    Describes only the 11 reviewed captures. 08, 09 and 22 stay uncaptured.
    """
    document = _image(profile, "01-document.jpg")
    document["caption"] = "Document tab with one UAT sample PDF and the filter controls."
    document["alt"] = document["caption"]
    document["caption_note"] = (
        "All (1), New Folder, Upload, Type, Source, Checked, Sort and Reset are visible. "
        "The file is a UAT sample PDF marked Test Report. Source and the date columns on that row are empty."
    )

    toolbar = _image(profile, "02-document-toolbar.jpg")
    toolbar["caption_note"] = (
        "The selection toolbar shows Set Data, Set Dates & Reminder, Archive, Download, Share, "
        "Rename, Edit Type, Move and Remove for the same UAT sample file."
    )

    _replace_in(
        profile,
        "Shows the length, width, height, gross and net weight, quantity and barcode for the **Selling Unit**, **Inner Carton** and **Outer Carton**. To change them, click **⋮** next to the product name → **Edit product** and update **Shipping Information**.",
        "Shows the length, width, height, gross and net weight, quantity and barcode for the **Selling Unit**, **Inner Carton** and **Outer Carton**. To change them, click **⋮** next to the product name → **Edit product** and update **Shipping Information**. The reviewed screenshot shows 0.00 and N/A in those fields, not filled shipping values.",
    )
    shipping = _image(profile, "04-shipping-detail.jpg")
    shipping["caption"] = "Shipping Detail tab — empty values (0.00 / N/A)."
    shipping["alt"] = "Shipping Detail tab with 0.00 measurements and N/A barcodes for Selling Unit, Inner Carton and Outer Carton."

    compliance = _image(profile, "05-compliance-data.jpg")
    compliance["caption_note"] = (
        "Test Data, Certificate Data and Other each show 0 and “There is no data here.”, with Add Data. "
        "This is the captured empty state."
    )

    _replace_in(
        profile,
        "**Legislation, Test Item & Citation** (required): type a keyword such as “lead” and pick the test item.",
        "**Legislation, Test Item & Citation** (required): type in this field. The reviewed screenshot sets Export Market to Africa and shows **+ Add '[UAT TEST]'**. It is not a legislation results list and not a saved Test Data record.",
    )
    search = _image(profile, "07-test-item-search.jpg")
    search["caption"] = "Test Data form — Export Market set; legislation field showing + Add ‘[UAT TEST]’ (not a completed saved record)."
    search["alt"] = "In-progress Test Data form. Result is unset, Export Market is Africa, and the legislation field shows + Add '[UAT TEST]'. Not a legislation results list and not a saved record."

    filled = _image(profile, "08-test-data-filled.jpg")
    filled["caption"] = "Not captured. A completed Test Data record with a linked report is not in this draft."
    filled["alt"] = filled["caption"]
    filled["availability"] = "not-captured"
    filled["pending_note"] = (
        "Not captured. A Test Data record was not saved and a report was not linked for this screenshot. "
        "This placeholder is not a completed or saved record."
    )

    _replace_in(
        profile,
        "Click **Confirm**. The record appears in the Test Data table with its export market, legislation, test item, citation, report ID and issue party.",
        "Click **Confirm** to close the Test Data form. This draft does not show a saved Test Data row. Screenshots of a completed record and of the table after saving were not captured, because each needs a real saved record.",
    )
    saved = _image(profile, "09-test-data-saved.jpg")
    saved["caption"] = "Not captured. The Test Data table after saving is not in this draft."
    saved["alt"] = saved["caption"]
    saved["availability"] = "not-captured"
    saved["pending_note"] = (
        "Not captured. A saved Test Data row was not created for this screenshot. "
        "This placeholder is not proof of a saved record."
    )

    _replace_in(
        profile,
        "**Certificate Data** works the same way. Fill in the certificate **Type**, **Issue Party**, **Score / Overall Rating**, **Expiry Date** and **Certificate Date**, then link the certificate file.",
        "**Certificate Data** works the same way. Fill in the certificate **Type**, **Issue Party**, **Score / Overall Rating**, **Expiry Date** and **Certificate Date**, then link the certificate file. The reviewed screenshot shows that form empty.",
    )
    certificate = _image(profile, "10-certificate-data-form.jpg")
    certificate["caption"] = "Empty Certificate Data form."
    certificate["alt"] = "Empty Certificate Data form. Type, Issue Party, score and dates are unset."
    certificate["caption_note"] = "This screenshot does not show filled certificate values."

    _before_image(
        profile,
        "11-quality-requirement.jpg",
        "The reviewed screenshot is not an empty tab. It shows one requirement with the name hidden, plus Test Plan, ⋯ and Add. The attachment area under that row is empty.",
    )
    quality = _image(profile, "11-quality-requirement.jpg")
    quality["caption"] = "Quality Requirement tab with one existing requirement (name redacted); Test Plan, ⋯, and Add visible — not an empty tab."
    quality["alt"] = "Quality Requirement tab with one redacted requirement row, Test Plan, the more menu and Add. Not an empty tab."

    _before_image(
        profile,
        "19-requirement-filled.jpg",
        "The reviewed Add Requirement screenshot shows Type and Name empty, with Mandatory checked. It is not an example of a filled Type and Name.",
    )
    add_req = _image(profile, "19-requirement-filled.jpg")
    add_req["caption"] = "Add Requirement modal — Type and Name empty, Mandatory checked (not a filled Type and Name example)."
    add_req["alt"] = "Add Requirement modal with empty Type and Name fields and Mandatory checked."

    templates = _image(profile, "20-templates-menu.jpg")
    templates["caption_note"] = (
        "The open menu shows Import To Product Testing, Import to Document Review, Export As Document, "
        "and Templates: Apply Template, Save As Template and Manage Templates."
    )

    apply = _image(profile, "21-apply-template.jpg")
    apply["caption_note"] = (
        "The list shows EU Electrical Compliance Template, EU Electrical Toy and new template 001, each with View and Apply. "
        "Creator names are blanked in this screenshot."
    )

    _before_image(
        profile,
        "22-requirement-list.jpg",
        "The screenshot of the list after Apply Template was not captured, because that needs a real apply. The placeholder is not that list.",
    )
    applied = _image(profile, "22-requirement-list.jpg")
    applied["availability"] = "not-captured"
    applied["pending_note"] = (
        "Not captured. Apply Template was not run for this screenshot. "
        "This placeholder is not the requirement list after a template is applied."
    )
    _set_meta(
        profile,
        "Checked against",
        "QMAS dev, 4 Nov 2026. Document, Shipping Detail, the empty Compliance Data tab, the in-progress Test Data form, the empty Certificate Data form, and the Quality Requirement shots included here were rechecked on QMAS dev, 9 Nov 2026.",
    )
