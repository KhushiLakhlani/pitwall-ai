from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chromadb
from sentence_transformers import SentenceTransformer
from groq import Groq
import pandas as pd
import os
import sys
from dotenv import load_dotenv

sys.path.append('.')
load_dotenv()

# --- Setup ---
app = FastAPI(title="PitWall AI", description="F1 Driver Performance RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Groq client (lightweight, load immediately) ---
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- Lazy loaded resources ---
_model = None
_collection = None
_df = None

def get_model():
    global _model
    if _model is None:
        print("Loading embedding model...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded ✅")
    return _model

def get_collection():
    global _collection
    if _collection is None:
        print("Connecting to ChromaDB Cloud...")
        client = chromadb.CloudClient(
            api_key=os.getenv("CHROMA_API_KEY"),
            tenant=os.getenv("CHROMA_TENANT"),
            database=os.getenv("CHROMA_DATABASE")
        )
        _collection = client.get_collection("f1_pitwall")
        print("ChromaDB Cloud connected ✅")
    return _collection

def get_df():
    global _df
    if _df is None:
        print("Loading master dataset...")
        _df = pd.read_csv("data/processed/master.csv")
        print("Dataset loaded ✅")
    return _df

print("API ready ✅")

# --- Request model ---
class QuestionRequest(BaseModel):
    question: str

# --- Routes ---
@app.get("/")
def root():
    return {"message": "PitWall AI is running 🏎️"}

@app.post("/chat")
def chat(request: QuestionRequest):
    question = request.question

    from rag.retriever import smart_retrieve
    chunks = smart_retrieve(question, n_results=8)
    context = "\n\n".join(chunks)

    prompt = f"""You are PitWall AI, an expert F1 analyst with access to race data from 2000 to 2025.

Use ONLY the following data to answer the question. Be specific, cite numbers, and give insights like a real analyst would.
If the data doesn't contain enough information, say so clearly.

DATA:
{context}

QUESTION: {question}

ANSWER:"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content

    return {
        "question": question,
        "answer": answer,
        "sources": chunks[:3]
    }

@app.get("/drivers")
def get_drivers():
    df = get_df()
    drivers = sorted(df['driver_full'].unique().tolist())
    return {"drivers": drivers}

@app.get("/stats/{driver_name}")
def get_driver_stats(driver_name: str):
    df = get_df()
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
    df = get_df()
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

@app.get("/compare/{driver1}/{driver2}")
def compare_drivers(driver1: str, driver2: str):
    df = get_df()

    def get_stats(driver_name):
        data = df[df['driver_full'] == driver_name]
        if len(data) == 0:
            return None
        wet = data[data['weather'] == 'wet']
        street = data[data['circuit_type'] == 'street']
        total = len(data)
        wins = len(data[data['position'] == 1])
        return {
            "driver": driver_name,
            "total_races": total,
            "wins": wins,
            "win_rate": round(wins / total * 100, 1),
            "avg_finish": round(data['position'].mean(), 2),
            "wet_avg_finish": round(wet['position'].mean(), 2) if len(wet) > 0 else None,
            "wet_wins": len(wet[wet['position'] == 1]),
            "street_avg_finish": round(street['position'].mean(), 2) if len(street) > 0 else None,
            "street_wins": len(street[street['position'] == 1]),
            "years_active": f"{int(data['year'].min())} - {int(data['year'].max())}",
        }

    stats1 = get_stats(driver1)
    stats2 = get_stats(driver2)

    if not stats1 or not stats2:
        return {"error": "One or both drivers not found"}

    from rag.retriever import smart_retrieve
    chunks1 = smart_retrieve(f"{driver1} career performance")
    chunks2 = smart_retrieve(f"{driver2} career performance")
    context = "\n\n".join(chunks1[:3] + chunks2[:3])

    prompt = f"""You are PitWall AI, an expert F1 analyst.
Compare these two drivers based on the data provided. Be specific, cite numbers, and give a clear verdict.

DATA:
{context}

Compare {driver1} vs {driver2} across: overall performance, wet conditions, street circuits.
Give a final verdict on who is the stronger all-round driver based on the data.

ANALYSIS:"""

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "driver1": stats1,
        "driver2": stats2,
        "ai_analysis": response.choices[0].message.content
    }