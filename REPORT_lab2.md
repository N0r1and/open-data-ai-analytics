# Звіт з лабораторної роботи №2
## Тема: Побудова CI-конвеєра із використанням GitHub Actions

**Студент:** N0r1and  
**Група:** ШІ-31  
**Курс:** Середовище та компоненти розробки у моделюванні та аналізі даних (СКРМАД)  
**Репозиторій:** https://github.com/N0r1and/open-data-ai-analytics

---

### 1. Мета роботи
Налаштувати CI/CD pipeline у GitHub Actions: автоматичний запуск усіх модулів проєкту при push/pull_request, публікація артефактів (логів, CSV, графіків), а також запуск pipeline на self-hosted runner (локальний Windows ПК).

---

### 2. Частина A — CI для кожного модуля

**Файл:** `.github/workflows/ci.yml`

Pipeline запускається на трьох тригерах:
- `push` у гілку `main`
- `pull_request` у `main`
- `workflow_dispatch` — ручний запуск з вибором конкретного модуля

Для паралельного запуску чотирьох модулів використано **matrix strategy**:

```yaml
strategy:
  fail-fast: false
  matrix:
    module: [data_load, data_quality_analysis, data_research, visualization]
```

`fail-fast: false` означає що навіть якщо один модуль впаде — інші продовжать виконання, і ми побачимо результат по кожному.

Кроки кожного job:
1. `actions/checkout@v4` — завантаження коду репозиторію
2. `actions/setup-python@v5` — встановлення Python 3.11
3. `pip install -r requirements.txt` — встановлення залежностей
4. Підготовка даних (копіювання датасету у `data/raw/`)
5. Запуск `data_load.py` для генерації CSV (якщо модуль не `data_load`)
6. Запуск основного модуля з перенаправленням виводу у лог-файл
7. `actions/upload-artifact@v4` — збереження артефактів

При `workflow_dispatch` використано умовний запуск:
```yaml
if: >
  github.event_name != 'workflow_dispatch' ||
  github.event.inputs.module == 'all' ||
  github.event.inputs.module == matrix.module
```
Це дозволяє запустити лише один конкретний модуль замість усіх чотирьох.

---

### 3. Частина B — CD/публікація артефактів

Після кожного успішного запуску кожен job зберігає результати через `actions/upload-artifact@v4`:

| Модуль | Артефакт |
|--------|----------|
| data_load | `run.log` + `housing_prices_clean.csv` |
| data_quality_analysis | `run.log` + `quality_report.csv` |
| data_research | `run.log` + `research_results.csv` |
| visualization | `run.log` + `fig1_overall_trend.png` + `fig2_primary_vs_secondary.png` + `fig3_seasonality_boxplot.png` + `fig4_heatmap_by_year.png` |

Артефакти зберігаються 7 днів і доступні у вкладці **Actions → конкретний run → Artifacts**.

---

### 4. Частина C — Self-hosted runner (Windows)

**Файл:** `.github/workflows/ci-selfhosted.yml`

#### Підключення runner

1. GitHub репозиторій → Settings → Actions → Runners → **New self-hosted runner**
2. Обрано: Windows, x64
3. Виконано команди реєстрації у PowerShell
4. Runner запущено командою `./run.cmd`

#### Порівняння GitHub-hosted vs Self-hosted

| Критерій | GitHub-hosted (ubuntu-latest) | Self-hosted (Windows) |
|----------|-------------------------------|----------------------|
| Швидкість встановлення залежностей | ~60–90 сек | ~15–30 сек (pip cache локально) |
| Доступ до локальних даних | ❌ Датасет треба зберігати в репо | ✅ Прямий доступ до `data/raw/` |
| Стабільність | ✅ Завжди online | ⚠️ Залежить від стану ПК |
| Безпека | ✅ Ізольоване середовище | ⚠️ Runner має доступ до файлової системи |
| Необхідність обслуговування | ❌ GitHub обслуговує сам | ✅ Треба самому оновлювати залежності |

**Головна перевага self-hosted у цьому проєкті** — великий датасет XLSX не потрібно завантажувати у репозиторій. Runner бере його напряму з локального диска.

**Головний ризик** — якщо ПК вимкнений або runner не запущений, pipeline не виконається (статус "runner offline").

---

### 5. Висновки
У ході роботи налаштовано повний CI/CD pipeline для Data Science проєкту. Використання matrix strategy дозволило паралельно запускати всі 4 модулі в одному workflow-файлі без дублювання коду. Артефакти (логи, CSV, графіки) автоматично зберігаються після кожного запуску. Self-hosted runner на Windows підключено і протестовано — він дає переваги в доступі до локальних даних та швидкості, але потребує ручного обслуговування.
