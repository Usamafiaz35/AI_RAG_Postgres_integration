# db.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

load_dotenv()

USER = os.getenv("SUPABASE_USER")
PASSWORD = os.getenv("SUPABASE_PASSWORD")
HOST = os.getenv("SUPABASE_HOST")
PORT = os.getenv("SUPABASE_PORT", "5432")
DATABASE = os.getenv("SUPABASE_DATABASE", "postgres")

if not (USER and PASSWORD and HOST):
    raise RuntimeError("Set SUPABASE_USER, SUPABASE_PASSWORD, SUPABASE_HOST in .env")

# Use the psycopg2 driver and require SSL
DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DATABASE}?sslmode=require"

# Create engine (SQLAlchemy 2.0 style)
engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)

def run_read_query(sql: str, params: dict | None = None, fetchone: bool = False):
    """
    Execute a read-only SQL query and return rows as list[dict]
    Params must be a dict for parameterized queries.
    """
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        cols = result.keys()
        rows = [dict(zip(cols, r)) for r in result.fetchall()]
        if fetchone:
            return rows[0] if rows else None
        return rows
