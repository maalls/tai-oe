ALTER TABLE brand
  ADD COLUMN IF NOT EXISTS vendor_id uuid REFERENCES vendor(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_brand_vendor_id ON brand (vendor_id);
