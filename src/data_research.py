"""
Модуль: data_research.py
Призначення: дослідницький аналіз — перевірка гіпотез, статистика, тренди
"""

import pandas as pd
import numpy as np
from scipy import stats
import os
import sys

DATA_FILE = os.path.join("data", "housing_prices_clean.csv")
ARTIFACTS_DIR = os.path.join("artifacts", "data_research")


def load_data() -> pd.DataFrame:
    if not os.path.exists(DATA_FILE):
        print(f"[research] ПОМИЛКА: файл не знайдено — {DATA_FILE}")
        sys.exit(1)
    df = pd.read_csv(DATA_FILE, dtype={"code": str})

    def period_to_float(p):
        year, q = p.split(" Q")
        return int(year) + (int(q) - 1) * 0.25

    df["time"] = df["period"].apply(period_to_float)
    return df


def get_category(df: pd.DataFrame, code: str) -> pd.DataFrame:
    return df[df["code"] == code].sort_values("time").reset_index(drop=True)


def hypothesis_1_war_impact(df: pd.DataFrame) -> dict:
    print("\n" + "=" * 50)
    print("ГІПОТЕЗА 1: Вплив вторгнення 2022")
    print("=" * 50)

    overall = get_category(df, "010")
    before = overall[overall["time"] < 2022]["idx_prev_q"].dropna()
    after  = overall[overall["time"] >= 2022]["idx_prev_q"].dropna()

    print(f"До вторгнення  (n={len(before)}): середнє = {before.mean():.2f}%")
    print(f"Після вторгнення (n={len(after)}): середнє = {after.mean():.2f}%")

    t_stat, p_val = stats.ttest_ind(before, after)
    print(f"t = {t_stat:.3f}, p = {p_val:.4f}")
    print("Висновок:", "ЗНАЧУЩА різниця" if p_val < 0.05 else "Різниця НЕ значуща")

    return {"hypothesis": "H1_war", "t_stat": t_stat, "p_value": p_val,
            "mean_before": before.mean(), "mean_after": after.mean()}


def hypothesis_2_primary_vs_secondary(df: pd.DataFrame) -> dict:
    print("\n" + "=" * 50)
    print("ГІПОТЕЗА 2: Первинний vs Вторинний ринок")
    print("=" * 50)

    primary   = get_category(df, "100")["idx_prev_q"].dropna()
    secondary = get_category(df, "200")["idx_prev_q"].dropna()

    print(f"Первинний: середнє = {primary.mean():.2f}%")
    print(f"Вторинний: середнє = {secondary.mean():.2f}%")

    u_stat, p_val = stats.mannwhitneyu(primary, secondary, alternative="greater")
    print(f"U = {u_stat:.1f}, p = {p_val:.4f}")
    print("Висновок:", "Первинний ШВИДШЕ зростає" if p_val < 0.05 else "Суттєвої різниці немає")

    return {"hypothesis": "H2_markets", "u_stat": u_stat, "p_value": p_val,
            "mean_primary": primary.mean(), "mean_secondary": secondary.mean()}


def hypothesis_3_seasonality(df: pd.DataFrame) -> dict:
    print("\n" + "=" * 50)
    print("ГІПОТЕЗА 3: Сезонність")
    print("=" * 50)

    overall = get_category(df, "010").copy()
    overall["quarter"] = overall["period"].str.extract(r"Q(\d)").astype(int)

    groups = [overall[overall["quarter"] == q]["idx_prev_q"].dropna() for q in [1, 2, 3, 4]]
    for i, g in enumerate(groups, 1):
        print(f"Q{i}: середнє = {g.mean():.2f}%")

    f_stat, p_val = stats.f_oneway(*groups)
    print(f"F = {f_stat:.3f}, p = {p_val:.4f}")
    print("Висновок:", "Сезонність ІСНУЄ" if p_val < 0.05 else "Сезонності НЕ виявлено")

    return {"hypothesis": "H3_seasonality", "f_stat": f_stat, "p_value": p_val}


def trend_analysis(df: pd.DataFrame) -> dict:
    print("\n" + "=" * 50)
    print("ТРЕНДОВИЙ АНАЛІЗ")
    print("=" * 50)

    overall = get_category(df, "010").dropna(subset=["idx_prev_q"])
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        overall["time"].values, overall["idx_prev_q"].values
    )
    print(f"Нахил: {slope:.4f} % на квартал, R² = {r_value**2:.4f}, p = {p_value:.4f}")
    print("Висновок:", ("зростаючий" if slope > 0 else "спадний") + " тренд" if p_value < 0.05 else "Тренду немає")

    return {"slope": slope, "r2": r_value**2, "p_value": p_value}


def save_results(results: list) -> None:
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    path = os.path.join(ARTIFACTS_DIR, "research_results.csv")
    pd.DataFrame(results).to_csv(path, index=False, encoding="utf-8-sig")
    print(f"\n[research] Результати збережено: {path}")


def main():
    print("=" * 50)
    print("  ДОСЛІДНИЦЬКИЙ АНАЛІЗ ДАНИХ")
    print("=" * 50)

    df = load_data()
    results = []
    results.append(hypothesis_1_war_impact(df))
    results.append(hypothesis_2_primary_vs_secondary(df))
    results.append(hypothesis_3_seasonality(df))
    results.append(trend_analysis(df))
    save_results(results)

    print("\n[research] Аналіз завершено успішно.")
    return df


if __name__ == "__main__":
    main()
