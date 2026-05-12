#!/usr/bin/env python3
import sys
from pathlib import Path
import hashlib
from qdrant_client.models import PointStruct

# Add parent directories to path for imports
script_dir = Path(__file__).resolve().parent
vendors_dir = script_dir.parent
script_root = vendors_dir.parent
back_dir = script_root.parent
sys.path.insert(0, str(back_dir))
sys.path.insert(0, str(script_root))

from src.config import get_vendor_config


def generate_numeric_id(ref_id: str) -> int:
    """Generate a stable numeric ID from a string reference.
    
    Args:
        ref_id: String ID (e.g., refciale)
        
    Returns:
        Numeric ID (positive integer)
    """
    # Create a hash of the string ID
    hash_obj = hashlib.md5(ref_id.encode('utf-8'))
    # Convert to unsigned 64-bit integer (Qdrant uses uint64)
    hash_int = int(hash_obj.hexdigest(), 16) & 0x7FFFFFFFFFFFFFFF  # Keep positive
    return hash_int


# collect yuasa feuille1.csv file in the config csv dir
# add a point to the Qdrant collection as defined in config.yml 
# the embedding is using the description field
def main():
    """Convert yuasa CSV to Qdrant vectors."""   
    print("🔍 Reading configuration...")
    config = get_vendor_config("yuasa")
    csv_dir_name = config.get("csv_output_dir")
    if not csv_dir_name:
        print(config)
        raise ValueError("CSV output directory not specified in configuration.")
    else:
        print(f"📁 yuasa CSV directory: {csv_dir_name}")
        # Resolve relative to back directory
        csv_dir = Path(csv_dir_name)
        if not csv_dir.is_absolute():
            back_dir = Path(__file__).resolve().parents[3]
            csv_dir = back_dir / csv_dir
    
    if not csv_dir.exists():
        print(f"❌ Directory not found: {csv_dir}")
        return 1
    
    from src.controller.qdrant_handler import QdrantHandler
    from src.embeddings import EmbeddingGenerator
    import csv

    try:
        qdrant_handler = QdrantHandler()
        embedding_generator = EmbeddingGenerator()
        
        for csv_file in csv_dir.glob("*.csv"):
            print(f"📄 Processing CSV file: {csv_file.name}")
            with csv_file.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    description = row.get("gamme", "")
                    if not description:
                        continue
                    
                    embedding = embedding_generator.embed_text(description)
                    
                    point_id = generate_numeric_id(row.get("marque", "") + row.get("reference", ""))
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "marque": row.get("marque"),
                            'refciale': row.get("reference"),
                            'libelle240': row.get("gamme"),
                            'tarif': row.get("ht"),
                            'vector_text': description
                        }
                    )
                    
                    qdrant_handler.client.upsert(
                        collection_name=qdrant_handler.collection_name,
                        points=[point]
                    )
                    print(f"   ➕ Added point ID: {point_id}")
        
        print("\n✨ All CSV files processed and points added to Qdrant!")
        return 0
    
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return 1



if __name__ == "__main__":
    sys.exit(main())
