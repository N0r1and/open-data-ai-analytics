"""
Модуль: data_load.py
Призначення: завантаження та первинна обробка датасету "Індекси цін на житло"
Джерело: https://data.gov.ua/dataset/85e5e66c-be8b-4e75-a7df-d3e4c886fa73
"""

import pandas as pd
import os

# Шлях до файлу датасету (покладіть файл у папку data/raw/)
DATA_FILE = os.path.join("data", "raw", "129-indeksi-tsin-na-zhitlo.xlsx")
OUTPUT_FILE = os.path.join("data", "housing_prices_clean.csv")


def load_raw_data(filepath: str) -> pd.DataFrame:
    """
    Завантажує сирі дані з XLSX-файлу.
    Зчитує аркуш 'Індекси цін на житло.ua', пропускає рядок із заголовками.
    """
    print(f"[data_load] Завантаження файлу: {filepath}")
    df = pd.read_excel(
        filepath,
        sheet_name="Індекси цін на житло.ua",
        header=1,       # другий рядок — реальні заголовки
        skiprows=[2]    # третій рядок — дублікат заголовків (ua-назви), пропускаємо
    )
    print(f"[data_load] Завантажено {len(df)} рядків, {len(df.columns)} колонок")
    return df


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Перейменовує колонки на зрозумілі англійські назви для подальшої обробки.
    """
    df = df.copy()
    df.columns = [
        "code",        # код категорії
        "category",    # назва категорії
        "period",      # квартал (наприклад: 2020 Q1)
        "idx_prev_q",  # індекс до попереднього кварталу
        "idx_prev_yr_q4",   # індекс до IV кварталу попереднього року
        "idx_same_q_prev_yr",  # індекс до відповідного кварталу попереднього року
        "idx_same_period_prev_yr"  # індекс до відповідного періоду попереднього року
    ]
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Очищає датафрейм:
    - замінює 'NA' (рядок) на справжній NaN
    - конвертує числові колонки у float
    - прибирає порожні рядки
    - конвертує 'code' у рядок для надійного фільтрування
    """
    df = df.copy()

    # Замінюємо рядок 'NA' на справжній NaN
    df.replace("NA", pd.NA, inplace=True)

    # Перелік числових колонок
    numeric_cols = ["idx_prev_q", "idx_prev_yr_q4",
                    "idx_same_q_prev_yr", "idx_same_period_prev_yr"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Переводимо code у рядок (може бути int після читання Excel)
    df["code"] = df["code"].astype(str).str.strip()

    # Прибираємо порожні рядки (де немає ні коду, ні кварталу)
    df.dropna(subset=["code", "period"], inplace=True)

    print(f"[data_load] Після очищення: {len(df)} рядків")
    return df


def save_data(df: pd.DataFrame, output_path: str) -> None:
    """
    Зберігає очищений датафрейм у CSV.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[data_load] Збережено: {output_path}")


def main():
    """Головна функція модуля — запускає повний пайплайн завантаження."""
    # Перевірка наявності файлу
    if not os.path.exists(DATA_FILE):
        print(f"[data_load] ПОМИЛКА: файл не знайдено — {DATA_FILE}")
        print("[data_load] Завантажте датасет з https://data.gov.ua та покладіть у data/raw/")
        return None

    df_raw = load_raw_data(DATA_FILE)
    df_renamed = rename_columns(df_raw)
    df_clean = clean_data(df_renamed)
    save_data(df_clean, OUTPUT_FILE)

    # Виводимо коротку інформацію
    print("\n=== Попередній перегляд даних ===")
    print(df_clean.head(10).to_string(index=False))
    print(f"\nУнікальні категорії:\n{df_clean[['code', 'category']].drop_duplicates().to_string(index=False)}")
    print(f"\nПеріод: {df_clean['period'].min()} — {df_clean['period'].max()}")
    print(f"Пропуски (idx_prev_q): {df_clean['idx_prev_q'].isna().sum()}")

    return df_clean


if __name__ == "__main__":
    main()
