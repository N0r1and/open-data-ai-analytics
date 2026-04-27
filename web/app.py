"""
Сервіс: web
Призначення: Flask веб-інтерфейс для відображення результатів всіх модулів
"""

from flask import Flask, render_template, send_from_directory
import psycopg2
import pandas as pd
import json
import os
import time

app = Flask(__name__)

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "housing")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "admin123")

PLOTS_DIR = "/plots"
REPORTS_DIR = "/reports"


def get_conn():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )


def wait_for_db(retries=20, delay=3):
    for i in range(retries):
        try:
            conn = get_conn()
            conn.close()
            return True
        except:
            time.sleep(delay)
    return False


@app.route("/")
def index():
    """Головна сторінка з коротким описом проєкту."""
    return render_template("index.html")


@app.route("/data")
def data_page():
    """Сторінка з завантаженими даними (перші 50 рядків)."""
    try:
        conn = get_conn()
        df = pd.read_sql(
            "SELECT code, category, period, idx_prev_q FROM housing_prices ORDER BY period LIMIT 50;",
            conn
        )
        conn.close()
        rows = df.values.tolist()
        columns = df.columns.tolist()
        total = pd.read_sql("SELECT COUNT(*) as cnt FROM housing_prices;", get_conn()).iloc[0]["cnt"]
    except Exception as e:
        rows, columns, total = [], [], f"Помилка: {e}"
    return render_template("data.html", rows=rows, columns=columns, total=total)


@app.route("/quality")
def quality_page():
    """Сторінка з результатами перевірки якості."""
    report = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT report_json FROM quality_report ORDER BY created_at DESC LIMIT 1;")
            row = cur.fetchone()
        conn.close()
        if row:
            report = json.loads(row[0])
    except Exception as e:
        report = {"error": str(e)}
    return render_template("quality.html", report=report)


@app.route("/research")
def research_page():
    """Сторінка з результатами дослідницького аналізу."""
    results = None
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT results_json FROM research_results ORDER BY created_at DESC LIMIT 1;")
            row = cur.fetchone()
        conn.close()
        if row:
            results = json.loads(row[0])
    except Exception as e:
        results = {"error": str(e)}
    return render_template("research.html", results=results)


@app.route("/visualization")
def visualization_page():
    """Сторінка з графіками."""
    plots = []
    for fname in ["fig1_overall_trend.png", "fig2_primary_vs_secondary.png",
                  "fig3_seasonality.png", "fig4_heatmap.png"]:
        if os.path.exists(os.path.join(PLOTS_DIR, fname)):
            plots.append(fname)
    return render_template("visualization.html", plots=plots)


@app.route("/plots/<filename>")
def serve_plot(filename):
    """Віддає PNG файли графіків."""
    return send_from_directory(PLOTS_DIR, filename)


if __name__ == "__main__":
    wait_for_db()
    app.run(host="0.0.0.0", port=5000, debug=False)
