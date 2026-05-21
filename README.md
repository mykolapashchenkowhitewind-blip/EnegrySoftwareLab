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
