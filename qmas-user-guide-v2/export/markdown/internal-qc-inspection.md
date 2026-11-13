---
title: "Internal QC Inspection — Start an Internal Inspection"
slug: internal-qc-inspection
document_status: working-copy-draft
version: 2026-11-13-draft
language: en
notion_working_hub: https://app.notion.com/p/4139c62c39fc8198ac49e172050cf65b
confidence: published-guide-plus-dev-verified-corrections
image_policy: Reviewed replacement screenshots use a relative path. Other screenshots are explicit placeholders and are not linked.
---

# Internal QC Inspection — Start an Internal Inspection

> Working copy draft 2026-11-13-draft. English text from the published QMAS User Guide. Unreviewed screenshots are omitted.

Schedule an inspection that your own QC team carries out, without a third-party provider.

- **Module:** Internal QC Inspection
- **Start here:** https://qmas.icw.io/inspection/internal/list → **Create Job**
- **Direct link:** https://qmas.icw.io/inspection/jobs/new?type=internalInspection
- **Steps:** 1 Inspection Requirement → 2 Report Details → 3 Supplier & Factory → 4 Additional Information → 5 Review & Submit
- **Checked against:** QMAS dev, 4 Nov 2026

## Overview

1. Open **Internal QC Inspection** and click **Create Job**. **Start internal inspection** is already selected. Click **Continue**.
2. **Inspection Requirement**: date, type, level and AQL.
3. **Report Details**, **Supplier & Factory** and **Additional Information** work the same way as in the QC Inspection quote flow.
4. **Review & Submit**: check everything and click **Submit**.

## Step-by-step

### 1. Open Internal QC Inspection

In the left menu, open **Internal QC Inspection**. The tabs show **All Job**, **Onsite Job Calendar** and **Draft**. Click **Create Job**. To add many jobs at once, use **Import Job**.

> **Image pending privacy review:** `01-list.jpg`
>
> Reviewed replacement image not available yet. Follow the written steps above.

*Internal QC Inspection list with Import Job and Create Job.*


### 2. Start internal inspection

**Start internal inspection** is selected. Click **Continue**.

> **Image pending privacy review:** `02-looking-to.jpg`
>
> Reviewed replacement image not available yet. Follow the written steps above.

*Create New Job — Start internal inspection selected.*


### 3. Inspection Requirement

Choose the **Inspection Date**, **Inspection type**, **Inspection Level** and the **AQL** (Critical, Major, Minor). There is no budget or service provider, because your own team does the inspection. Click **Next**.

> **Image pending privacy review:** `03-step1-requirement.jpg`
>
> Reviewed replacement image not available yet. Follow the written steps above.

*Step 1 Inspection Requirement for an internal inspection.*


### 4. Steps 2–5

The next steps are the same as in the QC Inspection quote flow. See the [QC Inspection](qc-inspection.md) guide for those steps.

- **Report Details**: add products and their POs.
- **Supplier & Factory**: select the supplier and the factory to inspect.
- **Additional Information**: upload reference files and add remarks.
- **Review & Submit**: check the summary, then click **Submit**. The job opens with its Job ID.


## Tips

- If you need a third-party inspector instead, use QC Inspection → Create Job → **Get QC inspection quote via ICW**.
- Click **Save** on any step to keep a draft.

## FAQ

**Q: How do I start an internal inspection?**

A: Go to Internal QC Inspection (https://qmas.icw.io/inspection/internal/list), click Create Job, keep Start internal inspection selected, click Continue and complete the 5 steps. Direct link: https://qmas.icw.io/inspection/jobs/new?type=internalInspection

**Q: Can I import internal inspection jobs?**

A: Yes. Click Import Job on the Internal QC Inspection list.

## Help Center additions and remaining gaps

This section adds Help Center material and named gaps. It does not replace the steps above.

- **Source-documented** — written in the original Help Center. The last-edited date is given. That does not by itself prove the current QMAS UI.
- **Dev-verified** — confirmed on qmas-dev.icw.io during guide work.
- **Gap** — named as missing or too thin. Not current behaviour until checked on dev.

Reviewed screenshots remain 33 of 98. No new images were added. Unreviewed Help Center screenshots were not copied.

### Help Center finding

There is no standalone Internal QC Help Center article.

The November 2026 QC article mentions **Start internal inspection** as a Looking-to option when your own QC team will inspect. That is the only Help Center mention. It does not document steps 2–5, Import Job, or the Onsite Job Calendar.

### Remaining gaps

- Own screenshots, or a clearly labelled “same as QC” set, for steps 2–5 and the completed job detail.
- **Import Job**.
- **Onsite Job Calendar** tab.
- Draft tab and job detail after submit.
- Difference callouts versus third-party QC beyond “no budget/provider”.

Help Center reconciliation 2026-11-13 (HKT). Original Help Center not edited. This draft is not the public guide. No Dify upload.
