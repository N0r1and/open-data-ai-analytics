"""
Модуль: data_quality_analysis.py
Призначення: перевірка якості даних — пропуски, дублікати, аномалії, типи
"""

import pandas as pd
import numpy as np
import os

DATA_FILE = os.path.join("data", "housing_prices_clean.csv")


def load_data() -> pd.DataFrame:
    """Завантажує очищений CSV-файл."""
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(
            f"Файл не знайдено: {DATA_FILE}\nСпочатку запустіть src/data_load.py"
        )
    df = pd.read_csv(DATA_FILE, dtype={"code": str})
    print(f"[quality] Завантажено {len(df)} рядків")
    return df


def check_shape(df: pd.DataFrame) -> None:
    """Виводить розмір датафрейму і типи колонок."""
    print("\n--- Розмір і типи ---")
    print(f"Рядків: {df.shape[0]}, Колонок: {df.shape[1]}")
    print(df.dtypes.to_string())


def check_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Підраховує пропущені значення у кожній колонці.
    Повертає датафрейм зі статистикою пропусків.
    """
    print("\n--- Пропущені значення ---")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    result = pd.DataFrame({
        "Пропусків": missing,
        "Відсоток, %": missing_pct
    })
    print(result[result["Пропусків"] > 0].to_string())
    if result["Пропусків"].sum() == 0:
        print("Пропусків не виявлено.")
    return result


def check_duplicates(df: pd.DataFrame) -> None:
    """Перевіряє наявність дублікатів за ключовими полями (code + period)."""
    print("\n--- Дублікати ---")
    dups = df.duplicated(subset=["code", "period"])
    print(f"Знайдено дублікатів: {dups.sum()}")
    if dups.sum() > 0:
        print(df[dups][["code", "category", "period"]].to_string())


def check_value_ranges(df: pd.DataFrame) -> None:
    """
    Перевіряє допустимі діапазони числових індексів.
    Індекс ~100 означає відсутність змін, тому значення поза [50, 200] — потенційні аномалії.
    """
    print("\n--- Діапазони значень (числові індекси) ---")
    numeric_cols = ["idx_prev_q", "idx_prev_yr_q4",
                    "idx_same_q_prev_yr", "idx_same_period_prev_yr"]

    stats = df[numeric_cols].describe().round(2)
    print(stats.to_string())

    # Пошук потенційних аномалій: значення < 50 або > 200
    print("\n--- Потенційні аномалії (значення < 50 або > 200) ---")
    anomaly_mask = pd.Series(False, index=df.index)
    for col in numeric_cols:
        anomaly_mask |= (df[col] < 50) | (df[col] > 200)
    anomalies = df[anomaly_mask]
    if len(anomalies) == 0:
        print("Аномалій не виявлено.")
    else:
        print(f"Знайдено {len(anomalies)} потенційних аномалій:")
        print(anomalies[["code", "category", "period"] + numeric_cols].to_string(index=False))


def check_categories(df: pd.DataFrame) -> None:
    """Перевіряє повноту категорій — чи всі 9 кодів присутні для кожного кварталу."""
    print("\n--- Повнота категорій ---")
    expected_codes = {"010", "100", "101", "102", "103", "200", "201", "202", "203"}
    actual_codes = set(df["code"].unique())
    missing_codes = expected_codes - actual_codes
    extra_codes = actual_codes - expected_codes

    print(f"Очікувані коди: {sorted(expected_codes)}")
    print(f"Наявні коди:    {sorted(actual_codes)}")
    if missing_codes:
        print(f"ВІДСУТНІ коди: {missing_codes}")
    if extra_codes:
        print(f"Зайві коди: {extra_codes}")
    if not missing_codes and not extra_codes:
        print("Всі категорії присутні.")

    # Перевірка кількості кварталів по кожному коду
    print("\nКількість кварталів по кожному коду:")
    counts = df.groupby("code")["period"].count()
    print(counts.to_string())


def check_periods(df: pd.DataFrame) -> None:
    """Перевіряє неперервність часового ряду (чи немає пропущених кварталів)."""
    print("\n--- Часовий ряд ---")
    periods = sorted(df["period"].unique())
    print(f"Перший: {periods[0]}, Останній: {periods[-1]}, Всього: {len(periods)} кварталів")

    # Генеруємо очікувані квартали
    years = range(2016, 2026)
    quarters = [f"{y} Q{q}" for y in years for q in range(1, 5)]
    quarters = [q for q in quarters if q <= periods[-1]]

    missing_periods = set(quarters) - set(periods)
    if missing_periods:
        print(f"Пропущені квартали: {sorted(missing_periods)}")
    else:
        print("Часовий ряд неперервний — пропусків немає.")


def main():
    """Запускає повну перевірку якості даних."""
    print("=" * 50)
    print("  ПЕРЕВІРКА ЯКОСТІ ДАНИХ")
    print("=" * 50)

    df = load_data()
    check_shape(df)
    check_missing(df)
    check_duplicates(df)
    check_value_ranges(df)
    check_categories(df)
    check_periods(df)

    print("\n[quality] Перевірку завершено.")
    return df


if __name__ == "__main__":
    main()
