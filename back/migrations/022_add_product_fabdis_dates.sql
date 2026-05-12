ALTER TABLE product
ADD COLUMN IF NOT EXISTS fabdis_appli_date date,
ADD COLUMN IF NOT EXISTS fabdis_edited_date date;
