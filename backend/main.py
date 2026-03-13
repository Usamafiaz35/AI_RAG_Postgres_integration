# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from rag_engine import run_question

load_dotenv()

app = FastAPI(title="RAG + Supabase + OpenAI")

# Add CORS middleware to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"                      # all origins (for development only)
    ],
    allow_credentials=True,
    allow_methods=["*"],         # Allow all HTTP methods
    allow_headers=["*"],         # Allow all headers
)

class QueryIn(BaseModel):
    query: str

@app.post("/query")
async def query_endpoint(q: QueryIn):
    """
    Accept JSON: {"query": "What were my total sales last month?"}
    Returns JSON with fields: ok, answer, sql, rows (rows is list of dicts)
    """
    out = run_question(q.query)
    return out

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
