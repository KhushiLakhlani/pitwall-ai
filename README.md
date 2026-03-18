# 🏎️ PitWall AI — F1 Driver Performance Intelligence

An AI-powered chatbot that answers deep questions about Formula 1 drivers using 25 years of race data (2000–2025), built with a full RAG (Retrieval-Augmented Generation) pipeline.

## 🔍 What It Does

- **Ask natural language questions** about any F1 driver — *"How does Verstappen perform in wet conditions?"*
- **Driver stats dashboard** — wins, podiums, wet race record, street circuit performance
- **Head-to-head comparison** — AI-powered analysis of any two drivers
- **All-time leaderboard** — win leaders from 2000 to 2025

## 🏗️ Architecture
```
User Question
    ↓
Smart Query Parser (detects driver, conditions, circuit type)
    ↓
ChromaDB Vector Search (10,289 embedded chunks)
    ↓
Top 8 Relevant Chunks Retrieved
    ↓
Groq LLM (Llama 3.3 70B) — synthesizes answer
    ↓
Data-backed answer with sources
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq API (Llama 3.3 70B) |
| Embeddings | HuggingFace sentence-transformers |
| Vector DB | ChromaDB |
| RAG Framework | LangChain |
| Backend | FastAPI + Python |
| Frontend | React |
| Data Source | Jolpica F1 API (Ergast successor) |

## 📊 Dataset

- **10,550 race results** across 25 seasons (2000–2025)
- **8,600+ qualifying results** with Q1/Q2/Q3 lap times
- **455 races** tagged with weather (wet/dry/mixed) and circuit type
- **10,289 vector chunks** — race results, season summaries, career summaries

## 🚀 Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (free at console.groq.com)

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Add your Groq API key to .env
echo "GROQ_API_KEY=your_key_here" > .env

# Run the data pipeline (first time only)
python pipeline/ingest.py
python pipeline/ingest_quali.py
python pipeline/ingest_weather.py
python pipeline/process.py
python pipeline/chunk.py
python pipeline/embed.py

# Start the API
python -m uvicorn api.main:app --reload
```

### Frontend
```bash
cd pitwall-ui
npm install
npm start
```

Open http://localhost:3000

## 💡 Sample Questions
- *"How does Max Verstappen perform in wet conditions?"*
- *"Who is the best driver at street circuits?"*
- *"Compare Hamilton and Schumacher's career records"*
- *"Which driver gained the most positions on average in races?"*

## 📁 Project Structure
```
pitwall-ai/
├── pipeline/
│   ├── ingest.py          # Race results data pipeline
│   ├── ingest_quali.py    # Qualifying data pipeline
│   ├── ingest_weather.py  # Weather + calendar pipeline
│   ├── process.py         # Data merging + feature engineering
│   ├── chunk.py           # Document chunking strategy
│   └── embed.py           # Vector embedding + ChromaDB storage
├── rag/
│   ├── retriever.py       # Smart hybrid retrieval
│   └── chain.py           # RAG chain (test script)
├── api/
│   └── main.py            # FastAPI REST API
├── pitwall-ui/
│   └── src/App.js         # React frontend
└── data/
    ├── raw/               # Raw API data
    ├── processed/         # Master dataset
    └── chunks/            # JSON chunks
```
