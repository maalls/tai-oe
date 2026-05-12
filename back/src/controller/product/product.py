"""Email classification request handler."""

import os
from typing import Dict
#from src.repository.email_repository import EmailRepository
from qdrant_client.models import FieldCondition, MatchValue, PointStruct, Filter
from script.generate_vector import generate_numeric_id, get_product
from src.controller.db_client import DatabaseHandler
from src.controller.qdrant_handler import QdrantHandler
from src.embeddings import EmbeddingGenerator
from src.supabase.supabase_client import get_supabase_service


class ProductController:

    def __init__(self):
        enable_qdrant = os.getenv('ENABLE_QDRANT', 'true').lower() == 'true'
        if enable_qdrant:
            self.qdrant_handler = QdrantHandler()
        else:
            print("[ProductController] QdrantHandler disabled (ENABLE_QDRANT=false)")
            self.qdrant_handler = None
        self.embedding_generator = EmbeddingGenerator()
        self.supabase = get_supabase_service()

    
    def list(self, qs: dict):
        """
        List products, optionally filtering by sku (ILIKE/partial match) and supporting limit.
        Accepts qs: dict (query string params from the request).
        """
        sku = qs.get('sku', [None])[0]
        limit = int(qs.get('limit', [10])[0])
        query = self.supabase.from_('product').select('*,product_family(*,family(*))')
        if sku:
            query = query.ilike('sku', f'{sku}')
        query = query.limit(limit)
        print("[api][product][list] Querying database with sku:", sku )
        result = query.execute()
        products = result.data if result and result.data else []
        print(f"[api][product][list] Retrieved {len(products)} products from database")
        return products

    def post(self, payload) -> Dict:
        product = self.upsert_product(payload)
        self.upsert_family(product, payload)
        self.upsert_in_qdrant(product, payload)
        print("Product upserted in database", product)
        return product

    def upsert_family(self, product, payload):
        print("Validating family codes in the database:", payload['family_codes'])
        db_families = self.supabase.from_('family').select('*').in_('code', payload['family_codes']).execute()
        print('found families: ', len(db_families.data))
        families = db_families.data
        print("Families found in database:", families)
        # We create the family codes that are missing in the database
        codes = {family['code'] for family in db_families.data}
        for code in payload['family_codes']:
            if code not in codes:
                family = self.create_family(code)
                families.append(family)
            else :
                family = next(f for f in db_families.data if f['code'] == code)
            
            print(f"Linking product to family code '{family['code']}' in database")
            result = self.supabase.from_('product_family').upsert({
                'product_id': product['id'],
                'family_id': family['id']
            }).execute()
            print("Database insert result for product_family link:", result)
            if result.data is None:
                raise Exception(f"Failed to link product to family code in database: {result['error']}")
            else:
                print(f"Product linked to family code '{family['code']}' successfully in database", result.data)
                

        product['families'] = families
        return product

    def create_family(self, code):
        print(f"Creating missing family code '{code}' in database")
        data = {"code": code, "type": "NET_PRICE", "name": code}
        result = self.supabase.from_('family').insert(data).execute()
        print("Database insert result for family code:", result)
        if result.data is None:
            raise Exception(f"Failed to create family code in database: {result['error']}")
        else:
            print(f"Family code '{code}' created successfully in database", result.data)
            return result.data[0]
            

    def upsert_product(self, payload) -> Dict:
        """
        {
            "marque": "Hélita",
            "refciale": "sdf",
            "libelle240": "sdf",
            "tarif": 1,
            "family_codes": [
                "FA",
                "BU"
            ],
            "vector_text": ""
        }
        """
        fields = ['family_codes', 'libelle240', 'marque', 'refciale', 'tarif', 'vector_text']

        for field in fields:
            if field not in payload:
                raise ValueError(f'Missing product field: {field}')

        print("Retreiving brand", payload['marque'])
        brands = self.supabase.from_('brand').select('*').eq('marque', payload['marque']).execute()
        if len(brands.data) == 0:
            raise ValueError(f"Brand '{payload['marque']}' not found in database")
        brand = brands.data[0]
        print("Brand found in database:", brand['id'])
        # check all the related families exist in the database    
        
        print("Looking up the database via db client")
        products = self.supabase.from_('product').select('*').eq('sku', payload['refciale']).execute()
        print("Database lookup result:", products)
        if (len(products.data) > 0):
            print("Product found in database")
            product = products.data[0]
        else:
            print("Product not found in database, inserting new product")
            # Insert into database
            data = {
                "sku": payload['refciale'],
                "name": payload['libelle240'],
                "brand_id": brand['id'],
                "price": payload['tarif'],
            }
            insert_result = self.supabase.from_('product').insert(data).execute()
            print("Database insert result:", insert_result)
            if insert_result.data:
                print("Product inserted successfully into database", insert_result.data)
                product = insert_result.data[0]
            else:
                raise Exception(f"Failed to insert product into database: {insert_result['error']}")
        product['brand'] = brand
        return product
        
    def upsert_in_qdrant(self, product: dict, payload) -> Dict:
        print("[product]Upserting product in Qdrant, marque:", product['brand']['marque'], "refciale:", product['sku'])
        """Upsert a product into Qdrant."""

        
        filters = {
            "marque": product['brand']['marque'],
            "refciale": product['sku'],
        }

        print("Checking for existing product in Qdrant with filters:", filters)
        points = self.qdrant_handler.scroll_points(filters=filters)
        
        if len(points['points']) == 0:
            print("No existing product found in Qdrant, creating new point")
            ref_id = f"{product['brand']['marque']}-{product['sku']}"
            qd_id = generate_numeric_id(ref_id)
            id = qd_id
            new = True
            print("Upserting new product with ID:", id)
            vector = self.embedding_generator.embed_text(product['name'])

            codes = [family['code'] for family in product.get('families', [])]
            data = {
                'marque': product['brand']['marque'],
                'refciale': product['sku'],
                'libelle240': product['name'],
                'tarif': product['price'],
                'family_codes': codes,
            }
            point = self.qdrant_handler.upsert_point(point_id=qd_id, vector=vector, payload=data)
            return point
        else:
            print("Existing product found in Qdrant, ID:", points['points'][0]['id'])
            return points['points'][0]

        
