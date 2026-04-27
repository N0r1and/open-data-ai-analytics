"""
Сервіс: data_load
Призначення: читає XLSX датасет, створює таблицю у PostgreSQL, завантажує дані
"""

import pandas as pd
import psycopg2
from psycopg2 import sql
import os
import time
import sys

# Параметри підключення з змінних середовища
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "housing")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "admin123")

DATA_FILE = "/data/129-indeksi-tsin-na-zhitlo.xlsx"


def wait_for_db(retries=10, delay=3):
    """Чекає поки PostgreSQL буде готовий приймати з'єднання."""
    for i in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                user=DB_USER, password=DB_PASS
            )
            conn.close()
            print("[data_load] БД готова!")
            return True
        except psycopg2.OperationalError:
            print(f"[data_load] Очікування БД... спроба {i+1}/{retries}")
            time.sleep(delay)
    return False


def load_and_clean():
    """Завантажує та очищає датасет."""
    print(f"[data_load] Читання файлу: {DATA_FILE}")
    df = pd.read_excel(DATA_FILE, sheet_name="Індекси цін на житло.ua", header=1, skiprows=[2])
    df.columns = ["code", "category", "period", "idx_prev_q",
                  "idx_prev_yr_q4", "idx_same_q_prev_yr", "idx_same_period_prev_yr"]
    df.replace("NA", None, inplace=True)

    numeric_cols = ["idx_prev_q", "idx_prev_yr_q4", "idx_same_q_prev_yr", "idx_same_period_prev_yr"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["code"] = df["code"].astype(str).str.strip()
    df.dropna(subset=["code", "period"], inplace=True)
    print(f"[data_load] Завантажено {len(df)} рядків")
    return df


def create_table(conn):
    """Створює таблицю housing_prices якщо не існує."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS housing_prices (
                id SERIAL PRIMARY KEY,
                code VARCHAR(10),
                category VARCHAR(200),
                period VARCHAR(20),
                idx_prev_q FLOAT,
                idx_prev_yr_q4 FLOAT,
                idx_same_q_prev_yr FLOAT,
                idx_same_period_prev_yr FLOAT
            );
        """)
        cur.execute("TRUNCATE TABLE housing_prices RESTART IDENTITY;")
        conn.commit()
    print("[data_load] Таблиця housing_prices створена/очищена")


def insert_data(conn, df):
    """Завантажує дані у таблицю."""
    with conn.cursor() as cur:
        for _, row in df.iterrows():
            cur.execute("""
                INSERT INTO housing_prices
                    (code, category, period, idx_prev_q, idx_prev_yr_q4,
                     idx_same_q_prev_yr, idx_same_period_prev_yr)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                row["code"], row["category"], row["period"],
                row["idx_prev_q"] if pd.notna(row["idx_prev_q"]) else None,
                row["idx_prev_yr_q4"] if pd.notna(row["idx_prev_yr_q4"]) else None,
                row["idx_same_q_prev_yr"] if pd.notna(row["idx_same_q_prev_yr"]) else None,
                row["idx_same_period_prev_yr"] if pd.notna(row["idx_same_period_prev_yr"]) else None,
            ))
        conn.commit()
    print(f"[data_load] Завантажено {len(df)} записів у БД")


def main():
    if not wait_for_db():
        print("[data_load] ПОМИЛКА: БД недоступна")
        sys.exit(1)

    df = load_and_clean()

    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )
    try:
        create_table(conn)
        insert_data(conn, df)
        print("[data_load] Виконано успішно!")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
