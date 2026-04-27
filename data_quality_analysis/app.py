"""
Сервіс: data_quality_analysis
Призначення: перевірка якості даних з БД, збереження звіту
"""

import psycopg2
import pandas as pd
import json
import os
import time
import sys

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "housing")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "admin123")

REPORTS_DIR = "/reports"


def wait_for_data(retries=15, delay=3):
    """Чекає поки data_load заповнить таблицю."""
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                user=DB_USER, password=DB_PASS
            )
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM housing_prices;")
                count = cur.fetchone()[0]
            conn.close()
            if count > 0:
                print(f"[quality] Таблиця містить {count} записів — починаємо аналіз")
                return True
            print(f"[quality] Таблиця порожня, очікування... {i+1}/{retries}")
        except Exception as e:
            print(f"[quality] БД недоступна: {e}, спроба {i+1}/{retries}")
        time.sleep(delay)
    return False


def load_data():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )
    df = pd.read_sql("SELECT * FROM housing_prices;", conn)
    conn.close()
    return df


def analyze(df):
    """Виконує перевірку якості даних."""
    numeric_cols = ["idx_prev_q", "idx_prev_yr_q4", "idx_same_q_prev_yr", "idx_same_period_prev_yr"]

    report = {
        "total_rows": int(len(df)),
        "total_columns": int(len(df.columns)),
        "duplicates": int(df.duplicated(subset=["code", "period"]).sum()),
        "missing_values": {col: int(df[col].isna().sum()) for col in df.columns},
        "missing_pct": {col: round(df[col].isna().mean() * 100, 2) for col in df.columns},
        "unique_codes": sorted(df["code"].unique().tolist()),
        "period_range": {
            "first": df["period"].min(),
            "last": df["period"].max(),
            "total_quarters": int(df["period"].nunique())
        },
        "statistics": {}
    }

    # Діапазони числових колонок
    for col in numeric_cols:
        report["statistics"][col] = {
            "min": round(float(df[col].min()), 2) if not df[col].isna().all() else None,
            "max": round(float(df[col].max()), 2) if not df[col].isna().all() else None,
            "mean": round(float(df[col].mean()), 2) if not df[col].isna().all() else None,
            "anomalies": int(((df[col] < 50) | (df[col] > 200)).sum())
        }

    return report


def save_report(report):
    """Зберігає звіт у JSON файл."""
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, "quality_report.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"[quality] Звіт збережено: {path}")


def save_to_db(report):
    """Зберігає результат перевірки у БД."""
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS quality_report (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT NOW(),
                report_json TEXT
            );
        """)
        cur.execute(
            "INSERT INTO quality_report (report_json) VALUES (%s);",
            (json.dumps(report, ensure_ascii=False),)
        )
        conn.commit()
    conn.close()
    print("[quality] Результат збережено у БД")


def main():
    if not wait_for_data():
        print("[quality] ПОМИЛКА: дані недоступні")
        sys.exit(1)

    df = load_data()
    report = analyze(df)
    save_report(report)
    save_to_db(report)

    print(f"[quality] Рядків: {report['total_rows']}")
    print(f"[quality] Дублікатів: {report['duplicates']}")
    print(f"[quality] Аномалій (idx_prev_q): {report['statistics']['idx_prev_q']['anomalies']}")
    print("[quality] Виконано успішно!")


if __name__ == "__main__":
    main()
