"""
Модуль: visualization.py
Призначення: побудова та збереження графіків для аналізу індексів цін на житло
Важливо: використовує matplotlib backend 'Agg' — працює без GUI (в CI середовищі)
"""

import matplotlib
matplotlib.use("Agg")  # ОБОВ'ЯЗКОВО для CI — без цього впаде на сервері без дисплею

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import sys

DATA_FILE   = os.path.join("data", "housing_prices_clean.csv")
OUTPUT_DIR  = os.path.join("artifacts", "visualization")

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "figure.dpi": 120,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
})


def load_data() -> pd.DataFrame:
    if not os.path.exists(DATA_FILE):
        print(f"[viz] ПОМИЛКА: файл не знайдено — {DATA_FILE}")
        sys.exit(1)
    return pd.read_csv(DATA_FILE, dtype={"code": str})


def get_category(df: pd.DataFrame, code: str) -> pd.DataFrame:
    return df[df["code"] == code].sort_values("period").reset_index(drop=True)


def xtick_labels(periods, step=4):
    return [p if i % step == 0 else "" for i, p in enumerate(periods)]


def plot_overall_trend(df: pd.DataFrame) -> None:
    """Графік 1: Загальний індекс цін з позначкою вторгнення."""
    data = get_category(df, "010").dropna(subset=["idx_prev_q"])
    periods = data["period"].tolist()
    values  = data["idx_prev_q"].tolist()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(range(len(periods)), values, marker="o", markersize=4,
            linewidth=1.8, color="#2E75B6", label="Індекс до попереднього кварталу")
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.7, label="Базова лінія (100%)")

    war_idx = periods.index("2022 Q1") if "2022 Q1" in periods else None
    if war_idx is not None:
        ax.axvline(war_idx, color="red", linestyle=":", linewidth=1.5, label="24.02.2022")
        ax.annotate("Повномасштабне\nвторгнення",
                    xy=(war_idx, max(values) * 0.97),
                    fontsize=8, color="red", ha="center")

    ax.set_xticks(range(len(periods)))
    ax.set_xticklabels(xtick_labels(periods, step=4), rotation=45, ha="right", fontsize=8)
    ax.set_title("Загальний індекс цін на житло (до попереднього кварталу)")
    ax.set_ylabel("Індекс, %")
    ax.set_xlabel("Квартал")
    ax.legend(fontsize=9)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    plt.tight_layout()

    path = os.path.join(OUTPUT_DIR, "fig1_overall_trend.png")
    plt.savefig(path)
    plt.close()
    print(f"[viz] Збережено: {path}")


def plot_primary_vs_secondary(df: pd.DataFrame) -> None:
    """Графік 2: Первинний vs Вторинний ринок."""
    primary   = get_category(df, "100").dropna(subset=["idx_same_q_prev_yr"])
    secondary = get_category(df, "200").dropna(subset=["idx_same_q_prev_yr"])

    common = sorted(set(primary["period"]) & set(secondary["period"]))
    p1 = primary[primary["period"].isin(common)].set_index("period")["idx_same_q_prev_yr"]
    p2 = secondary[secondary["period"].isin(common)].set_index("period")["idx_same_q_prev_yr"]

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(range(len(common)), p1.values, marker="s", markersize=4,
            linewidth=1.8, color="#2E75B6", label="Первинний ринок")
    ax.plot(range(len(common)), p2.values, marker="^", markersize=4,
            linewidth=1.8, color="#ED7D31", label="Вторинний ринок")
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.7)

    ax.set_xticks(range(len(common)))
    ax.set_xticklabels(xtick_labels(common, step=4), rotation=45, ha="right", fontsize=8)
    ax.set_title("Індекс цін: первинний vs вторинний ринок")
    ax.set_ylabel("Індекс, %")
    ax.set_xlabel("Квартал")
    ax.legend(fontsize=9)
    plt.tight_layout()

    path = os.path.join(OUTPUT_DIR, "fig2_primary_vs_secondary.png")
    plt.savefig(path)
    plt.close()
    print(f"[viz] Збережено: {path}")


def plot_seasonality_boxplot(df: pd.DataFrame) -> None:
    """Графік 3: Boxplot сезонності."""
    data = get_category(df, "010").dropna(subset=["idx_prev_q"]).copy()
    data["quarter"] = "Q" + data["period"].str.extract(r"Q(\d)")[0]

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=data, x="quarter", y="idx_prev_q", palette="Blues", ax=ax,
                order=["Q1", "Q2", "Q3", "Q4"])
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_title("Сезонність: розподіл квартального індексу")
    ax.set_ylabel("Індекс до попереднього кварталу, %")
    ax.set_xlabel("Квартал")
    plt.tight_layout()

    path = os.path.join(OUTPUT_DIR, "fig3_seasonality_boxplot.png")
    plt.savefig(path)
    plt.close()
    print(f"[viz] Збережено: {path}")


def plot_heatmap_by_year(df: pd.DataFrame) -> None:
    """Графік 4: Теплова карта по роках і категоріях."""
    pivot_df = df.copy()
    pivot_df["year"] = pivot_df["period"].str[:4]
    pivot_df = pivot_df.dropna(subset=["idx_same_q_prev_yr"])
    pivot_df = pivot_df[pivot_df["code"] != "010"]

    label_map = {
        "100": "Первинний (заг.)", "101": "Первинний 1к",
        "102": "Первинний 2к",     "103": "Первинний 3к",
        "200": "Вторинний (заг.)", "201": "Вторинний 1к",
        "202": "Вторинний 2к",     "203": "Вторинний 3к",
    }
    pivot_df["label"] = pivot_df["code"].map(label_map)
    heat = pivot_df.groupby(["label", "year"])["idx_same_q_prev_yr"].mean().unstack()

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(heat, annot=True, fmt=".1f", cmap="RdYlGn", center=100,
                linewidths=0.5, ax=ax, cbar_kws={"label": "Індекс, %"})
    ax.set_title("Середній річний індекс цін на житло по категоріях")
    ax.set_xlabel("Рік")
    ax.set_ylabel("")
    plt.tight_layout()

    path = os.path.join(OUTPUT_DIR, "fig4_heatmap_by_year.png")
    plt.savefig(path)
    plt.close()
    print(f"[viz] Збережено: {path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = load_data()

    print("[viz] Будуємо графіки...")
    plot_overall_trend(df)
    plot_primary_vs_secondary(df)
    plot_seasonality_boxplot(df)
    plot_heatmap_by_year(df)

    print(f"\n[viz] Всі графіки збережено у: {OUTPUT_DIR}/")
    print("[viz] Виконано успішно.")


if __name__ == "__main__":
    main()
