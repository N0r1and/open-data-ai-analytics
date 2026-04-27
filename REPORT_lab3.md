# Звіт з лабораторної роботи №3
## Тема: Контейнеризація модулів проєкту за допомогою Docker

**Студент:** N0r1and  
**Група:** ШІ-31  
**Репозиторій:** https://github.com/N0r1and/open-data-ai-analytics

---

### 1. Мета роботи
Опанувати базові принципи контейнеризації: створити Docker-образи для всіх модулів проєкту, організувати їх спільний запуск через Docker Compose, налаштувати взаємодію через PostgreSQL і volumes, реалізувати веб-інтерфейс для перегляду результатів.

---

### 2. Архітектура рішення

Проєкт розгорнуто як 6 Docker-сервісів у спільній мережі `housing_net`:

| Сервіс | Образ | Роль |
|--------|-------|------|
| `db` | postgres:16-alpine | Зберігає дані та результати |
| `data_load` | python:3.11-slim | Читає XLSX → завантажує у БД |
| `data_quality_analysis` | python:3.11-slim | Перевірка якості → JSON у БД |
| `data_research` | python:3.11-slim | Статистичний аналіз → JSON у БД |
| `visualization` | python:3.11-slim | 4 графіки PNG → volume /plots |
| `web` | python:3.11-slim | Flask, порт 5000 |

---

### 3. Взаємодія між сервісами

Сервіси обмінюються даними двома способами:

**База даних (PostgreSQL):** `data_load` створює таблицю `housing_prices` і заповнює її. `data_quality_analysis` і `data_research` читають дані з цієї таблиці і зберігають результати у таблиці `quality_report` і `research_results`. `web` читає з усіх таблиць для відображення.

**Docker volumes:** `visualization` зберігає PNG-файли у volume `/plots`. `web` монтує той самий volume як read-only і роздає графіки через `/plots/<filename>`.

---

### 4. Порядок запуску сервісів

Docker Compose забезпечує правильний порядок через `depends_on`:

```
db (healthcheck: pg_isready)
  └── data_load (після готовності БД)
        ├── data_quality_analysis
        ├── data_research
        └── visualization
web (після готовності БД, незалежно від інших)
```

---

### 5. Реалізовані компоненти

**Dockerfile** — створено для кожного з 5 Python-сервісів. Базовий образ `python:3.11-slim` (мінімальний розмір). Кожен Dockerfile: копіює `requirements.txt`, встановлює залежності, копіює `app.py`, запускає `python app.py`.

**compose.yaml** — описує всі 6 сервісів з мережами, томами, змінними середовища з `.env`, healthcheck для БД, залежностями між сервісами.

**Веб-інтерфейс** — Flask додаток з 5 сторінками: головна, дані (таблиця з БД), якість, аналіз (результати гіпотез), графіки.

---

### 6. Труднощі та вирішення

**Проблема:** сервіси запускаються паралельно, але `data_quality_analysis` потребує щоб `data_load` вже завантажив дані.
**Вирішення:** у кожному сервісі реалізовано функцію `wait_for_data()` — вона перевіряє кількість записів у таблиці і чекає якщо їх ще немає. Також використано `depends_on: condition: service_completed_successfully`.

**Проблема:** visualization будує графіки без екрана (headless середовище).
**Вирішення:** `matplotlib.use("Agg")` — backend без GUI.

---

### 7. Команда запуску
```bash
docker compose up --build
```
Веб-інтерфейс: http://localhost:5000
