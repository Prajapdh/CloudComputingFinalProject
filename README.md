# Cloud Computing Final Project: Retail Data Analysis Dashboard

## 📖 Project Overview

This project is the final group assignment for Cloud Computing. It demonstrates end-to-end retail data ingestion, processing, visualization, and basic machine learning on anonymized household transaction data (400 households, 2 years of transactions). Built with Python/Flask and deployed as a web application, it provides:

- **User Authentication** (Register / Login / Logout)  
- **Persistent User Storage** via SQLite & SQLAlchemy  
- **Data Ingestion** from CSVs (Transactions, Households, Products)  
- **Interactive Dashboard**  
  - Sample data pull for `HSHD_NUM = 10`  
  - Filter by any `HSHD_NUM`  
  - Scatter plot of Household Size vs. Total Spend  
  - Loading spinner feedback during long uploads  
- **Static Notebook Embed** (read-only export of Jupyter analysis)  
- **CSV Upload & Dynamic Reload** of new data  

---

## 🏗️ Directory Structure

```
├── 8451_The_Complete_Journey_2_Sample-2-1/ # Original data zip (git-ignored) ├── app/ 
│ ├── flaskapp.py # Flask application entrypoint 
│ ├── requirements.txt # App-specific dependencies 
│ ├── users.db # SQLite DB (auto-generated) 
│ ├── uploads/ # Uploaded CSVs (git-ignored) 
│ │ ├── 400_households.csv 
│ │ ├── 400_products.csv 
│ │ └── 400_transactions.csv 
│ ├── static/ 
│ │ └── notebook.html # Static export of Jupyter notebook 
│ └── templates/ 
│   ├── base.html 
│   ├── home.html 
│   ├── register.html 
│   ├── login.html 
│   ├── success.html 
│   ├── index.html 
│   └── notebook_view.html 
├── .gitignore 
└── README.md
```

---

## 🚀 Getting Started

### 1. Clone & Enter Directory
```bash
git clone https://github.com/Prajapdh/CloudComputingFinalProject.git
cd CloudComputingFinalProject
```

### 2. Create & Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the App Locally
```bash
cd app
python flaskapp.py
```
Open your browser at `http://127.0.0.1:5000/`

---

## 🔧 Usage

1. **Register** a new user (Username, Password, First/Last Name, Email).  
2. **Login** to access the dashboard.  
3. **View Sample Pull** for household `10`.  
4. **Filter** by entering any `HSHD_NUM` and clicking **Search**.  
5. **Upload** updated CSVs (Transactions, Households, Products) and watch the loading spinner.  
6. **Navigate** to **Notebook** from the header to see a static read-only version of the Jupyter analysis.

---

## 📂 Data Files

> **Note:** The raw CSVs (`400_transactions.csv`, etc.) are **not** committed to Git due to their size.  
> Place them in the project root or `uploads/` folder before first run, or upload via the dashboard.

---

## 📓 Static Notebook Embed

We exported our analysis notebook (`FinalProjectLinearReg.ipynb`) to `static/notebook.html`.  
Navigate to `/notebook` in the app to browse the full, read-only analysis.

---

## 🛠️ Deployment

You can deploy this app to any WSGI-compatible host. For Azure App Service:

1. Provision a **Free** Linux Web App.  
2. Push this code to a GitHub repo and enable **Continuous Deployment**.  
3. Set application setting `SCM_DO_BUILD_DURING_DEPLOYMENT = true` to install `requirements.txt`.  
4. Ensure you have an **App Setting** for `SECRET_KEY`.  

---

## 🧑‍💻 Team Members

- Daksh Prajapati  
- Varad Parte  
- Jalin Solankee  

---
