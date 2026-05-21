import csv
import sqlite3
from collections import defaultdict

from config import DB_PATH, GENERATED_DIR, OBJECT, TARIFF_ZONES


METER_LOCATIONS = [
    "Main building input",
    "Lecture halls",
    "Laboratories",
    "Library",
    "Dormitory block A",
    "Dormitory block B",
    "Administration",
    "Cafeteria",
    "Sports facilities",
    "Server room",
    "HVAC systems",
    "Outdoor lighting",
    "Workshop",
    "Solar auxiliary systems",
]


def seed_object(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO objects (
            object_id, name, object_type, area_m2, installed_power_kw,
            operating_mode, solar_capacity_kw, battery_capacity_kwh
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            OBJECT["object_id"],
            OBJECT["name"],
            OBJECT["object_type"],
            OBJECT["area_m2"],
            OBJECT["installed_power_kw"],
            OBJECT["operating_mode"],
            OBJECT["solar_capacity_kw"],
            OBJECT["battery_capacity_kwh"],
        ),
    )


def seed_tariffs(connection: sqlite3.Connection) -> None:
    connection.executemany(
        """
        INSERT INTO tariff_zones (
            tariff_zone_id, name, start_hour, end_hour, price_uah_per_kwh
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (
                zone["tariff_zone_id"],
                zone["name"],
                zone["start_hour"],
                zone["end_hour"],
                zone["price_uah_per_kwh"],
            )
            for zone in TARIFF_ZONES
        ],
    )


def seed_meters(connection: sqlite3.Connection) -> None:
    rows = []
    for meter_id in range(1, OBJECT["meter_count"] + 1):
        if meter_id <= 2:
            level = 1
        elif meter_id <= 7:
            level = 2
        else:
            level = 3

        rows.append(
            (
                meter_id,
                OBJECT["object_id"],
                f"UNI-TR51-{meter_id:03d}",
                level,
                "electricity",
                "3-phase smart meter, hourly interval",
                METER_LOCATIONS[meter_id - 1],
                round(OBJECT["installed_power_kw"] / OBJECT["meter_count"] * 1.25, 2),
                "2025-01-01",
            )
        )

    connection.executemany(
        """
        INSERT INTO meters (
            meter_id, object_id, serial_number, accounting_level,
            resource_type, technical_params, installation_location,
            max_power_kw, installed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )


def load_weather(connection: sqlite3.Connection) -> None:
    path = GENERATED_DIR / "weather_data.csv"
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        connection.executemany(
            """
            INSERT INTO weather_data (
                object_id, measured_at, temperature_c, irradiation_w_m2
            )
            VALUES (:object_id, :measured_at, :temperature_c, :irradiation_w_m2)
            """,
            reader,
        )


def load_measurements(connection: sqlite3.Connection) -> None:
    path = GENERATED_DIR / "measurements.csv"
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        connection.executemany(
            """
            INSERT INTO measurements (
                meter_id, tariff_zone_id, measured_at, consumption_kwh,
                voltage_v, power_factor, quality_flag
            )
            VALUES (
                :meter_id, :tariff_zone_id, :measured_at, :consumption_kwh,
                :voltage_v, :power_factor, :quality_flag
            )
            """,
            reader,
        )


def seed_baselines(connection: sqlite3.Connection) -> None:
    monthly = defaultdict(float)
    for month, total in connection.execute(
        """
        SELECT CAST(strftime('%m', measured_at) AS INTEGER), SUM(consumption_kwh)
        FROM measurements
        GROUP BY CAST(strftime('%m', measured_at) AS INTEGER)
        """
    ):
        monthly[month] = total

    rows = []
    for month in range(1, 13):
        baseline = monthly[month] * 0.97
        rows.append((OBJECT["object_id"], month, round(baseline, 2), "generated_97_percent_of_actual"))

    connection.executemany(
        """
        INSERT INTO baselines (object_id, month, baseline_kwh, method)
        VALUES (?, ?, ?, ?)
        """,
        rows,
    )


def seed_efficiency_metrics(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        INSERT INTO energy_efficiency_metrics (
            object_id, period_start, period_end, total_consumption_kwh,
            kwh_per_m2, baseline_kwh, deviation_percent
        )
        SELECT
            o.object_id,
            date(ms.measured_at, 'start of month') AS period_start,
            date(ms.measured_at, 'start of month', '+1 month', '-1 day') AS period_end,
            SUM(ms.consumption_kwh) AS total_consumption_kwh,
            SUM(ms.consumption_kwh) / o.area_m2 AS kwh_per_m2,
            b.baseline_kwh,
            (SUM(ms.consumption_kwh) - b.baseline_kwh) * 100.0 / b.baseline_kwh AS deviation_percent
        FROM measurements ms
        JOIN meters m ON m.meter_id = ms.meter_id
        JOIN objects o ON o.object_id = m.object_id
        JOIN baselines b
            ON b.object_id = o.object_id
           AND b.month = CAST(strftime('%m', ms.measured_at) AS INTEGER)
        GROUP BY o.object_id, period_start, period_end, b.baseline_kwh
        """
    )


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database does not exist: {DB_PATH}. Run create_database.py first.")

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON;")
        seed_object(connection)
        seed_tariffs(connection)
        seed_meters(connection)
        load_weather(connection)
        load_measurements(connection)
        seed_baselines(connection)
        seed_efficiency_metrics(connection)

        counts = {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in ["objects", "meters", "weather_data", "measurements", "baselines", "energy_efficiency_metrics"]
        }

    print("Loaded database rows:")
    for table, count in counts.items():
        print(f"- {table}: {count}")


if __name__ == "__main__":
    main()
