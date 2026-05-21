# Лабораторна робота №1

**Тема:** Проектування системи збереження та збору даних  
**Дисципліна:** Програмне забезпечення енергетичного менеджменту  
**Студент:** Pashchenko Mykola  
**Група:** TR-51mp

## Мета роботи

Спроєктувати та реалізувати систему збору, збереження й первинної обробки даних для трирівневого обліку енергоспоживання об'єкта. Система зберігає погодинні дані мінімум за один рік, підтримує рівні обліку 1, 2 і 3, тарифні зони, метеодані, базову лінію споживання та аналітичні запити.

## Варіант

Варіант 8: University.

| Параметр | Значення |
| --- | --- |
| Об'єкт | University |
| Площа | 5200 m2 |
| Встановлена потужність | 350 kW |
| Кількість лічильників | 14 |
| Режим роботи | 24/7 |
| Навантаження | 85 kW, range 50-130 kW |
| СЕС | about 140 kW |
| Батарея | 110 kWh |
| Тариф | 3-zone tariff |

## Обраний трек і технології

Виконано Track A: класична реляційна система.

- Python 3 for scripts.
- SQLite for the relational database.
- SQL scripts for schema, views, and analytics.
- CSV files for generated test data and query results.
- Mermaid for the ER diagram.

## Структура проєкту

```text
.
|-- README.md
|-- plan.md
|-- Lab1.pdf
|-- variants.pdf
|-- data/
|   |-- energy_management.db
|   |-- generated/
|   |   |-- measurements.csv
|   |   `-- weather_data.csv
|   `-- results/
|       |-- query_01.csv
|       |-- query_02.csv
|       |-- query_03.csv
|       |-- query_04.csv
|       |-- query_05.csv
|       |-- query_06.csv
|       `-- query_07.csv
|-- docs/
|   `-- er_diagram.md
|-- sql/
|   |-- schema.sql
|   |-- views.sql
|   `-- analytics.sql
`-- src/
    |-- config.py
    |-- create_database.py
    |-- generate_test_data.py
    |-- load_data.py
    `-- run_analytics.py
```

## Модель даних

Основні таблиці:

- `objects`: об'єкт обліку з площею, потужністю, режимом роботи, СЕС і батареєю.
- `meters`: 14 лічильників із рівнями обліку 1, 2 і 3.
- `measurements`: погодинні показники споживання з прив'язкою до лічильника та тарифної зони.
- `weather_data`: температура й інсоляція для кожної години року.
- `tariff_zones`: 3-зонний тариф.
- `baselines`: місячна базова лінія споживання.
- `energy_efficiency_metrics`: місячні показники енергоефективності.

ER diagram: [docs/er_diagram.md](docs/er_diagram.md)

## Як запустити

Run commands from the project root:

```powershell
python .\src\create_database.py
python .\src\generate_test_data.py
python .\src\load_data.py
python .\src\run_analytics.py
```

If the system Python is not suitable, use the bundled or virtual-environment Python executable instead.

## Генерація тестових даних

The generator creates:

- 8760 hourly weather records.
- 122640 hourly measurement records: 8760 hours * 14 meters.
- Seasonal variation for winter and summer.
- Workday/weekend and daily load patterns.
- Temperature and solar irradiation values.
- Random fluctuation of about 5-10 percent.

## Аналітичні запити

The file [sql/analytics.sql](sql/analytics.sql) contains queries for:

- Daily consumption.
- Weekly consumption.
- Monthly consumption.
- Consumption and cost by tariff zone.
- Specific consumption in kWh/m2.
- Monthly comparison with the baseline.
- Anomaly detection where deviation is greater than 20 percent from average hourly consumption.

After running `src/run_analytics.py`, results are saved in `data/results/query_01.csv` through `data/results/query_07.csv`.

## Представлення для рівнів обліку

The database creates these views:

- `v_level_1_consumption`
- `v_level_2_consumption`
- `v_level_3_consumption`
- `v_hourly_object_consumption`

They allow analyzing measurements separately by accounting level and by total hourly object consumption.

## Звітність за вимогами лабораторної

| Вимога Track A | Файл |
| --- | --- |
| Діаграма структури даних | `docs/er_diagram.md` |
| SQL scripts for structure | `sql/schema.sql`, `sql/views.sql` |
| Test data generation script | `src/generate_test_data.py` |
| Analytical queries with results | `sql/analytics.sql`, `data/results/*.csv` |
| README with instructions | `README.md` |

## Очікуваний результат

Після виконання команд буде створено SQLite database `data/energy_management.db`, заповнено її даними для університету за один рік та сформовано CSV-файли з результатами базової аналітики.

---

# Лабораторна робота №2

**Тема:** Аналіз даних та прогнозування енергоспоживання  
**Дисципліна:** Програмне забезпечення енергетичного менеджменту  
**Студент:** Pashchenko Mykola  
**Група:** TR-51mp  
**Варіант:** 8, University

## Мета роботи

На основі даних, отриманих у лабораторній роботі №1, виконати аналітичне дослідження, визначити фактори впливу на енергоспоживання та побудувати моделі прогнозування.

## Як запустити Lab 2

Спочатку має існувати база `data/energy_management.db` з Lab 1. Потім виконайте:

```powershell
python .\src\lab2_prepare_dataset.py
python .\src\lab2_eda.py
python .\src\lab2_train_models.py
python .\src\lab2_forecast.py
```

## Результати Lab 2

- Prepared dataset: `data/lab2/analysis_dataset.csv`
- Descriptive statistics: `data/lab2/descriptive_statistics.csv`
- Missing values: `data/lab2/missing_values.csv`
- Outlier summary: `data/lab2/outlier_summary.csv`
- Autocorrelation: `data/lab2/autocorrelation.csv`
- Model comparison: `data/lab2/model_comparison.csv`
- Residuals: `data/lab2/residuals.csv`
- Next-month forecast: `data/lab2/next_month_forecast.csv`
- Best model: `models/lab2_best_model.pkl`
- Report: `docs/lab2_report.md`
- Figures: `reports/figures/*.png`

## Візуалізації

The Lab 2 workflow creates at least 10 figures:

- consumption across the year,
- distribution,
- box plot by hour,
- daily profile,
- workday vs weekend profile,
- monthly dynamics,
- heatmap by hour and weekday,
- consumption vs temperature,
- correlation matrix,
- monthly temperature/consumption,
- actual vs predicted values,
- residual distribution,
- feature importance when available.

---

# Лабораторна робота №3

**Тема:** Моделювання системи управління енергопотоками (EMS)  
**Дисципліна:** Програмне забезпечення енергетичного менеджменту  
**Студент:** Pashchenko Mykola  
**Група:** TR-51mp  
**Варіант:** 8, University

## Мета роботи

Побудувати модель EMS для об'єкта з СЕС, батареєю, мережею та навантаженням. Система приймає рішення щодо заряду/розряду батареї, імпорту/експорту енергії та мінімізації вартості з урахуванням тарифних зон.

## Як запустити Lab 3

Спочатку мають існувати результати Lab 1, а бажано також Lab 2. Потім виконайте:

```powershell
python .\src\lab3_prepare_input.py
python .\src\lab3_simulate_ems.py
python .\src\lab3_analyze_results.py
```

## Результати Lab 3

- Simulation input: `data/lab3/simulation_input.csv`
- Simulation results: `data/lab3/simulation_results.csv`
- Energy metrics: `data/lab3/energy_metrics.csv`
- Economic metrics: `data/lab3/economic_metrics.csv`
- Architecture: `docs/lab3_architecture.md`
- Report: `docs/lab3_report.md`
- Figures: `reports/lab3_figures/*.png`

## Візуалізації Lab 3

The workflow creates:

- energy balance,
- battery SOC,
- grid import/export,
- consumption sources,
- savings by tariff zone,
- baseline cost versus EMS cost.

---

# Лабораторна робота №4

**Тема:** Веб-інтерфейс для моніторингу та управління  
**Дисципліна:** Програмне забезпечення енергетичного менеджменту  
**Студент:** Pashchenko Mykola  
**Група:** TR-51mp  
**Варіант:** 8, University

## Мета роботи

Створити веб-застосунок, який об'єднує результати Lab 1, Lab 2 і Lab 3: історію споживання, агреговану аналітику, baseline, прогноз, EMS-моніторинг та формування звітів.

## Як запустити Lab 4

```powershell
python .\app\main.py
```

Open in browser:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

## Результати Lab 4

- Backend API: `app/main.py`, `app/services/`
- Frontend app: `app/static/`
- API reference: `docs/lab4_api.md`
- Lab report: `docs/lab4_report.md`
- JSON report: `data/lab4/summary_report.json`
- CSV export: `data/lab4/exported_report.csv`
- Screenshots folder: `reports/lab4_screenshots/`
