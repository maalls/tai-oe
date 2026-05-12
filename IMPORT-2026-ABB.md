# Import des nouveaux tarifs

# Import des nouvelles remises

fichier FAB-DIS:
back/var/stage/abb-2026/FULL_Tarif_Public_ABB France_Février_2026.xlsx

Mapping product <- FAB DIST:

getting the brand ID:

brand_id = select id from brand where brand.name = B01_COMMERCE.MARQUE and vendor_id = (select id from vendor where name = "ABB")

upsert
product
where
sku == B01_COMMERCE.REFCIALE AND
with
brand_id = (select id from brand where brand.name = B01_COMMERCE.MARQUE and vendor_id = (select id from vendor where name = "ABB"))
name = B01_COMMERCE.LIBELLE80
default_tax_rate = B01_COMMERCE.TVA
price = B01_COMMERCE.TARIF
fabdis_appli_date = BOO_CARTOUCHE.DATEAPPLI
fabdis_edited_date = BOO_CARTOUCHE.DATEDIT
