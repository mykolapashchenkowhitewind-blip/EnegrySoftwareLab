import csv
import sqlite3
from datetime import datetime

from .paths import DB_PATH, LAB2_DIR, LAB3_DIR


OBJECT_META = {
    "student": "Pashchenko Mykola",
    "group": "TR-51mp",
    "discipline": "Програмне забезпечення енергетичного менеджменту",
    "variant": 8,
    "object": "University",
    "area_m2": 5200,
    "installed_power_kw": 350,
    "meters": 14,
    "operating_mode": "24/7",
    "solar_capacity_kw": 140,
    "battery_capacity_kwh": 110,
    "tariff": "3-zone",
}


def parse_date(value: str | None, name: str) -> str | None:
    if not value:
        return None
    try:
        datetime.fromisoformat(value.replace("T", " "))
    except ValueError as exc:
        raise ValueError(f"Invalid {name}. Use ISO format, for example 2025-01-01 or 2025-01-01 12:00:00.") from exc
    return value.replace("T", " ")


def query_rows(sql: str, params: tuple = ()) -> list[dict]:
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


def read_csv(path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def health() -> dict:
    return {
        "status": "ok",
        "database_exists": DB_PATH.exists(),
        "lab2_forecast_exists": (LAB2_DIR / "next_month_forecast.csv").exists(),
        "lab3_results_exists": (LAB3_DIR / "simulation_results.csv").exists(),
    }


def consumption_history(params: dict) -> list[dict]:
    start = parse_date(params.get("start", [""])[0], "start")
    end = parse_date(params.get("end", [""])[0], "end")
    meter_id = params.get("meter_id", [None])[0]
    level = params.get("level", [None])[0]

    sql = """
    SELECT
        ms.measured_at,
        m.meter_id,
        m.accounting_level,
        m.installation_location,
        ms.consumption_kwh,
        tz.name AS tariff_zone
    FROM measurements ms
    JOIN meters m ON m.meter_id = ms.meter_id
    JOIN tariff_zones tz ON tz.tariff_zone_id = ms.tariff_zone_id
    WHERE 1 = 1
    """
    values: list = []
    if start:
        sql += " AND ms.measured_at >= ?"
        values.append(start)
    if end:
        sql += " AND ms.measured_at <= ?"
        values.append(end)
    if meter_id:
        sql += " AND m.meter_id = ?"
        values.append(int(meter_id))
    if level:
        sql += " AND m.accounting_level = ?"
        values.append(int(level))
    sql += " ORDER BY ms.measured_at LIMIT 2000"
    return query_rows(sql, tuple(values))


def aggregate_consumption(params: dict) -> list[dict]:
    period = params.get("period", ["day"])[0]
    if period not in {"hour", "day", "month"}:
        raise ValueError("period must be one of: hour, day, month")
    start = parse_date(params.get("start", [""])[0], "start")
    end = parse_date(params.get("end", [""])[0], "end")
    bucket = {
        "hour": "strftime('%Y-%m-%d %H:00:00', hoc.measured_at)",
        "day": "date(hoc.measured_at)",
        "month": "strftime('%Y-%m', hoc.measured_at)",
    }[period]
    sql = f"""
    SELECT
        {bucket} AS period,
        ROUND(SUM(hoc.total_consumption_kwh), 3) AS consumption_kwh
    FROM v_hourly_object_consumption hoc
    WHERE 1 = 1
    """
    values: list = []
    if start:
        sql += " AND hoc.measured_at >= ?"
        values.append(start)
    if end:
        sql += " AND hoc.measured_at <= ?"
        values.append(end)
    sql += f" GROUP BY {bucket} ORDER BY period"
    return query_rows(sql, tuple(values))


def baseline() -> list[dict]:
    return query_rows(
        """
        SELECT
            b.month,
            ROUND(b.baseline_kwh, 2) AS baseline_kwh,
            ROUND(SUM(ms.consumption_kwh), 2) AS actual_kwh
        FROM baselines b
        JOIN objects o ON o.object_id = b.object_id
        JOIN meters m ON m.object_id = o.object_id
        JOIN measurements ms
            ON ms.meter_id = m.meter_id
           AND CAST(strftime('%m', ms.measured_at) AS INTEGER) = b.month
        GROUP BY b.month, b.baseline_kwh
        ORDER BY b.month
        """
    )


def forecast() -> list[dict]:
    return read_csv(LAB2_DIR / "next_month_forecast.csv")


def model_comparison() -> list[dict]:
    return read_csv(LAB2_DIR / "model_comparison.csv")


def ems_results() -> list[dict]:
    return read_csv(LAB3_DIR / "simulation_results.csv")


def ems_metrics() -> dict:
    return {
        "energy": read_csv(LAB3_DIR / "energy_metrics.csv"),
        "economic": read_csv(LAB3_DIR / "economic_metrics.csv"),
    }


def dashboard_summary() -> dict:
    aggregate = aggregate_consumption({"period": ["day"]})
    forecast_rows = forecast()
    ems = ems_metrics()
    latest = query_rows(
        """
        SELECT measured_at, ROUND(total_consumption_kwh, 3) AS consumption_kwh
        FROM v_hourly_object_consumption
        ORDER BY measured_at DESC
        LIMIT 1
        """
    )
    total_year = sum(float(row["consumption_kwh"]) for row in aggregate)
    forecast_total = sum(float(row.get("forecast_kwh", 0) or 0) for row in forecast_rows)
    weekly_savings = next((float(row["value"]) for row in ems["economic"] if row["metric"] == "weekly_savings_uah"), 0)
    pv_generation = next((float(row["value"]) for row in ems["energy"] if row["metric"] == "total_pv_generation_kwh"), 0)
    avg_soc = next((float(row["value"]) for row in ems["energy"] if row["metric"] == "avg_soc_percent"), 0)
    return {
        "latest": latest[0] if latest else {},
        "year_consumption_kwh": round(total_year, 2),
        "forecast_next_month_kwh": round(forecast_total, 2),
        "weekly_savings_uah": round(weekly_savings, 2),
        "pv_generation_week_kwh": round(pv_generation, 2),
        "avg_battery_soc_percent": round(avg_soc, 2),
        "co2_estimate_kg": round(total_year * 0.4, 2),
    }


def report_summary() -> dict:
    return {
        "object": OBJECT_META,
        "dashboard": dashboard_summary(),
        "baseline": baseline(),
        "models": model_comparison(),
        "ems_metrics": ems_metrics(),
    }
