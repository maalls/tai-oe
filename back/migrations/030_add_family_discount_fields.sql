ALTER TABLE family
  ADD COLUMN IF NOT EXISTS product_code text,
  ADD COLUMN IF NOT EXISTS quantity numeric(14,3),
  ADD COLUMN IF NOT EXISTS discount numeric(5,2),
  ADD COLUMN IF NOT EXISTS unit text,
  ADD COLUMN IF NOT EXISTS packing text,
  ADD COLUMN IF NOT EXISTS lead_time_week integer,
  ADD COLUMN IF NOT EXISTS net_price numeric(14,4);
