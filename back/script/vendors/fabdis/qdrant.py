import argparse
import sys
from qdrant_client.models import FieldCondition, MatchValue, PointStruct, Filter
from script.generate_vector import generate_numeric_id, get_product
from src.controller.db_client import DatabaseHandler
from src.controller.qdrant_handler import QdrantHandler
from src.embeddings import EmbeddingGenerator


def _fetch_marques_by_fabricant(db: DatabaseHandler, fabricant: str) -> list[str]:
    """Get all marques associated with a fabricant from cartouches."""
    rows = db.execute_dict_query(
        "SELECT DISTINCT carmarque FROM fabdis_cartouches WHERE LOWER(TRIM(fabricant)) = LOWER(TRIM(%s))",
        (fabricant,)
    )
    return [row['carmarque'] for row in rows if row.get('carmarque')]


def _fetch_commerce_rows(db: DatabaseHandler, marques: list[str], limit: int | None):
    """Fetch commerce rows for multiple marques."""
    if not marques:
        return []
    
    placeholders = ",".join(["%s"] * len(marques))
    query = f"SELECT * FROM fabdis_commerce WHERE marque IN ({placeholders})"
    params = tuple(marques)
    
    if limit:
        query += " LIMIT %s"
        params = (*params, limit)
    
    return db.execute_dict_query(query, params)


def main(args) -> int:
    fabricant = args.fabricant.strip()
    if not fabricant:
        print("Fabricant name is required.")
        return 1

    print("🔍 Reading configuration...")
    db = DatabaseHandler()
    qdrant_handler = QdrantHandler()
    embedding_generator = EmbeddingGenerator()

    # Fetch marques for this fabricant
    print(f"🔍 Looking up marques for fabricant '{fabricant}'...")
    marques = _fetch_marques_by_fabricant(db, fabricant)
    if not marques:
        print(f"❌ No marques found for fabricant '{fabricant}' in fabdis_cartouches")
        return 1
    
    print(f"✓ Found {len(marques)} marque(s): {', '.join(marques)}")

    # Delete existing points for all these marques
    print(f"\n🗑️  Deleting existing points for marques: {', '.join(marques)}")
    total_deleted = 0
    for marque in marques:
        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key="marque",
                    match=MatchValue(value=marque),
                )
            ]
        )
        delete_count_result = qdrant_handler.client.count(
            collection_name=qdrant_handler.collection_name,
            count_filter=qdrant_filter,
            exact=True,
        )
        delete_count = delete_count_result.count if delete_count_result else 0
        if delete_count > 0:
            delete_result = qdrant_handler.client.delete(
                collection_name=qdrant_handler.collection_name,
                points_selector=qdrant_filter,
            )
            print(f"  - {marque}: deleted {delete_count} points")
            total_deleted += delete_count
    
    print(f"✓ Total deleted: {total_deleted} points")

    # Fetch and index products for all marques
    print(f"\n📥 Fetching products for marques: {', '.join(marques)}")
    rows = _fetch_commerce_rows(db, marques, args.limit)
    total_rows = len(rows)
    if total_rows == 0:
        print(f"❌ No fabdis_commerce rows found for these marques.")
        return 0

    print(f"✓ Found {total_rows} rows to index")
 
    points_inserted = 0
    for start in range(0, total_rows, args.batch_size):
        batch_rows = rows[start:start + args.batch_size]
        products = [get_product(row, db) for row in batch_rows]
        
        payloads = [
            {
                "marque": product.get("marque"),
                "refciale": product.get("refciale"),
                "libelle240": product.get("libelle240"),
                "tarif": product.get("tarif"),
                "family_codes": product.get("family_codes"),
                "vector_text": product.get("vector_text"),
            }
            for product in products
        ]
        texts = [payload.get("vector_text") or "" for payload in payloads]
        try:
            embeddings = embedding_generator.embed_batch(texts)
        except Exception as e:
            print(f"❌ Error generating embeddings for batch starting at {start}: {e}")
            continue

        points = []
        for payload, embedding in zip(payloads, embeddings):
            original_id = f"{payload['marque']}-{payload['refciale']}"
            point_id = generate_numeric_id(original_id)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload,
                )
            )

        qdrant_handler.client.upsert(
            collection_name=qdrant_handler.collection_name,
            points=points,
        )
        points_inserted += len(points)
        print(f"  ✓ Inserted {points_inserted}/{total_rows} points")

    print(f"\n✅ Successfully indexed fabricant '{fabricant}' ({points_inserted} products for {len(marques)} marque(s))")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest FAB-DIS commerce data into Qdrant by fabricant")
    parser.add_argument("fabricant", help="Fabricant name (e.g. Thomas&Betts, ABB, etc.)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of rows to ingest")
    parser.add_argument("--batch-size", type=int, default=50, help="Embedding batch size")
    args = parser.parse_args()
    sys.exit(main(args))