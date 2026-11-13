---
title: "Product Testing — Request a Quotation"
slug: product-testing
document_status: working-copy-draft
version: 2026-11-13-draft
language: en
notion_working_hub: https://app.notion.com/p/4139c62c39fc8198ac49e172050cf65b
confidence: published-guide-plus-dev-verified-corrections
image_policy: Reviewed replacement screenshots use a relative path. Other screenshots are explicit placeholders and are not linked.
---

# Product Testing — Request a Quotation

> Updated working draft 2026-11-13-draft. This file is not deployed. Existing published version: https://marconip2026.github.io/qmas-user-guide/

## Source and verification

**Mixed.** The reviewed create-job screens are current UI verified. Quote Available, Preliminary Accept, and Final Quote are older Help Center wording and are not dev-verified.

Do not mark this whole module unverified. Source: QMAS Help Center — How To Request Quotation For Product Testing From Global Laboratories, last edited 2026-11-04 11:18:27 HKT. The November 2026 update covers the create path. The later quote and accept flow still needs verification.

- [How To Request Quotation For Product Testing From Global Laboratories](https://app.notion.com/p/a57449507c7c4ceea2ed34a1dbbe9f12) (last edited 2026-11-04 11:18:27 HKT). Create path is current UI verified. Preliminary Accept and Final Quote are source-only, not dev-verified.

Help Center home: [QMAS Help Center](https://icw-io.notion.site/QMAS-Help-Center-5cd9414da2474d16a7c405a3542fe4af) (last edited 2026-01-20 13:54:13 HKT). User Guide index: [User Guide](https://app.notion.com/p/a92963a30e584145bb457a62b7706541) (last edited 2026-01-16 15:44:49 HKT). Public icw-io addresses for individual articles were not verified, so those links use app.notion.com.

Create a product testing job and get a quotation from a laboratory.

- **Module:** Product Testing
- **Start here:** [qmas.icw.io/product-testing](https://qmas.icw.io/product-testing) → **Create Job**
- **Direct link:** [qmas.icw.io/product-testing/create-job](https://qmas.icw.io/product-testing/create-job)
- **Steps:** 1 Product Info → 2 Requirements → 3 Provider Selection → 4 Done

## Overview

1. **Open Product Testing** and click **Create Job**.
2. **Product Info** — add an existing product or create a new one.
3. **Requirements** — set the export market, test items, quality requirements and service details.
4. **Provider Selection** — choose Connected Provider, ICW or TicMart, then **Submit**.
5. **Done** — the Order details page opens. Track the job there or in the Product Testing list.

## Step-by-step

### 1. Open Product Testing

In the left menu, open **Product Testing**. The page shows charts of job status, service provider and test results, and the list of all jobs. Click **Create Job** above the list.

![Product Testing list page with the Create Job button](images/product-testing/01-list.jpg)


*Product Testing list — Create Job is at the top right of the job list.*


### 2. Product Info — select products

The **Request Quotations** wizard opens. Add the products for this testing order:

- **+ Existing Products** picks from your Product Management list.
- **+ Add Products** creates a new product here.

![Step 1 Product Info, empty](images/product-testing/02-step1-product-info.jpg)


*Step 1 starts empty. Next stays disabled until a product is added.*

In the **Select Product(s)** pop-up, search by product name or ID, click **Select** on each product you need, then click **Confirm**. You can select more than one product.

![Select Product(s) pop-up with one product selected](images/product-testing/04-product-selected.jpg)


*A selected product shows a blue “✓ Selected” button.*

Check the product details. You can change **Item name on report** and **Item no. on report**, which are printed on the test report. Click **Add PO Information** to link a purchase order (optional). Then click **Next**.

![Step 1 with one product added](images/product-testing/05-step1-filled.jpg)


*Use Remove to drop a product, or Edit product profile to update it.*


### 3. Requirements

**1. Test Requirements**

- **Export Market** — where the product will be sold (required).
- **Test Item** (optional) — choose a country, then search for test items or citations.
- **Quality Requirement** — Create New Requirements, Add Existing Requirements, or Import Requirement Template.
- **Remarks** and **Attachment** (optional) — special instructions and reference files.

![Step 2 Test Requirements with Export Market filled](images/product-testing/07-step2-export-market.jpg)


*Export Market filled in.*

**2. Additional Information**

- **Service Level** — Regular, Express or Shuttle / Emergency.
- **Country of Origin** — where the product is made (you can pick more than one).
- **Intended Usage** — General product, Adult product, Children product or Toys.
- **Buyer Name** (optional).

When all required fields are filled, **Next** turns blue. Click it.

![Step 2 Additional Information filled](images/product-testing/09-step2-filled.jpg)


*Additional Information filled — Next is now enabled.*


### 4. Provider Selection

Choose who should quote this job. You can tick more than one:

| Option | Use it when |
|---|---|
| Connected Provider | You already work with a lab that is connected to your QMAS account. |
| ICW | You want ICW to find a lab. Pick a preferred lab, or leave “No Preference”. |
| TicMart (Marketplace) | You want quotations from labs in the TicMart marketplace. |

![Step 3 Provider Selection with ICW ticked](images/product-testing/11-step3-icw-selected.jpg)


*ICW ticked with “No Preference”. Click Submit to send the request.*


### 5. Done — track your order

After you click **Submit**, QMAS shows “Product testing created successfully” and opens the **Order details** page. Your job has a new order number (for example 260008342) and starts as **Under Review**.

- **Product Testing Requirements**, **Products**, **Supplier**, **PO** and **Test Plan** tabs show what you submitted.
- **Quotations** on the right shows lab quotes when they arrive.
- The tabs below (Quotes, Failure Records, Reports, Attachments, Invoices, Tag, Activity Log, Message Board) follow the job until the report is ready.

![Order details page after submitting](images/product-testing/13-order-details.jpg)


*The new order opens with status Under Review. You can find it again in the Product Testing list.*


## Tips

- Items marked **(optional)** can be skipped. Next stays grey until every required field on the step is filled. A field you leave empty turns red with a message, for example “Country of origin is required”.
![Country of Origin field showing required error](images/product-testing/12-required-error.jpg)


*Required field left empty.*
- Item name and item no. on report are what the lab prints on the test report. Check them before you continue.
- To leave the wizard, click **✕** at the top right.

## Help Center additions and remaining gaps

This section adds Help Center material and named gaps. It does not replace the steps above.

- **Source-documented** — written in the original Help Center. The last-edited date is given. That does not by itself prove the current QMAS UI.
- **Dev-verified** — confirmed on qmas-dev.icw.io during guide work.
- **Gap** — named as missing or too thin. Not current behaviour until checked on dev.

Reviewed screenshots remain 56 of 98. Forty-two inventory slots are still pending. Six supplementary images are not part of the 98. Unreviewed screenshots were not copied.

### Source-documented — create path (Help Center updated 2026-11-04)

Source: How To Request Quotation For Product Testing From Global Laboratories, https://app.notion.com/p/a57449507c7c4ceea2ed34a1dbbe9f12. Direct link cited there: https://qmas.icw.io/product-testing/create-job.

The November 2026 create steps already match this page. Help Center step 7 also says you can tick **Connected Provider** (a lab already linked to the account), **ICW** (ICW finds a lab; preferred lab or “No Preference”), and/or **TicMart (Marketplace)**, then Submit. This page still only has an ICW screenshot.

### Source-documented — post-submit quote flow (older wording; needs verification)

This “receive and confirm” section was not rewritten in November 2026.

1. After submission, the job appears on the list with status **under review**.
2. When the quotation is ready, the status changes to **Quote Available**.
3. Open order details. Under **Quotations**, select a quotation and click **Preliminary Accept**.
4. The Help Center says the designated agency or ICW agency service will then contact you about sample delivery.
5. “The price may vary according to the actual sample. Accept the **Final Quote** to proceed to product testing.”

A 2022 FAQ says cancelling an order is done by contacting customer support via email or online chat. Not re-verified.

### Remaining gaps

- Screenshots and current-UI confirmation for Connected Provider and TicMart.
- Job-detail tabs named in the create steps but not walked through: Quotes, Failure Records, Reports, Attachments, Invoices, Tag, Activity Log, Message Board.
- Edit, cancel, reopen, list search, status filters, and charts.

Help Center reconciliation 2026-11-13 (HKT). Original Help Center not edited. This draft is not the public guide. No Dify upload.
