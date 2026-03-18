import chromadb
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv

load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_API_KEY"),
    tenant=os.getenv("CHROMA_TENANT"),
    database=os.getenv("CHROMA_DATABASE")
)
collection = client.get_collection("f1_pitwall")

def parse_query(question):
    """Extract filters from the question"""
    question_lower = question.lower()
    filters = {}

    all_drivers = [
        "verstappen", "hamilton", "leclerc", "sainz", "norris",
        "alonso", "schumacher", "vettel", "raikkonen", "button",
        "rosberg", "massa", "webber", "ricciardo", "bottas",
        "russell", "perez", "stroll", "ocon", "gasly"
    ]
    detected_drivers = [d for d in all_drivers if d in question_lower]

    if any(w in question_lower for w in ["career", "overall", "all time", "best", "greatest"]):
        filters["type"] = "career_summary"
    elif any(w in question_lower for w in ["season", "year", "championship"]):
        filters["type"] = "season_summary"
    elif any(w in question_lower for w in ["race", "grand prix", "gp", "specific"]):
        filters["type"] = "race_result"

    if any(w in question_lower for w in ["wet", "rain", "weather"]):
        filters["weather"] = "wet"

    if any(w in question_lower for w in ["street", "monaco", "baku", "singapore", "miami"]):
        filters["circuit_type"] = "street"
    elif any(w in question_lower for w in ["fast", "monza", "spa", "silverstone", "speed"]):
        filters["circuit_type"] = "high_speed"

    return filters, detected_drivers

def smart_retrieve(question, n_results=8):
    """Smart retrieval with metadata filtering"""
    filters, detected_drivers = parse_query(question)
    query_embedding = model.encode(question).tolist()

    where_clause = None
    if filters:
        conditions = []
        for key, value in filters.items():
            conditions.append({key: {"$eq": value}})
        if len(conditions) == 1:
            where_clause = conditions[0]
        elif len(conditions) > 1:
            where_clause = {"$and": conditions}

    try:
        if where_clause:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_clause
            )
        else:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
        chunks = results['documents'][0]
    except Exception:
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        chunks = results['documents'][0]

    # Always include career summary for driver questions
    for driver in detected_drivers:
        career_query = f"{driver.capitalize()} career summary"
        career_embedding = model.encode(career_query).tolist()
        career_results = collection.query(
            query_embeddings=[career_embedding],
            n_results=2,
            where={"type": {"$eq": "career_summary"}}
        )
        if career_results['documents'][0]:
            chunks = career_results['documents'][0] + chunks
            chunks = chunks[:8]

    return chunks