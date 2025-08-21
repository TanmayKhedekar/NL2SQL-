# app_streamlit_queriums_ui.py
import os, re
import pandas as pd
import sqlite3
import streamlit as st
from dotenv import load_dotenv
import cohere
import numpy as np
import plotly.express as px
from streamlit_option_menu import option_menu

# ------------------------------
# Load Cohere API key
# ------------------------------
load_dotenv()
COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
if not COHERE_API_KEY:
    st.warning("⚠️ Missing COHERE_API_KEY in .env")
co = cohere.Client(COHERE_API_KEY)
DEFAULT_MODEL = "command-xlarge"

# ------------------------------
# Initialize SQLite DB
# ------------------------------
@st.cache_resource
def init_db():
    return sqlite3.connect(":memory:", check_same_thread=False)
conn = init_db()

# ------------------------------
# SQL Safety
# ------------------------------
FORBIDDEN = re.compile(r"\b(INSERT|UPDATE|DELETE|ALTER|DROP|TRUNCATE|VACUUM|CREATE|GRANT|REVOKE|COPY|;|\$\$)\b", re.IGNORECASE)
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
# Cohere AI Features
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
    response = co.generate(model=DEFAULT_MODEL, prompt=prompt, max_tokens=300, temperature=0.2)
    return extract_sql(response.generations[0].text)

def summarize_table(df, table_name):
    summary = f"Table '{table_name}' has {df.shape[0]} rows and {df.shape[1]} columns.\n"
    missing_info = df.isna().sum()
    for col, miss in missing_info.items():
        if miss > 0:
            summary += f"- Column '{col}' has {miss} missing values\n"
    summary += f"\nColumns: {', '.join(df.columns)}"
    return summary

def detect_outliers(df):
    numeric_cols = df.select_dtypes(include=np.number).columns
    outliers = {}
    for col in numeric_cols:
        z_scores = (df[col] - df[col].mean()) / df[col].std()
        outlier_rows = df[np.abs(z_scores) > 3]
        if not outlier_rows.empty:
            outliers[col] = len(outlier_rows)
    return outliers

def generate_data_story(df, question):
    prompt = f"""You are a senior data analyst. Given the following query results, generate a short data report.
Query: "{question}"
Data (first 20 rows shown):
{df.head(20).to_dict()}
Return only a concise textual summary highlighting insights, trends, or patterns."""
    response = co.generate(model=DEFAULT_MODEL, prompt=prompt, max_tokens=200, temperature=0.3)
    return response.generations[0].text.strip()

def suggest_queries(schema_text):
    prompt = f"""You are a helpful data analyst. Based on the following database schema, suggest 3 useful SELECT queries a user might want to run:
Schema:
{schema_text}
Return only SQL queries without explanations."""
    response = co.generate(model=DEFAULT_MODEL, prompt=prompt, max_tokens=200, temperature=0.3)
    suggested = response.generations[0].text.strip().split("\n")
    return [q for q in suggested if q.strip()]

def generate_auto_charts(df):
    charts = []
    numeric_cols = df.select_dtypes(include='number').columns
    categorical_cols = df.select_dtypes(include='object').columns
    for col in numeric_cols:
        charts.append(px.histogram(df, x=col, nbins=20, title=f"Distribution of {col}", template="plotly_dark"))
    for col in categorical_cols:
        top_vals = df[col].value_counts().nlargest(10)
        charts.append(px.bar(x=top_vals.index, y=top_vals.values, labels={'x': col, 'y':'Count'}, title=f"Top 10 values in {col}", template="plotly_dark"))
    return charts

# ------------------------------
# Theme & Styling (Gradient + Navbar + Cards)
# ------------------------------
st.set_page_config(page_title="Queriums: NL → SQL Data Explorer", layout="wide")

st.markdown(f"""
<style>
body {{
    background: linear-gradient(135deg, #FF2F92 0%, #6088FF 100%) !important;
    color: white !important;
    font-family: 'Poppins', sans-serif;
}}
.card {{
    background: rgba(0,0,0,0.4);
    backdrop-filter: blur(12px);
    border-radius:18px;
    padding:22px;
    margin-bottom:25px;
    box-shadow:0 8px 32px rgba(0,0,0,0.3);
}}
textarea, input[type="text"] {{
    background-color: #1E1E1F !important;
    color: white !important;
    border-radius: 12px !important;
    padding: 10px !important;
    border: 1px solid #FF2F92 !important;
}}
div.stButton > button {{
    background-color:#FF2F92; color:white; font-weight:600; border-radius:12px;
    padding:10px 18px; border:none; transition:all 0.3s ease; box-shadow:0 6px 22px rgba(255,47,146,0.35);
}}
div.stButton > button:hover {{
    background: linear-gradient(90deg,#FF2F92,#FF85C0);
    transform: scale(1.05);
    box-shadow:0 10px 32px rgba(255,47,146,0.6);
}}
h1,h2,h3,h4 {{
    font-weight:800;
    color:white;
    text-align:center;
}}
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Navbar
# ------------------------------
selected = option_menu(
    menu_title=None,
    options=["Upload Data", "Tables", "Ask Questions"],
    icons=["cloud-upload", "table", "question-circle"],
    default_index=2,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background": "rgba(0,0,0,0.3)"},
        "icon": {"color": "white", "font-size": "18px"},
        "nav-link": {
            "font-size": "16px",
            "text-align": "center",
            "margin": "0px",
            "--hover-color": "#FF85C0",
        },
        "nav-link-selected": {"background-color": "#FF2F92", "color": "white"},
    }
)

# ------------------------------
# Title
# ------------------------------
st.markdown("<h1>💡 Queriums: NL → SQL Data Explorer</h1>", unsafe_allow_html=True)

# ------------------------------
# Page Logic
# ------------------------------
if selected == "Upload Data":
    st.markdown('<div class="card"><h3>📤 Upload CSV or Excel</h3></div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Choose a file", type=["csv","xlsx"])
    table_name = st.text_input("Enter table name","my_table")
    if uploaded_file and table_name:
        if st.button("Upload Table"):
            try:
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
                df.to_sql(table_name, conn, if_exists="replace", index=False)
                st.success(f"Table '{table_name}' uploaded with {len(df)} rows ✅")
            except Exception as e:
                st.error(f"Upload failed: {e}")

elif selected == "Tables":
    st.markdown('<div class="card"><h3>📊 Table Insights & AI Analysis</h3></div>', unsafe_allow_html=True)
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    if not tables.empty:
        selected_table = st.selectbox("Select Table", tables['name'])
        if selected_table:
            df_preview = pd.read_sql(f"SELECT * FROM {selected_table} LIMIT 100", conn)
            st.dataframe(df_preview, use_container_width=True)
            with st.expander("🔍 Dataset Summary & Outlier Detection"):
                st.text(summarize_table(df_preview, selected_table))
                outliers = detect_outliers(df_preview)
                if outliers:
                    st.warning("⚠️ Outliers detected:")
                    for col,count in outliers.items(): st.write(f"- {col}: {count}")
                else: st.success("✅ No significant outliers")
            st.markdown("### 📊 Auto Charts")
            charts = generate_auto_charts(df_preview)
            for fig in charts: st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No tables uploaded yet.")

elif selected == "Ask Questions":
    st.markdown('<div class="card"><h3>❓ Ask a Question (Natural Language → SQL)</h3></div>', unsafe_allow_html=True)
    question = st.text_area("Enter your question (e.g., 'Show top 5 rows of my_table')")
    if st.button("Generate SQL & Run") and question:
        try:
            schema_parts = []
            tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
            for tbl in tables['name']:
                cols = pd.read_sql(f"PRAGMA table_info({tbl})", conn)
                cols_str = ", ".join([f"{c['name']} ({c['type']})" for idx,c in cols.iterrows()])
                schema_parts.append(f"{tbl}: {cols_str}")
            schema_text = "\n".join(schema_parts)
            sql = generate_sql_cohere(question, schema_text)
            sql = enforce_read_only(sql)
            st.subheader("Generated SQL")
            st.code(sql, language="sql")
            df_result = pd.read_sql(sql, conn)
            if not df_result.empty:
                st.subheader("Query Results")
                st.dataframe(df_result, use_container_width=True)
                st.download_button("Download CSV", df_result.to_csv(index=False), "results.csv")
                st.subheader("📄 Data Story")
                st.text(generate_data_story(df_result, question))
                st.subheader("📊 Suggested Queries")
                suggested = suggest_queries(schema_text)
                for q in suggested: st.code(q, language="sql")
                charts = generate_auto_charts(df_result)
                for fig in charts: st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No results found")
        except Exception as e:
            st.error(f"Error: {e}")
