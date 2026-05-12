## to import fabdis xls to csv set (csv stored in var/storage/<imported filename_without_xls>)

go to interface
http://localhost:5173/admin/source

in the select, choose 'import new source'

then in the cmd line, run:

python script/cli.py database:sync:fabdis --fabdis-dir var/storage/<imported filename_without_xls>

## export to qdrant

python script/vendors/fabdis/qdrant.py <FABRICANT>

## import qdrant to product, brand, vendor:

python script/import_qdrant_products.py --fabricant <FABRICANT>

# Optional: import only specific marque

python script/import_qdrant_products.py --marque <MARQUE>

## Generation de devis de test

# Default markdown output

python script/list_random_products.py

# Generate PDF with default settings

python script/list_random_products.py --format pdf

# Generate PDF with custom output path

python script/list_random_products.py --format pdf --output /path/to/report.pdf

# Generate PDF with custom quantity range and count

python script/list_random_products.py --format pdf --count 20 --min-qty 5 --max-qty 200
