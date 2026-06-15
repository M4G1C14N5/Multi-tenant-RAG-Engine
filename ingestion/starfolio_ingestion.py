import os
import uuid
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from openai import OpenAI
from test_starfolio_preprocessing import run_preprocessing_pipeline, extract_from_tsx, extract_projects, generate_chunks, RESUME_TSX_PATH, PROJECTS_JSON_PATH

load_dotenv()

# We need an OPENAI_API_KEY to run this in reality, but we'll mock or set it
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "mock-key"))
qdrant = QdrantClient("localhost", port=6333)

COLLECTION_NAME = "tenant_data"

def setup_qdrant():
    collections = qdrant.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)
    
    if not exists:
        print(f"Creating collection: {COLLECTION_NAME}")
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=1536, # OpenAI text-embedding-3-small dimension
                distance=models.Distance.COSINE
            )
        )
    else:
        print(f"Collection {COLLECTION_NAME} already exists.")

def get_embedding(text: str):
    # Mocking if no key
    if client.api_key == "mock-key":
        return [0.0] * 1536
        
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

def upload_chunks(tenant_id: str, chunks: list):
    points = []
    print(f"Generating embeddings for {len(chunks)} chunks...")
    
    for i, chunk in enumerate(chunks):
        vector = get_embedding(chunk["text"])
        point_id = str(uuid.uuid4())
        
        # The crucial part for Multi-tenancy: The Payload
        payload = {
            "tenant_id": tenant_id,
            "type": chunk["type"],
            "text": chunk["text"]
        }
        
        points.append(models.PointStruct(id=point_id, vector=vector, payload=payload))
        
    print(f"Upserting to Qdrant for tenant: {tenant_id}")
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )
    print("Done!")

if __name__ == "__main__":
    print("Connecting to Qdrant and checking setup...")
    setup_qdrant()
    
    print("\nFetching chunks from our preprocessing pipeline...")
    basic_info, work, education = extract_from_tsx(RESUME_TSX_PATH)
    projects = extract_projects(PROJECTS_JSON_PATH)
    chunks = generate_chunks(basic_info, work, education, projects)
    
    tenant_id = "tenant_starfolio_123"
    
    upload_chunks(tenant_id, chunks)
