# app_snippet_streamlit.py
import streamlit as st
import pandas as pd
from sqlite_helpers import connect, list_tables, table_info, sample_rows, fetch_all, is_select_only

st.set_page_config(page_title="Queriums: NL → SQL Data Explorer", layout="wide")

st.title("Queriums: NL → SQL Data Explorer")

uploaded = st.file_uploader("Upload a SQLite .db/.sqlite file", type=["db", "sqlite"])
if uploaded:
    # Save to a temporary file
    tmp_path = f"/tmp/{uploaded.name}"
    with open(tmp_path, "wb") as f:
        f.write(uploaded.getbuffer())

    conn = connect(tmp_path)
    tabs = st.tabs(["📚 Tables", "🔎 Schema", "📝 Query", "👀 Preview"])
    
    with tabs[0]:
        tables = list_tables(conn)
        st.write("**Tables:**", tables if tables else "_No tables found_")

    with tabs[1]:
        t = st.selectbox("Select table", list_tables(conn))
        if t:
            st.write(pd.DataFrame(table_info(conn, t)))

    with tabs[3]:
        t2 = st.selectbox("Preview table", list_tables(conn), key="preview")
        if t2:
            st.dataframe(pd.DataFrame(sample_rows(conn, t2)))

    with tabs[2]:
        q = st.text_area("Enter SELECT query (read-only)", "SELECT * FROM sqlite_master LIMIT 10")
        if st.button("Run"):
            if is_select_only(q):
                rows = fetch_all(conn, q)
                st.dataframe(pd.DataFrame(rows))
            else:
                st.error("Only single SELECT statements are allowed here for safety.")




# Sqlite.py

import sqlite3
from contextlib import closing
from typing import Iterable, Tuple, Any, List, Dict, Optional

def connect(db_path: str) -> sqlite3.Connection:
    """Create a connection with sensible defaults."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # dict-like rows
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def exec_many(conn: sqlite3.Connection, sql: str, rows: Iterable[Tuple[Any, ...]]):
    """Efficient bulk insert/update."""
    with conn:
        conn.executemany(sql, rows)

def exec_one(conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...] = ()):
    """Execute a single statement (DDL or DML)."""
    with conn:
        conn.execute(sql, params)

def fetch_all(conn: sqlite3.Connection, sql: str, params: Tuple[Any, ...] = ()) -> List[Dict[str, Any]]:
    """Run a SELECT and return list of dicts."""
    with closing(conn.cursor()) as cur:
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

def is_select_only(query: str) -> bool:
    """Very light guardrail: allow only SELECT statements."""
    q = query.strip().lower()
    return q.startswith("select") and ";" not in q[6:]  # no stacked statements

# ----- Schema helpers -----
def list_tables(conn) -> List[str]:
    rows = fetch_all(conn, """
      SELECT name FROM sqlite_master
      WHERE type='table' AND name NOT LIKE 'sqlite_%'
      ORDER BY name;
    """)
    return [r["name"] for r in rows]

def table_info(conn, table: str) -> List[Dict[str, Any]]:
    return fetch_all(conn, f"PRAGMA table_info({table});")

def sample_rows(conn, table: str, limit: int = 10) -> List[Dict[str, Any]]:
    return fetch_all(conn, f"SELECT * FROM {table} LIMIT {limit};")

# ----- Simple CRUD -----
def create_table_example(conn):
    exec_one(conn, """
      CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      );
    """)

def insert_customer(conn, name: str, email: Optional[str]):
    exec_one(conn, "INSERT INTO customers(name, email) VALUES (?, ?);", (name, email))

def update_customer_email(conn, cid: int, email: str):
    exec_one(conn, "UPDATE customers SET email = ? WHERE id = ?;", (email, cid))

def delete_customer(conn, cid: int):
    exec_one(conn, "DELETE FROM customers WHERE id = ?;", (cid,))

# ----- CSV -> SQLite -----
def load_csv_to_table(conn, csv_path: str, table_name: str):
    import pandas as pd
    df = pd.read_csv(csv_path)
    df.to_sql(table_name, conn, if_exists="replace", index=False)
