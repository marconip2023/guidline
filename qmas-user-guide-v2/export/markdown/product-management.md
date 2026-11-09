---
title: "Product Management — Create and Edit a Product"
slug: product-management
document_status: working-copy-draft
version: 2026-11-09-draft
language: en
notion_working_hub: https://app.notion.com/p/4139c62c39fc8198ac49e172050cf65b
image_policy: Reviewed replacement screenshots use a relative path. Other screenshots are explicit placeholders and are not linked.
---

# Product Management — Create and Edit a Product

> Working copy draft 2026-11-09-draft. English text from the published QMAS User Guide. Unreviewed screenshots are omitted.

Add a product profile to QMAS so you can attach documents, compliance data, testing and eFiling to it.

- **Module:** Product Management
- **Start here:** https://qmas.icw.io/product/list → **+ New Product**
- **Direct link:** https://qmas.icw.io/add-product
- **Steps:** 1 Product Profile → 2 Related Product → Done
- **Checked against:** QMAS dev, 9 Nov 2026

## Overview

1. Open **Product Management** and click **+ New Product**.
2. **Product Profile**: fill in product details, then choose a supplier. Shipping information, factory and additional info are optional.
3. **Related Product** (optional): link related products, then click **Done**.
4. The product appears at the top of the Product Management list. Open it to see the product profile.
5. To change it later, open the product, click **⋮** next to the name, then **Edit product**.

## Step-by-step

### 1. Open Product Management

In the left menu, open **Product Management**. Click **+ New Product** at the top right. To add many products at once, use **Import Product**.

Filter the list with **Product Category**, **Customer Product Category**, **Product Number**, **Status**, **Created By** and **Team**. **Sort by Date modified** changes the order. **Reset** clears the filters.

![Product Management list with Import Product and + New Product at the top right.](images/product-management/01-list.jpg)


*Product Management list with Import Product and + New Product at the top right.*

Reviewed screenshot of the list filters and column headers. No data rows are shown.


### 2. Product Profile — product details

The **Add new product** wizard opens. Under **1. Product Details**, fill in:

- **Item No.** and **Product Name** (required).
- **Long Descriptions** (optional): purpose, materials and internal parts such as batteries or stuffing.
- **Additional Item No.** (optional).
- **Product Category (QMAS)**: click **Select Category**.
- **Customer Tag**, **Customer Product Category** (Level 1–3) and **Remark** (optional).

![Step 1 Product Profile — Product Details.](images/product-management/02-step1-empty.jpg)


*Step 1 Product Profile — Product Details.*

In **Select Category**, search by name (for example “drinkware”), click the category, then click **Add category**.

![Selected categories show as dark chips at the top. “1 selected” appears next to Add category.](images/product-management/03-select-category.jpg)


*Selected categories show as dark chips at the top. “1 selected” appears next to Add category.*


### 3. Product Profile — supplier

Under **2. Supplier**, choose **My supplier list** and click **Select supplier**, or choose **New supplier** to add one here.

In the pop-up, click **Select** on one supplier, then **Confirm**.

![Select 1 Supplier — you can link one supplier per product.](images/product-management/04-select-supplier.jpg)


*Select 1 Supplier — you can link one supplier per product.*

The supplier card appears. Use **Change Supplier** to pick another one, or **Edit this profile** to update the supplier.

![Selected supplier, followed by 3. Shipping Information (optional).](images/product-management/05-supplier-shipping.jpg)


*Selected supplier, followed by 3. Shipping Information (optional).*

The supplier card body in this screenshot is intentionally blank. Change Supplier and Edit this profile remain visible. The selected test supplier is shown on the Select supplier screenshot.


### 4. Product Profile — optional sections

- **Shipping Information**: size, weight, tolerance and barcode for the selling unit, inner carton and outer carton.
- **Factory**: click **Select existing factory**.
- **Additional Info**: choose a **Buyer** (or **Add buyer**) and upload up to 30 **product photos** (JPG, JPEG, PNG).

Click **Next**.

![Factory and Additional Info at the bottom of step 1, then Next.](images/product-management/06-factory-additional.jpg)


*Factory and Additional Info at the bottom of step 1, then Next.*


### 5. Related Product (optional)

Product linkage helps you manage compliance reports. For example, link a raw material or an assortment to several end products. Click **Select related product**, or skip this step. Click **Done**. **Unlink** removes a product from this step.

![Step 2 Related Product.](images/product-management/07-step2-related.jpg)


*Step 2 Related Product.*


### 6. Done — find your product

QMAS shows “Product added” and returns to the Product Management list. The new product is at the top.

The screenshot of that new row was not captured, because it would require creating a real product. The placeholder is not a picture of a finished create.

> **Not captured:** `08-product-added.jpg`
>
> Not captured. A real product was not created for this screenshot, so this placeholder is not confirmation of a completed create.

*The new product at the top of the list.*

Click the product to open its profile. From the left menu of the profile you can manage **Document**, **Shipping Detail**, **Compliance Data**, **Quality Requirement**, **AI Risk Screening**, **CPSC eFiling** and **Packaging Detail**.

The left menu also includes **QR Code**.

![Product profile.](images/product-management/09-product-profile.jpg)


*Product profile.*

Left menu includes Document, Shipping Detail, Compliance Data, Quality Requirement, AI Risk Screening, CPSC eFiling, Packaging Detail and QR Code. The Document tab shows New Folder, Upload, All, Archived, Type, Source, Checked, Sort and Reset.


### 7. Edit, copy or deactivate a product

On the product profile, click **⋮** next to the product name:

| Option | What it does |
|---|---|
| Edit product | Opens the same wizard with your saved details. Change them, then click Next and Done. |
| Testing order | Starts a Product Testing order for this product. |
| Make a copy | Creates a new product with the same details. |
| Mark as inactive | Sets the product to inactive. |

![The ⋮ menu on the product profile.](images/product-management/10-more-menu.jpg)


*The ⋮ menu on the product profile.*

![Edit product profile — the same steps as creating a product.](images/product-management/11-edit-product.jpg)


*Edit product profile — the same steps as creating a product.*


## Tips

- Search the list before you create a product so you don’t add a duplicate.
- Shipping information is optional when you create the product. You can add it later from **Shipping Detail** on the profile.

## FAQ

**Q: How do I create a new product in QMAS?**

A: Go to Product Management (https://qmas.icw.io/product/list), click + New Product, fill in Product Profile, then click Next and Done. Direct link: https://qmas.icw.io/add-product

**Q: How do I edit a product?**

A: Open the product from the Product Management list, click ⋮ next to the product name, then Edit product.

**Q: Can I add many products at once?**

A: Yes. Click Import Product on the Product Management list.

**Q: Where do I submit eFiling or add compliance data for a product?**

A: Open the product profile and use CPSC eFiling or Compliance Data in its left menu.
