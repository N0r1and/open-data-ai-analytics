"""
Модуль: data_quality_analysis.py
Призначення: перевірка якості даних — пропуски, дублікати, аномалії, типи
"""

import pandas as pd
import numpy as np
import os
import sys

DATA_FILE = os.path.join("data", "housing_prices_clean.csv")
ARTIFACTS_DIR = os.path.join("artifacts", "data_quality_analysis")


def load_data() -> pd.DataFrame:
    """Завантажує очищений CSV-файл."""
    if not os.path.exists(DATA_FILE):
        print(f"[quality] ПОМИЛКА: файл не знайдено — {DATA_FILE}")
        print("[quality] Спочатку запустіть src/data_load.py")
        sys.exit(1)
    df = pd.read_csv(DATA_FILE, dtype={"code": str})
    print(f"[quality] Завантажено {len(df)} рядків")
    return df


def check_shape(df: pd.DataFrame) -> None:
    print("\n--- Розмір і типи ---")
    print(f"Рядків: {df.shape[0]}, Колонок: {df.shape[1]}")
    print(df.dtypes.to_string())


def check_missing(df: pd.DataFrame) -> pd.DataFrame:
    print("\n--- Пропущені значення ---")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    result = pd.DataFrame({"Пропусків": missing, "Відсоток, %": missing_pct})
    print(result.to_string())
    if result["Пропусків"].sum() == 0:
        print("Пропусків не виявлено.")
    return result


def check_duplicates(df: pd.DataFrame) -> None:
    print("\n--- Дублікати ---")
    dups = df.duplicated(subset=["code", "period"])
    print(f"Знайдено дублікатів: {dups.sum()}")


def check_value_ranges(df: pd.DataFrame) -> None:
    print("\n--- Діапазони значень ---")
    numeric_cols = ["idx_prev_q", "idx_prev_yr_q4",
                    "idx_same_q_prev_yr", "idx_same_period_prev_yr"]
    print(df[numeric_cols].describe().round(2).to_string())

    print("\n--- Потенційні аномалії (< 50 або > 200) ---")
    anomaly_mask = pd.Series(False, index=df.index)
    for col in numeric_cols:
        anomaly_mask |= (df[col] < 50) | (df[col] > 200)
    anomalies = df[anomaly_mask]
    if len(anomalies) == 0:
        print("Аномалій не виявлено.")
    else:
        print(f"Знайдено {len(anomalies)} аномалій")


def check_categories(df: pd.DataFrame) -> None:
    print("\n--- Повнота категорій ---")
    expected = {"010", "100", "101", "102", "103", "200", "201", "202", "203"}
    actual = set(df["code"].unique())
    missing = expected - actual
    print(f"Відсутні коди: {missing if missing else 'немає'}")
    print(df.groupby("code")["period"].count().to_string())


def check_periods(df: pd.DataFrame) -> None:
    print("\n--- Часовий ряд ---")
    periods = sorted(df["period"].unique())
    print(f"Перший: {periods[0]}, Останній: {periods[-1]}, Всього: {len(periods)} кварталів")


def save_report(df: pd.DataFrame) -> None:
    """Зберігає звіт якості у artifacts."""
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    report_path = os.path.join(ARTIFACTS_DIR, "quality_report.csv")

    numeric_cols = ["idx_prev_q", "idx_prev_yr_q4",
                    "idx_same_q_prev_yr", "idx_same_period_prev_yr"]
    stats = df[numeric_cols].describe().round(2)
    stats.to_csv(report_path, encoding="utf-8-sig")
    print(f"\n[quality] Звіт збережено: {report_path}")


def main():
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
    save_report(df)

    print("\n[quality] Перевірку завершено успішно.")
    return df


if __name__ == "__main__":
    main()
