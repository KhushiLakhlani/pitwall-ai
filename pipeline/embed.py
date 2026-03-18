import json
import chromadb
from sentence_transformers import SentenceTransformer
import time
import os
from dotenv import load_dotenv

load_dotenv()

# --- Load chunks ---
print("Loading chunks...")
with open("data/chunks/all_chunks.json", "r") as f:
    chunks = json.load(f)
print(f"Loaded {len(chunks)} chunks")

# --- Load free HuggingFace embedding model ---
print("\nLoading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded ✅")

# --- Set up ChromaDB Cloud ---
print("\nSetting up ChromaDB Cloud...")
client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_API_KEY"),
    tenant=os.getenv("CHROMA_TENANT"),
    database=os.getenv("CHROMA_DATABASE")
)
collection = client.get_or_create_collection(
    name="f1_pitwall",
    metadata={"hnsw:space": "cosine"}
)
print("ChromaDB Cloud ready ✅")

# --- Embed and store in batches ---
BATCH_SIZE = 100
total = len(chunks)
print(f"\nEmbedding {total} chunks in batches of {BATCH_SIZE}...")

for i in range(0, total, BATCH_SIZE):
    batch = chunks[i:i + BATCH_SIZE]

    texts = [c['text'] for c in batch]
    ids = [c['chunk_id'] for c in batch]
    metadatas = [c['metadata'] for c in batch]

    # Generate embeddings
    embeddings = model.encode(texts, show_progress_bar=False).tolist()

    # Store in ChromaDB Cloud
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )

    print(f"  Progress: {min(i + BATCH_SIZE, total)}/{total} chunks embedded")
    time.sleep(0.3)  # slightly longer pause for cloud

print(f"\n✅ All chunks embedded and stored in ChromaDB Cloud!")
print(f"Total vectors stored: {collection.count()}")

# --- Test a query ---
print("\n--- Test Query: Verstappen wet conditions ---")
query = "How does Verstappen perform in wet conditions?"
query_embedding = model.encode(query).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=3,
    where={"driver": "Max Verstappen"}
)

for i, doc in enumerate(results['documents'][0]):
    print(f"\nResult {i+1}:")
    print(doc)