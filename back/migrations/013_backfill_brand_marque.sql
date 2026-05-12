UPDATE brand
SET marque = name
WHERE marque IS NULL OR marque = '';
