Design a scalable relational database schema for a distributor/ERP catalog & pricing system (MySQL, compatible with TypeORM). Output:

1. A concise ERD-style description (tables + key columns + relationships).
2. Then the full MySQL DDL (CREATE TABLE ...) with:
   - proper PK/FK
   - indexes for common queries
   - unique constraints
   - DECIMAL types for money
   - utf8mb4
3. Keep it modular and production-ready.

Requirements / scope:

- Multi-tenant: each record belongs to a company (company_id) unless explicitly global.
- Entities:
  - Company, Currency, Tax
  - Brand (and optional Manufacturer)
  - Category taxonomy (one table with parent_id for hierarchy: family/subfamily/category)
  - Product (SKU, EAN, name, descriptions, brand_id, unit)
  - Product ↔ Category many-to-many with is_primary flag (exactly one primary category per product enforced if possible)
  - Tags (tag + product_tag)
  - Price lists (public/net/promo/purchase) with currency + validity dates
  - Price list items (per product, price, min_qty, validity override)
  - Customers, customer groups, membership table
  - Discount rules system:
    - scope enum: PRODUCT | BRAND | CATEGORY | CUSTOMER | CUSTOMER_GROUP
    - discount_type: PERCENT | FIXED
    - priority integer
    - stacking enum: EXCLUSIVE | STACKABLE
    - validity dates
- Optional-but-included modules:
  - Supplier + supplier_product
  - Warehouse + stock_level (on_hand, reserved)
- ETIM support:
  - etim_class, etim_feature, product_etim (1 class per product), product_feature_value (typed value fields).

Design rules:

- Use BIGINT auto-increment ids.
- Use created_at / updated_at timestamps on main tables.
- Store money as DECIMAL(18,6) (or justify another).
- Prevent duplicates:
  - unique(company_id, sku) on product
  - unique(company_id, ean) if not null (handle carefully)
  - unique(company_id, name) on brand (normalized_name optional)
  - unique(company_id, price_list.name)
  - unique(price_list_id, product_id, min_qty, valid_from, valid_to) for price_list_item (or best alternative)
- Index common lookups:
  - product by sku/ean/name
  - product_category by category_id and product_id
  - price_list_item by price_list_id + product_id
  - discount_rule by scope + scope_id + validity + priority
  - stock_level by warehouse_id + product_id

TypeORM compatibility notes:

- Use InnoDB, utf8mb4, and explicit FK constraints.
- Use snake_case table and column names.

After the DDL, also output a short “Query patterns” section listing 8–10 common queries this schema supports (e.g., compute customer price for a product, list products in a category subtree, etc.).

No extra commentary outside these deliverables.
