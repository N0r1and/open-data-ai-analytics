"""
Сервіс: data_research
Призначення: статистичний аналіз даних з БД, збереження результатів
"""

import psycopg2
import pandas as pd
import json
import os
import time
import sys
from scipy import stats

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "housing")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "admin123")

REPORTS_DIR = "/reports"


def wait_for_data(retries=15, delay=3):
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
                print(f"[research] Таблиця містить {count} записів")
                return True
            print(f"[research] Очікування даних... {i+1}/{retries}")
        except Exception as e:
            print(f"[research] БД недоступна: {e}, спроба {i+1}/{retries}")
        time.sleep(delay)
    return False


def load_data():
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )
    df = pd.read_sql("SELECT * FROM housing_prices ORDER BY period;", conn)
    conn.close()
    return df


def hypothesis_1(df):
    """Вплив вторгнення 2022 на ціни (t-тест)."""
    overall = df[df["code"] == "010"].dropna(subset=["idx_prev_q"])
    before = overall[overall["period"] < "2022 Q1"]["idx_prev_q"]
    after  = overall[overall["period"] >= "2022 Q1"]["idx_prev_q"]
    t, p = stats.ttest_ind(before, after)
    return {
        "name": "Вплив вторгнення 2022",
        "mean_before": round(float(before.mean()), 2),
        "mean_after": round(float(after.mean()), 2),
        "t_stat": round(float(t), 3),
        "p_value": round(float(p), 4),
        "significant": bool(p < 0.05),
        "conclusion": "Різниця статистично значуща" if p < 0.05 else "Різниця не значуща"
    }


def hypothesis_2(df):
    """Первинний vs вторинний ринок (тест Манна-Уітні)."""
    primary   = df[df["code"] == "100"]["idx_prev_q"].dropna()
    secondary = df[df["code"] == "200"]["idx_prev_q"].dropna()
    u, p = stats.mannwhitneyu(primary, secondary, alternative="greater")
    return {
        "name": "Первинний vs Вторинний ринок",
        "mean_primary": round(float(primary.mean()), 2),
        "mean_secondary": round(float(secondary.mean()), 2),
        "u_stat": round(float(u), 1),
        "p_value": round(float(p), 4),
        "significant": bool(p < 0.05),
        "conclusion": "Первинний ринок зростає швидше" if p < 0.05 else "Суттєвої різниці немає"
    }


def hypothesis_3(df):
    """Сезонність по кварталах (ANOVA)."""
    overall = df[df["code"] == "010"].copy()
    overall["quarter"] = overall["period"].str.extract(r"Q(\d)").astype(int)
    groups = [overall[overall["quarter"] == q]["idx_prev_q"].dropna() for q in [1,2,3,4]]
    means = {f"Q{i+1}": round(float(g.mean()), 2) for i, g in enumerate(groups)}
    f, p = stats.f_oneway(*groups)
    return {
        "name": "Сезонність по кварталах",
        "means_by_quarter": means,
        "f_stat": round(float(f), 3),
        "p_value": round(float(p), 4),
        "significant": bool(p < 0.05),
        "conclusion": "Сезонність існує" if p < 0.05 else "Сезонності не виявлено"
    }


def basic_stats(df):
    """Базові статистики по загальному індексу."""
    overall = df[df["code"] == "010"]["idx_prev_q"].dropna()
    return {
        "count": int(len(overall)),
        "mean": round(float(overall.mean()), 2),
        "median": round(float(overall.median()), 2),
        "std": round(float(overall.std()), 2),
        "min": round(float(overall.min()), 2),
        "max": round(float(overall.max()), 2),
    }


def save_to_db(results):
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASS
    )
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS research_results (
                id SERIAL PRIMARY KEY,
                created_at TIMESTAMP DEFAULT NOW(),
                results_json TEXT
            );
        """)
        cur.execute(
            "INSERT INTO research_results (results_json) VALUES (%s);",
            (json.dumps(results, ensure_ascii=False),)
        )
        conn.commit()
    conn.close()
    print("[research] Результати збережено у БД")


def save_to_file(results):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    path = os.path.join(REPORTS_DIR, "research_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"[research] Результати збережено: {path}")


def main():
    if not wait_for_data():
        print("[research] ПОМИЛКА: дані недоступні")
        sys.exit(1)

    df = load_data()

    results = {
        "basic_stats": basic_stats(df),
        "hypotheses": [
            hypothesis_1(df),
            hypothesis_2(df),
            hypothesis_3(df),
        ]
    }

    save_to_file(results)
    save_to_db(results)

    for h in results["hypotheses"]:
        print(f"[research] {h['name']}: {h['conclusion']} (p={h['p_value']})")

    print("[research] Виконано успішно!")


if __name__ == "__main__":
    main()
