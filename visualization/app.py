"""
Сервіс: visualization
Призначення: побудова графіків на основі даних з БД, збереження PNG
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import psycopg2
import pandas as pd
import os
import time
import sys

DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "housing")
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "admin123")

PLOTS_DIR = "/plots"

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"font.family": "DejaVu Sans", "figure.dpi": 120})


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
                return True
            print(f"[viz] Очікування даних... {i+1}/{retries}")
        except Exception as e:
            print(f"[viz] БД недоступна: {e}, спроба {i+1}/{retries}")
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


def get_cat(df, code):
    return df[df["code"] == code].sort_values("period").reset_index(drop=True)


def xticks(periods, step=4):
    return [p if i % step == 0 else "" for i, p in enumerate(periods)]


def plot_overall_trend(df):
    data = get_cat(df, "010").dropna(subset=["idx_prev_q"])
    periods = data["period"].tolist()
    values  = data["idx_prev_q"].tolist()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(range(len(periods)), values, marker="o", markersize=4,
            linewidth=1.8, color="#2E75B6", label="Індекс до попереднього кварталу")
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.7)

    if "2022 Q1" in periods:
        wi = periods.index("2022 Q1")
        ax.axvline(wi, color="red", linestyle=":", linewidth=1.5, label="24.02.2022")
        ax.annotate("Вторгнення", xy=(wi, max(values)*0.97),
                    fontsize=8, color="red", ha="center")

    ax.set_xticks(range(len(periods)))
    ax.set_xticklabels(xticks(periods), rotation=45, ha="right", fontsize=8)
    ax.set_title("Загальний індекс цін на житло (до попереднього кварталу)")
    ax.set_ylabel("Індекс, %")
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "fig1_overall_trend.png")
    plt.savefig(path)
    plt.close()
    print(f"[viz] Збережено: {path}")


def plot_primary_vs_secondary(df):
    p1 = get_cat(df, "100").dropna(subset=["idx_same_q_prev_yr"])
    p2 = get_cat(df, "200").dropna(subset=["idx_same_q_prev_yr"])
    common = sorted(set(p1["period"]) & set(p2["period"]))
    v1 = p1[p1["period"].isin(common)].set_index("period")["idx_same_q_prev_yr"]
    v2 = p2[p2["period"].isin(common)].set_index("period")["idx_same_q_prev_yr"]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(range(len(common)), v1.values, marker="s", markersize=4,
            linewidth=1.8, color="#2E75B6", label="Первинний ринок")
    ax.plot(range(len(common)), v2.values, marker="^", markersize=4,
            linewidth=1.8, color="#ED7D31", label="Вторинний ринок")
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xticks(range(len(common)))
    ax.set_xticklabels(xticks(common), rotation=45, ha="right", fontsize=8)
    ax.set_title("Первинний vs Вторинний ринок")
    ax.set_ylabel("Індекс, %")
    ax.legend(fontsize=9)
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "fig2_primary_vs_secondary.png")
    plt.savefig(path)
    plt.close()
    print(f"[viz] Збережено: {path}")


def plot_seasonality(df):
    data = get_cat(df, "010").dropna(subset=["idx_prev_q"]).copy()
    data["quarter"] = "Q" + data["period"].str.extract(r"Q(\d)")[0]

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=data, x="quarter", y="idx_prev_q", palette="Blues",
                ax=ax, order=["Q1","Q2","Q3","Q4"])
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_title("Сезонність: розподіл індексу по кварталах")
    ax.set_ylabel("Індекс, %")
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "fig3_seasonality.png")
    plt.savefig(path)
    plt.close()
    print(f"[viz] Збережено: {path}")


def plot_heatmap(df):
    pv = df.copy()
    pv["year"] = pv["period"].str[:4]
    pv = pv[pv["code"] != "010"].dropna(subset=["idx_same_q_prev_yr"])
    label_map = {
        "100": "Первинний (заг.)", "101": "Первинний 1к",
        "102": "Первинний 2к",     "103": "Первинний 3к",
        "200": "Вторинний (заг.)", "201": "Вторинний 1к",
        "202": "Вторинний 2к",     "203": "Вторинний 3к",
    }
    pv["label"] = pv["code"].map(label_map)
    heat = pv.groupby(["label","year"])["idx_same_q_prev_yr"].mean().unstack()

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(heat, annot=True, fmt=".1f", cmap="RdYlGn", center=100,
                linewidths=0.5, ax=ax, cbar_kws={"label": "Індекс, %"})
    ax.set_title("Середній річний індекс цін по категоріях")
    plt.tight_layout()
    path = os.path.join(PLOTS_DIR, "fig4_heatmap.png")
    plt.savefig(path)
    plt.close()
    print(f"[viz] Збережено: {path}")


def main():
    os.makedirs(PLOTS_DIR, exist_ok=True)

    if not wait_for_data():
        print("[viz] ПОМИЛКА: дані недоступні")
        sys.exit(1)

    df = load_data()
    plot_overall_trend(df)
    plot_primary_vs_secondary(df)
    plot_seasonality(df)
    plot_heatmap(df)
    print("[viz] Всі графіки побудовано!")


if __name__ == "__main__":
    main()
