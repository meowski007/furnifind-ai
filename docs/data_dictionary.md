# FurniFind AI — Data Dictionary & Catalogue Schema

## 1. Product Entity Schema

All catalogue products are mapped to the `products` table in the relational store and validated via Pydantic schemas.

| Field Name | Type | Nullable | Units / Format | Description | Index |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `product_id` | String(64) | No | Format: `FUR-{CAT}-{NUM}` | Unique primary key identifier | Primary Key, Indexed |
| `title` | String(255) | No | UTF-8 String | Commercial product title | Indexed |
| `description` | Text | No | UTF-8 String | Detailed product copy and features | Full text |
| `category` | String(64) | No | Normalized lowercase | Furniture category (desks, chairs, sofas, tables, beds, bookcases, storage, lighting) | Indexed |
| `price` | Float | No | INR (₹) | Product sale price in Indian Rupees | Indexed |
| `currency` | String(8) | No | ISO 4217 | Default: `"INR"` | No |
| `material` | String(64) | Yes | Normalized lowercase | Primary material (oak, walnut, pine, velvet, leather, rattan, metal, etc.) | Indexed |
| `colour` | String(64) | Yes | Normalized lowercase | Colorway or finish | Indexed |
| `style` | String(64) | Yes | Normalized lowercase | Aesthetic classification (scandinavian, modern, industrial, mid-century, boho, rustic) | Indexed |
| `width` | Float | Yes | Centimetres (cm) | Outer width dimension | Indexed |
| `height` | Float | Yes | Centimetres (cm) | Outer height dimension | No |
| `depth` | Float | Yes | Centimetres (cm) | Outer depth dimension | No |
| `image_path` | String(512) | Yes | Relative filesystem path | Path to local product thumbnail image | No |
| `image_url` | String(1024)| Yes | HTTPS URL | External asset URL fallback | No |
| `availability`| Boolean | No | Boolean (`True`/`False`)| Stock status flag | Indexed |
| `source` | String(128) | No | String | Data provenance label (`furnifind_sample_catalogue`) | No |
| `created_at` | DateTime | No | ISO 8601 UTC | Record creation timestamp | Indexed |

---

## 2. Dimensional Standards

- **Length Units**: All dimensions (`width`, `height`, `depth`) are strictly normalized to **centimetres (cm)**.
- **Price Units**: All prices are expressed in **Indian Rupees (INR ₹)** as floating-point values.
- **Missing Value Policy**:
  - Missing dimensions are stored as SQL `NULL` (`None` in Python).
  - Search engine hard filters handle nulls explicitly: if a query specifies `max_width <= 110 cm`, products with `width IS NULL` are omitted from hard width filter results unless width filter is disabled.
  - The Shopping Assistant explicitly flags missing attributes rather than fabricating estimates.

---

## 3. Sample Catalogue Distribution

The sample catalogue contains 31 curated furniture products across 8 major categories:

| Category | Product Count | Price Range (₹) | Key Materials |
| :--- | :--- | :--- | :--- |
| **Desks** | 5 | ₹6,499 – ₹28,999 | Oak, Walnut, Pine, Bamboo, Engineered Wood |
| **Chairs** | 6 | ₹3,800 – ₹15,999 | Mesh, Oak, Faux Leather, Velvet, Teak & Rattan |
| **Sofas** | 4 | ₹22,499 – ₹79,999 | Belgian Linen, Navy Velvet, Top-Grain Leather, Woven Fabric |
| **Tables** | 4 | ₹7,999 – ₹34,999 | Solid Oak, Honed Carrara Marble, Acacia Wood, Smoked Glass |
| **Beds** | 3 | ₹24,500 – ₹46,999 | Woven Fabric, Sheesham Rosewood, Powder-coated Steel |
| **Bookcases** | 3 | ₹9,499 – ₹16,800 | Ash Wood, Rustic Oak & Iron, Walnut Veneer |
| **Storage** | 4 | ₹2,999 – ₹29,999 | Oak Tambour, Fluted Glass & Black Steel, Cane Rattan |
| **Lighting** | 2 | ₹4,299 – ₹11,499 | Brushed Brass & Marble, Handcrafted Ceramic |
