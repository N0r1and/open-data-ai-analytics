"""
Модуль: data_research.py
Призначення: дослідницький аналіз даних — перевірка гіпотез, статистика, тренди
"""

import pandas as pd
import numpy as np
from scipy import stats
import os

DATA_FILE = os.path.join("data", "housing_prices_clean.csv")


def load_data() -> pd.DataFrame:
    """Завантажує очищений датасет і додає числовий індекс часу для аналізу."""
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Файл не знайдено: {DATA_FILE}\nСпочатку запустіть src/data_load.py"
        )
    df = pd.read_csv(DATA_FILE, dtype={"code": str})

    # Додаємо числову колонку для часової осі (наприклад: 2016 Q1 → 2016.0, Q2 → 2016.25 ...)
    def period_to_float(p):
        year, q = p.split(" Q")
        return int(year) + (int(q) - 1) * 0.25

    df["time"] = df["period"].apply(period_to_float)
    return df


def get_category(df: pd.DataFrame, code: str) -> pd.DataFrame:
    """Повертає дані для конкретного коду категорії, відсортовані за часом."""
    return df[df["code"] == code].sort_values("time").reset_index(drop=True)


# ──────────────────────────────────────────────
# Гіпотеза 1: Вплив повномасштабного вторгнення
# ──────────────────────────────────────────────
def hypothesis_1_war_impact(df: pd.DataFrame) -> None:
    """
    Перевіряє Гіпотезу 1: чи спричинило вторгнення (2022 Q1) статистично значущий
    зсув у загальному індексі цін (код 010).

    Метод: t-тест Стьюдента для двох незалежних вибірок:
    - до вторгнення: 2016 Q1 – 2021 Q4
    - після вторгнення: 2022 Q1 – 2025 Q2
    Порівнюємо середні значення idx_prev_q (квартальне зростання).
    """
    print("\n" + "=" * 50)
    print("ГІПОТЕЗА 1: Вплив вторгнення 2022 на ціни")
    print("=" * 50)

    overall = get_category(df, "010")
    before = overall[overall["time"] < 2022]["idx_prev_q"].dropna()
    after  = overall[overall["time"] >= 2022]["idx_prev_q"].dropna()

    print(f"До вторгнення  (n={len(before)}): середнє = {before.mean():.2f}%, std = {before.std():.2f}%")
    print(f"Після вторгнення (n={len(after)}): середнє = {after.mean():.2f}%, std = {after.std():.2f}%")

    t_stat, p_val = stats.ttest_ind(before, after)
    print(f"\nt-статистика = {t_stat:.3f}, p-value = {p_val:.4f}")

    if p_val < 0.05:
        print("Висновок: різниця СТАТИСТИЧНО ЗНАЧУЩА (p < 0.05)")
        if after.mean() > before.mean():
            print("→ Після вторгнення квартальне зростання цін ЗБІЛЬШИЛОСЬ")
        else:
            print("→ Після вторгнення квартальне зростання цін ЗМЕНШИЛОСЬ")
    else:
        print("Висновок: різниця НЕ є статистично значущою (p ≥ 0.05)")


# ──────────────────────────────────────────────
# Гіпотеза 2: Первинний vs Вторинний ринок
# ──────────────────────────────────────────────
def hypothesis_2_primary_vs_secondary(df: pd.DataFrame) -> None:
    """
    Перевіряє Гіпотезу 2: чи зростають ціни на первинному ринку (код 100)
    швидше, ніж на вторинному (код 200)?

    Метод: порівняння кумулятивного зростання цін за весь період,
    а також тест Манна-Уітні (не параметричний, бо розподіл може бути ненормальним).
    """
    print("\n" + "=" * 50)
    print("ГІПОТЕЗА 2: Первинний ринок vs Вторинний ринок")
    print("=" * 50)

    primary   = get_category(df, "100")["idx_prev_q"].dropna()
    secondary = get_category(df, "200")["idx_prev_q"].dropna()

    print(f"Первинний ринок  (n={len(primary)}): середнє = {primary.mean():.2f}%, медіана = {primary.median():.2f}%")
    print(f"Вторинний ринок  (n={len(secondary)}): середнє = {secondary.mean():.2f}%, медіана = {secondary.median():.2f}%")

    # Кумулятивне зростання (добуток індексів / 100)
    cum_primary   = (primary / 100).prod() * 100 - 100
    cum_secondary = (secondary / 100).prod() * 100 - 100
    print(f"\nКумулятивне зростання за весь період:")
    print(f"  Первинний: {cum_primary:.1f}%")
    print(f"  Вторинний: {cum_secondary:.1f}%")

    u_stat, p_val = stats.mannwhitneyu(primary, secondary, alternative="greater")
    print(f"\nТест Манна-Уітні: U = {u_stat:.1f}, p-value = {p_val:.4f}")

    if p_val < 0.05:
        print("Висновок: первинний ринок зростає СТАТИСТИЧНО ШВИДШЕ (p < 0.05)")
    else:
        print("Висновок: суттєвої різниці між ринками НЕ виявлено (p ≥ 0.05)")


# ──────────────────────────────────────────────
# Гіпотеза 3: Сезонність
# ──────────────────────────────────────────────
def hypothesis_3_seasonality(df: pd.DataFrame) -> None:
    """
    Перевіряє Гіпотезу 3: чи існує статистично значуща сезонність
    у квартальних змінах цін на житло?

    Метод: одновибірковий дисперсійний аналіз (ANOVA) по кварталах (Q1–Q4).
    Якщо середні по кварталах суттєво відрізняються → є сезонність.
    """
    print("\n" + "=" * 50)
    print("ГІПОТЕЗА 3: Сезонність цін по кварталах")
    print("=" * 50)

    overall = get_category(df, "010").copy()
    overall["quarter"] = overall["period"].str.extract(r"Q(\d)").astype(int)

    groups = [
        overall[overall["quarter"] == q]["idx_prev_q"].dropna()
        for q in [1, 2, 3, 4]
    ]

    print("Середні значення по кварталах (квартальний індекс, %):")
    for i, g in enumerate(groups, 1):
        print(f"  Q{i}: середнє = {g.mean():.2f}%, n = {len(g)}")

    f_stat, p_val = stats.f_oneway(*groups)
    print(f"\nANOVA: F = {f_stat:.3f}, p-value = {p_val:.4f}")

    if p_val < 0.05:
        print("Висновок: сезонність ІСНУЄ — квартали статистично відрізняються (p < 0.05)")
    else:
        print("Висновок: статистично значущої сезонності НЕ виявлено (p ≥ 0.05)")


# ──────────────────────────────────────────────
# Додатковий аналіз: лінійний тренд
# ──────────────────────────────────────────────
def trend_analysis(df: pd.DataFrame) -> None:
    """
    Оцінює лінійний тренд загального індексу цін (код 010)
    за допомогою лінійної регресії.
    """
    print("\n" + "=" * 50)
    print("ТРЕНДОВИЙ АНАЛІЗ: загальний індекс (010)")
    print("=" * 50)

    overall = get_category(df, "010").dropna(subset=["idx_prev_q"])
    x = overall["time"].values
    y = overall["idx_prev_q"].values

    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    print(f"Нахил (slope): {slope:.4f} % на квартал")
    print(f"R²: {r_value**2:.4f}")
    print(f"p-value: {p_value:.4f}")

    if p_value < 0.05:
        direction = "зростаючий" if slope > 0 else "спадний"
        print(f"Висновок: є статистично значущий {direction} тренд")
    else:
        print("Висновок: статистично значущого тренду не виявлено")


def main():
    """Запускає повний дослідницький аналіз."""
    print("=" * 50)
    print("  ДОСЛІДНИЦЬКИЙ АНАЛІЗ ДАНИХ")
    print("=" * 50)

    df = load_data()
    hypothesis_1_war_impact(df)
    hypothesis_2_primary_vs_secondary(df)
    hypothesis_3_seasonality(df)
    trend_analysis(df)

    print("\n[research] Аналіз завершено.")
    return df


if __name__ == "__main__":
    main()
