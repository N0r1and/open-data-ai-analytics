# Звіт з лабораторної роботи
## Тема: Налаштування Git-репозиторію та робота з Git Flow (Data Science Project)

**Студент:** N0r1and  
**Група:** ШІ-31  
**Курс:** Середовище та компоненти розробки у моделюванні та аналізі даних (СКРМАД)  
**Дата:** 2026-03-11

---

### 1. Мета роботи
Створити базову структуру проєкту для аналізу відкритих даних (`open-data-ai-analytics`), налаштувати систему контролю версій Git, відпрацювати створення гілок (feature branches), злиття через Pull Requests, розв'язання merge-конфліктів та тегування релізів.

---

### 2. Виконані завдання

**1. Ініціалізація репозиторію (коміти: `04171b2`, `8dc3e6b`)**  
Створено локальний та віддалений репозиторії `open-data-ai-analytics`. Налаштовано структуру папок (`data/`, `notebooks/`, `src/`, `reports/figures/`) та файл `.gitignore` для виключення Python-кешу (`__pycache__/`), віртуального середовища (`.venv/`) та папки `data/raw/` з великими файлами даних. Заповнено `README.md` з описом проєкту — аналіз індексів цін на житло в Україні (джерело: data.gov.ua, Держстат) — та трьома гіпотезами: вплив повномасштабного вторгнення (2022) на ціни, порівняння первинного і вторинного ринків, дослідження сезонності.

**2. Гілка `feature/data_load` (коміт: `06f3884`)**  
Створено гілку `feature/data_load` із скриптом `src/data_load.py` — завантаження датасету з XLSX, перейменування колонок, очищення від рядкових `NA`, конвертація типів, збереження у CSV. Гілку змерджено напряму у `main`.

**3. Гілки через Pull Request (коміти: `e8be7f8`, `d8d23e1`; merge-коміти: `e223701`, `1f25905`)**  
Створено паралельні гілки:
- `feature/data_quality_analysis` — модуль `src/data_quality_analysis.py`: перевірка розміру та типів, пропущених значень, дублікатів, діапазонів числових індексів, повноти категорій і неперервності часового ряду. Злито через Pull Request #1 з описом виконаних змін.
- `feature/data_research` — модуль `src/data_research.py`: статистичний аналіз трьох гіпотез (t-тест Стьюдента, тест Манна-Уітні, ANOVA) та лінійний трендовий аналіз. Злито через Pull Request #2 з описом виконаних змін.

**4. Розв'язання merge-конфлікту (коміти: `09b6880`, `052386c`, `747f960`)**  
Штучно створено merge-конфлікт у файлі `README.md` шляхом одночасної зміни секції гіпотез у двох гілках — `conflict-branch-A` та `conflict-branch-B`. При злитті `conflict-branch-B` у `main` Git повідомив про конфлікт. Конфлікт розв'язано локально: видалено маркери `<<<<<<<`, `=======`, `>>>>>>>`, залишено фінальний коректний варіант тексту. Зроблено коміт `fix: resolve merge conflict in README hypotheses section`.

**5. Гілка `feature/visualization` (коміт: `ce87aa7`)**  
Створено модуль `src/visualization.py` з чотирма графіками:
- Динаміка загального індексу цін з позначкою вторгнення 24.02.2022
- Порівняння первинного та вторинного ринків
- Boxplot сезонності по кварталах (Q1–Q4)
- Теплова карта середніх річних індексів по всіх категоріях

**6. Реліз `v0.1.0` (коміт: `c0082ec`)**  
Додано `CHANGELOG.md` з повною історією змін проєкту. Фінальний стан зафіксовано анотованим тегом `v0.1.0`.

---

### 3. Посилання на репозиторій
https://github.com/N0r1and/open-data-ai-analytics

---

### 4. Дерево комітів (Git Log)

```
* c0082ec (HEAD -> main, tag: v0.1.0, origin/main, origin/HEAD) docs: add CHANGELOG and REPORT
* ce87aa7 (origin/feature/visualization, feature/visualization) feat: add visualization module (4 charts)
*   1f25905 Merge pull request #2 from N0r1and/feature/data_research
|\
| * d8d23e1 (origin/feature/data_research, feature/data_research) feat: add research analysis (t-test, ANOVA, trend)
|/
*   747f960 fix: resolve merge conflict in README hypotheses section
|\
| * 052386c (origin/conflict-branch-B, conflict-branch-B) docs: update hypothesis 1 - version B
* | 09b6880 (origin/conflict-branch-A, conflict-branch-A) docs: update hypothesis 1 - version A
|/
*   e223701 Merge pull request #1 from N0r1and/feature/data_quality_analysis
|\
| * e8be7f8 (origin/feature/data_quality_analysis, feature/data_quality_analysis) feat: add data quality checks (missing, duplicates, ranges)
|/
* 06f3884 (origin/feature/data_load, feature/data_load) feat: add data loading and cleaning script
* 8dc3e6b docs: fill README with project description and hypotheses
* 04171b2 init: project structure and .gitignore
```

---

### 5. Висновки
У ході роботи опановано повний Git Flow для Data Science проєкту: від ініціалізації репозиторію до релізу з тегом `v0.1.0`. Відпрацьовано роботу з feature-гілками (4 гілки), злиття через Pull Requests (PR #1 та PR #2), штучне створення та розв'язання merge-конфлікту. Проєкт реалізовано на датасеті «Індекси цін на житло» (Держстат України, 2016–2025 рр.) і містить чотири Python-модулі: завантаження даних, перевірку якості, дослідницький аналіз та візуалізацію.
