from pathlib import Path
from script.generate_vector import generate_numeric_id
from src.config import get_vendor_config
import sys
from src.controller.qdrant_handler import QdrantHandler
from src.embeddings import EmbeddingGenerator
import csv
from qdrant_client.models import PointStruct

def main():
    print("🔍 Reading configuration...")
    config = get_vendor_config("legrand")
    
    csv_dir_name = config.get("csv_output_dir")

    if not csv_dir_name:
        print(config)
        raise ValueError("CSV output directory not specified in configuration.")
    
    filename = csv_dir_name + "/TPR.csv"

    if not Path(filename).exists():
        raise FileNotFoundError(f"CSV file not found: {filename}")

    print(f"📁 legrand CSV file: {filename}")
    try:
        qdrant_handler = QdrantHandler()
        embedding_generator = EmbeddingGenerator()
        
        with open(filename, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                print(f"📄 Processing row: {row}")

                description = row.get("Désignation", "")
                embedding = embedding_generator.embed_text(description)

                payload={
                    "marque": row.get("Marque", ""),
                    'refciale': row.get("Référence"),
                    'libelle240': len(description) > 240 and description[:237] + "..." or description   ,
                    'tarif': row.get("Tarif unitaire HT"),
                    'vector_text': description
                }

                point_id = generate_numeric_id(payload["marque"] + payload["refciale"])
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                
                qdrant_handler.client.upsert(
                    collection_name=qdrant_handler.collection_name,
                    points=[point]
                )
                
        print("✅ legrand CSV data successfully ingested into Qdrant.")
        return 0
    except Exception as e:
        print(f"❌ Error during legrand CSV to Qdrant ingestion: {e}")
        return 1
if __name__ == "__main__":
    sys.exit(main())
