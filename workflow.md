# 🔄 Workflow – NL2SQL Streamlit App

This document explains the **end-to-end workflow** of the NL2SQL Streamlit App.

---

## 1️⃣ Upload Database
- User uploads a `.db` or `.sqlite` file using Streamlit’s **file uploader**.
- The app connects to the uploaded database via **sqlite3**.
- Schema and metadata (tables, columns) are extracted.

---

## 2️⃣ Explore Schema
- The app lists all available **tables** in the database.
- On selecting a table:
  - First few rows are displayed in a **Pandas DataFrame**.
  - Users can inspect structure before writing queries.

---

## 3️⃣ Run SQL Queries
- A text box is provided for users to enter **SQL queries**.
- Queries are executed against the uploaded database.
- Results are shown in an interactive **Streamlit table**.

---

## 4️⃣ Data Visualization
- After running a query, results can be visualized.
- Users select chart type from a dropdown:
  - 📊 Bar chart  
  - 📈 Line chart  
  - 🔵 Scatter plot  
  - 🥧 Pie chart  
- Visualization is built using **Plotly Express**.

---

## 5️⃣ Navigation Flow
Navigation is handled using `streamlit-option-menu`:
- **Home** → Intro & usage guide  
- **Upload DB** → Upload & explore tables  
- **Run Query** → Enter SQL queries & view results  
- **Visualization** → Plot charts from query results  

---

## 6️⃣ CI/CD Workflow (GitHub Actions)
- On every push:
  - Python dependencies are installed  
  - Code is linted using `flake8`  
  - Streamlit app is launched in **headless mode** to ensure no errors  

This ensures the app remains **stable and production-ready**.

---

## 7️⃣ Deployment
- The app is deployed on **Streamlit Cloud**.  
- Live version: 👉 [NL2SQL App](https://queriums.streamlit.app/)  

---

## 📌 Workflow Diagram

```mermaid
flowchart TD
    A[📂 Upload SQLite DB] --> B[🔎 Explore Schema & Tables]
    B --> C[📝 Enter SQL Query]
    C --> D[📋 Query Results in Table]
    D --> E[📊 Visualize with Plotly]
    E --> F[📑 Navigate via Sidebar Menu]
    F --> G[⚙️ CI/CD with GitHub Actions]
    G --> H[🚀 Deploy on Streamlit Cloud]
