from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
import ollama
import pandas as pd

# --- Setup ---
app = FastAPI(title="PitWall AI", description="F1 Driver Performance RAG Chatbot")

# Allow React frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load models and data ---
print("Loading embedding model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

print("Connecting to ChromaDB...")
client = chromadb.PersistentClient(path="./chromadb")
collection = client.get_collection("f1_pitwall")

print("Loading master dataset...")
df = pd.read_csv("data/processed/master.csv")

print("API ready")

# --- Request model ---
class QuestionRequest(BaseModel):
    question: str

# --- Routes ---
@app.get("/")
def root():
    return {"message": "PitWall AI is running"}

@app.post("/chat")
def chat(request: QuestionRequest):
    """Ask any F1 question"""
    question = request.question
    
    # Retrieve relevant chunks
    query_embedding = model.encode(question).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5
    )
    chunks = results['documents'][0]
    context = "\n\n".join(chunks)
    
    # Generate answer
    prompt = f"""You are PitWall AI, an expert F1 analyst with access to race data from 2000 to 2023.

Use ONLY the following data to answer the question. Be specific, cite numbers, and give insights like a real analyst would.
If the data doesn't contain enough information, say so clearly.

DATA:
{context}

QUESTION: {question}

ANSWER:"""

    response = ollama.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}]
    )
    
    answer = response['message']['content']
    
    return {
        "question": question,
        "answer": answer,
        "sources": chunks[:3]  # Return top 3 sources
    }

@app.get("/drivers")
def get_drivers():
    """Get list of all drivers"""
    drivers = sorted(df['driver_full'].unique().tolist())
    return {"drivers": drivers}

@app.get("/stats/{driver_name}")
def get_driver_stats(driver_name: str):
    """Get stats for a specific driver"""
    driver_data = df[df['driver_full'] == driver_name]
    
    if len(driver_data) == 0:
        return {"error": "Driver not found"}
    
    total_races = len(driver_data)
    wins = len(driver_data[driver_data['position'] == 1])
    podiums = len(driver_data[driver_data['position'] <= 3])
    wet_races = driver_data[driver_data['weather'] == 'wet']
    street_races = driver_data[driver_data['circuit_type'] == 'street']
    
    return {
        "driver": driver_name,
        "total_races": total_races,
        "wins": wins,
        "podiums": podiums,
        "win_rate": round(wins / total_races * 100, 1),
        "avg_finish": round(driver_data['position'].mean(), 2),
        "wet_races": len(wet_races),
        "avg_wet_finish": round(wet_races['position'].mean(), 2) if len(wet_races) > 0 else None,
        "street_races": len(street_races),
        "avg_street_finish": round(street_races['position'].mean(), 2) if len(street_races) > 0 else None,
        "years_active": f"{int(driver_data['year'].min())} - {int(driver_data['year'].max())}",
        "teams": driver_data['constructor'].unique().tolist(),
    }

@app.get("/leaderboard")
def get_leaderboard():
    """Get top drivers by wins"""
    top_drivers = []
    for driver, group in df.groupby('driver_full'):
        wins = len(group[group['position'] == 1])
        if wins > 0:
            top_drivers.append({
                "driver": driver,
                "wins": wins,
                "races": len(group),
                "win_rate": round(wins / len(group) * 100, 1)
            })
    
    top_drivers = sorted(top_drivers, key=lambda x: x['wins'], reverse=True)[:10]
    return {"leaderboard": top_drivers}