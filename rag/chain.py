import chromadb
from sentence_transformers import SentenceTransformer
import ollama

# --- Load embedding model ---
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# --- Connect to ChromaDB ---
print("Connecting to ChromaDB...")
client = chromadb.PersistentClient(path="./chromadb")
collection = client.get_collection("f1_pitwall")
print(f"Connected — {collection.count()} vectors loaded ✅")

def retrieve(query, n_results=5):
    """Find the most relevant chunks for a question"""
    query_embedding = model.encode(query).tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    return results['documents'][0]

def ask(question):
    """Full RAG pipeline: retrieve + generate answer"""
    print(f"\nQuestion: {question}")
    print("Retrieving relevant data...")
    
    # Step 1: Retrieve relevant chunks
    chunks = retrieve(question)
    
    # Step 2: Build context from chunks
    context = "\n\n".join(chunks)
    
    # Step 3: Build prompt
    prompt = f"""You are PitWall AI, an expert F1 analyst with access to race data from 2000 to 2023.

Use ONLY the following data to answer the question. Be specific, cite numbers, and give insights like a real analyst would.
If the data doesn't contain enough information, say so clearly.

DATA:
{context}

QUESTION: {question}

ANSWER:"""

    print("Generating answer with Llama...")
    
    # Step 4: Send to Ollama
    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    answer = response['message']['content']
    
    print("\n" + "="*50)
    print("PITWALL AI ANSWER:")
    print("="*50)
    print(answer)
    print("="*50)
    
    return answer

# --- Test it! ---
if __name__ == "__main__":
    # Test query 1
    ask("How does Max Verstappen perform in wet conditions?")
    
    print("\n")
    
    # Test query 2  
    ask("Who is the best driver at street circuits?")