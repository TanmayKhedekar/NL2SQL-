Got it 👍 since you’ve deployed your app at **[https://queriums.streamlit.app/](https://queriums.streamlit.app/)**, we can add a nice **launch badge** and link in your README.

Here’s the updated **README.md** with deployment info added:

---

```markdown
# 🚀 NL2SQL Streamlit App

## 🌟 Introduction
Databases are powerful, but writing SQL queries can feel overwhelming for many users.  
To make this process easier, I built a **Streamlit application** that allows users to:

- Upload their own SQLite database  
- Interactively explore tables  
- Run SQL queries easily  
- Visualize query results with **Plotly**  

👉 **Try it live here:**  
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://queriums.streamlit.app/)

---

## 🛠️ Tech Stack
The app uses some amazing open-source tools:

- **[Streamlit](https://streamlit.io/):** For building the interactive UI quickly  
- **Pandas:** For handling dataframes & SQL results  
- **SQLite:** Lightweight database engine for uploads  
- **Plotly:** For interactive charts  
- **streamlit-option-menu:** Sidebar navigation menu for clean UI  

---

## 📂 Project Structure
```

.
├── app\_streamlit\_upload\_db\_ui.py   # Main Streamlit app
├── requirements.txt                # Python dependencies
└── .github/workflows/streamlit.yml # GitHub Actions workflow (CI/CD)

````

---

## 🚀 Features
✅ Upload SQLite database files  
✅ Browse tables and schema  
✅ Write & execute SQL queries directly inside the app  
✅ Visualize results as interactive plots (bar, line, scatter, etc.)  
✅ Clean sidebar navigation  

---

## ⚡ Setup & Run Locally

### 1. Clone repo
```bash
git clone https://github.com/your-username/nl2sql-.git
cd nl2sql-
````

### 2. (Optional) Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Streamlit app

```bash
streamlit run app_streamlit_upload_db_ui.py
```

Then open [http://localhost:8501](http://localhost:8501) 🎉

---

## 🔄 CI/CD with GitHub Actions

This project includes a **GitHub Actions workflow** (`.github/workflows/streamlit.yml`) that:

* Installs dependencies
* Lints code with **flake8**
* Runs the Streamlit app in headless mode to ensure it launches

---

## 💡 Learnings

* Streamlit makes it incredibly fast to prototype and build full apps
* SQLite is lightweight but powerful enough for many real use cases
* Automating with GitHub Actions saves time and ensures consistency

---

## 📌 Next Steps

* Add **NL2SQL (natural language to SQL)** support using LLMs
* Enhance visualization features further

---

## 📜 License

This project is licensed under the **MIT License**.

---

```

---

✅ Now your README shows a **badge + direct link** to the deployed app.  

Do you also want me to add a **demo GIF or screenshots** section so that GitHub visitors see how your app looks before clicking?
```
