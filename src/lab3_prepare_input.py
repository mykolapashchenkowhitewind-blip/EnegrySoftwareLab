import sqlite3

import pandas as pd

from config import DB_PATH, PROJECT_ROOT


OUTPUT_DIR = PROJECT_ROOT / "data" / "lab3"
OUTPUT_PATH = OUTPUT_DIR / "simulation_input.csv"


def load_data() -> pd.DataFrame:
    query = """
    SELECT
        hoc.measured_at AS timestamp,
        hoc.total_consumption_kwh AS load_kwh,
        wd.irradiation_w_m2,
        wd.temperature_c
    FROM v_hourly_object_consumption hoc
    JOIN weather_data wd
        ON wd.object_id = hoc.object_id
       AND wd.measured_at = hoc.measured_at
    ORDER BY hoc.measured_at
    """
    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(query, connection, parse_dates=["timestamp"])


def tariff_zone(hour: int) -> str:
    if hour >= 23 or hour < 7:
        return "night"
    if 8 <= hour < 11 or 20 <= hour < 22:
        return "peak"
    return "half_peak"


def tariff_price(zone: str) -> float:
    return {"night": 2.64, "half_peak": 5.28, "peak": 7.92}[zone]


def select_typical_week(df: pd.DataFrame) -> pd.DataFrame:
    # A spring week gives both meaningful solar generation and normal university load.
    start = pd.Timestamp("2025-04-07 00:00:00")
    end = start + pd.Timedelta(days=7)
    week = df[(df["timestamp"] >= start) & (df["timestamp"] < end)].copy()
    if len(week) != 168:
        week = df.iloc[:168].copy()
    return week.reset_index(drop=True)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database was not found: {DB_PATH}. Run Lab 1 first.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    data = select_typical_week(load_data())
    data["tariff_zone"] = data["timestamp"].dt.hour.map(tariff_zone)
    data["tariff_price_uah_per_kwh"] = data["tariff_zone"].map(tariff_price)

    if (PROJECT_ROOT / "data" / "lab2" / "next_month_forecast.csv").exists():
        forecast = pd.read_csv(PROJECT_ROOT / "data" / "lab2" / "next_month_forecast.csv")
        data["day_ahead_load_forecast_kwh"] = forecast["forecast_kwh"].head(len(data)).to_numpy()
    else:
        data["day_ahead_load_forecast_kwh"] = data["load_kwh"].rolling(24, min_periods=1).mean()

    data.to_csv(OUTPUT_PATH, index=False)
    print(f"Prepared Lab 3 simulation input: {OUTPUT_PATH}")
    print(f"Rows: {len(data)}")


if __name__ == "__main__":
    main()
