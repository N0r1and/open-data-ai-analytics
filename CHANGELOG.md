# Changelog

Усі значущі зміни цього проєкту задокументовано тут.
Формат базується на [Keep a Changelog](https://keepachangelog.com/uk/1.0.0/).

## [v0.1.0] - 2026-03-11

### Додано
- Ініціалізовано структуру проєкту (`data/`, `src/`, `notebooks/`, `reports/figures/`)
- Налаштовано `.gitignore` (Python-кеш, віртуальне середовище, сирі дані)
- Заповнено `README.md` з описом проєкту, джерелом даних та гіпотезами
- `src/data_load.py` — модуль завантаження та очищення датасету (гілка `feature/data_load`)
- `src/data_quality_analysis.py` — перевірка якості: пропуски, дублікати, аномалії, повнота (гілка `feature/data_quality_analysis`)
- `src/data_research.py` — дослідницький аналіз: t-тест, ANOVA, тренд (гілка `feature/data_research`)
- `src/visualization.py` — 4 графіки: тренд, порівняння ринків, сезонність, теплова карта (гілка `feature/visualization`)
- Розв'язано merge-конфлікт у `README.md`
- Додано `CHANGELOG.md` та тег `v0.1.0`

### Датасет
- Індекси цін на житло — Держстат України, data.gov.ua
- Охоплення: 2016 Q1 – 2025 Q2
