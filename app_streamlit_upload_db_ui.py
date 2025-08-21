# app_streamlit_upload_db_ui_v2.py
import os
import re
import pandas as pd
import sqlite3
import streamlit as st
from io import BytesIO
from dotenv import load_dotenv
import cohere
import time

# ------------------------------
# Load Cohere API key
# ------------------------------
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
if not COHERE_API_KEY:
    st.warning("Missing COHERE_API_KEY in .env")
co = cohere.Client(COHERE_API_KEY)
DEFAULT_MODEL = "command-xlarge"

# ------------------------------
# In-memory SQLite DB
# ------------------------------
@st.cache_resource
def init_db():
    return sqlite3.connect(":memory:", check_same_thread=False)

conn = init_db()

# ------------------------------
# SQL Safety
# ------------------------------
FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|ALTER|DROP|TRUNCATE|VACUUM|CREATE|GRANT|REVOKE|COPY|;|\$\$)\b", re.IGNORECASE
)

def enforce_read_only(sql):
    if FORBIDDEN.search(sql):
        raise ValueError("Forbidden keywords detected in SQL")
    if sql.count(";") > 1:
        raise ValueError("Multiple statements detected; only SELECT allowed")
    if not re.match(r"^\s*SELECT\b", sql, re.IGNORECASE):
        raise ValueError("Only SELECT queries allowed")
    if not re.search(r"\bLIMIT\b", sql, re.IGNORECASE):
        sql = sql.rstrip().rstrip(";") + " LIMIT 100"
    return sql

def extract_sql(text):
    m = re.search(r"```sql\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    return m.group(1).strip() if m else text.strip()

# ------------------------------
# Cohere SQL Generation
# ------------------------------
SYSTEM_RULES = """
You are a senior data analyst that writes safe, syntactically-correct SQLite SELECT queries.
- Use only SELECT queries.
- Do not use multiple statements; return exactly one SQL statement.
- Prefer correct table and column names based on the schema provided.
- If aggregation is requested, include GROUP BY as needed.
- Output SQL only, no prose.
"""

def generate_sql_cohere(question, schema_text):
    prompt = f"{SYSTEM_RULES}\n\nSchema:\n{schema_text}\n\nUser question:\n\"\"\"{question}\"\"\"\nReturn only SQL."
    response = co.generate(
        model=DEFAULT_MODEL,
        prompt=prompt,
        max_tokens=300,
        temperature=0.2,
        stop_sequences=[]
    )
    return extract_sql(response.generations[0].text)

# ------------------------------
# Streamlit UI
# ------------------------------
st.set_page_config(page_title="NL → SQL Explorer", layout="wide", initial_sidebar_state="expanded")
st.title("💡 NL → SQL Data Explorer")

# --- Sidebar ---
with st.sidebar:
    st.header("📂 Database Operations")
    st.markdown("Manage your tables, upload files, and run queries from here.")
    
    api_key_input = st.text_input("Cohere API Key", type="password", value=COHERE_API_KEY)
    if st.button("Update API Key"):
        COHERE_API_KEY = api_key_input
        co = cohere.Client(COHERE_API_KEY)
        st.success("Cohere API key updated")
    
    if st.button("Clear all tables"):
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        for tbl in tables['name']:
            conn.execute(f"DROP TABLE IF EXISTS {tbl}")
        st.success("All tables cleared")

# ------------------------------
# Tabs
# ------------------------------
tab1, tab2, tab3 = st.tabs(["📤 Upload Data", "📊 Tables", "❓ Ask Questions"])

# ------------------------------
# Tab 1: Upload Data
# ------------------------------
with tab1:
    st.subheader("Upload CSV or Excel")
    uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx"])
    table_name = st.text_input("Enter table name", value="my_table")

    if uploaded_file and table_name:
        if st.button("Upload Table"):
            try:
                if uploaded_file.name.endswith(".csv"):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                st.success(f"Table '{table_name}' created with {len(df)} rows")
                st.metric("Rows inserted", len(df))
                st.dataframe(df.head(5))
            except Exception as e:
                st.error(f"Failed to create table: {e}")

# ------------------------------
# Tab 2: Show Tables
# ------------------------------
with tab2:
    st.subheader("Current Tables in Database")
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    if not tables.empty:
        search = st.text_input("Search tables")
        filtered = tables[tables['name'].str.contains(search, case=False)] if search else tables
        st.table(filtered)

        selected_table = st.selectbox("Select table to preview/manage", filtered['name'])
        preview_rows = st.slider("Rows to preview", 1, 20, 5)
        if selected_table:
            df_preview = pd.read_sql(f"SELECT * FROM {selected_table} LIMIT {preview_rows}", conn)
            st.dataframe(df_preview)

            # Delete table
            if st.button(f"🗑 Delete '{selected_table}'"):
                conn.execute(f"DROP TABLE IF EXISTS {selected_table}")
                st.success(f"Table '{selected_table}' deleted")

            # Rename table
            new_name = st.text_input("✏️ Rename table", value=selected_table)
            if st.button("Rename Table"):
                conn.execute(f"ALTER TABLE {selected_table} RENAME TO {new_name}")
                st.success(f"Table renamed to '{new_name}'")
    else:
        st.info("No tables found. Upload your CSV/Excel first.")

# ------------------------------
# Tab 3: NL → SQL
# ------------------------------
with tab3:
    st.subheader("Ask a Question (Natural Language → SQL)")
    question = st.text_area("Enter your question (e.g., 'Show top 5 rows of my_table')")

    if st.button("Generate SQL & Run") and question:
        try:
            # Prepare schema
            schema_parts = []
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
            for tbl in tables['name']:
                cols = pd.read_sql(f"PRAGMA table_info({tbl})", conn)
                cols_str = ", ".join([f"{c['name']} ({c['type']})" for idx, c in cols.iterrows()])
                schema_parts.append(f"{tbl}: {cols_str}")
            schema_text = "\n".join(schema_parts)

            # Generate SQL
            sql = generate_sql_cohere(question, schema_text)
            sql = enforce_read_only(sql)
            st.subheader("Generated SQL")
            st.code(sql, language="sql")

            # Run query
            start = time.time()
            df_result = pd.read_sql(sql, conn)
            end = time.time()
            st.caption(f"Query executed in {end - start:.2f} seconds")

            if not df_result.empty:
                st.subheader("Query Results")
                with st.expander("View full results"):
                    st.dataframe(df_result)
                st.download_button("Download CSV", df_result.to_csv(index=False), "results.csv")
            else:
                st.info("No results found")
        except Exception as e:
            st.error(f"Error: {e}")
