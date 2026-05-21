import sqlite3

import numpy as np
import pandas as pd

from config import DB_PATH, OBJECT, PROJECT_ROOT


OUTPUT_DIR = PROJECT_ROOT / "data" / "lab2"
OUTPUT_PATH = OUTPUT_DIR / "analysis_dataset.csv"


def load_hourly_dataset() -> pd.DataFrame:
    query = """
    SELECT
        hoc.measured_at,
        hoc.total_consumption_kwh,
        wd.temperature_c,
        wd.irradiation_w_m2,
        o.area_m2,
        o.installed_power_kw,
        o.solar_capacity_kw,
        o.battery_capacity_kwh
    FROM v_hourly_object_consumption hoc
    JOIN weather_data wd
        ON wd.object_id = hoc.object_id
       AND wd.measured_at = hoc.measured_at
    JOIN objects o
        ON o.object_id = hoc.object_id
    ORDER BY hoc.measured_at
    """
    with sqlite3.connect(DB_PATH) as connection:
        return pd.read_sql_query(query, connection, parse_dates=["measured_at"])


def tariff_zone(hour: int) -> str:
    if hour >= 23 or hour < 7:
        return "night"
    if 8 <= hour < 11 or 20 <= hour < 22:
        return "peak"
    return "half_peak"


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    prepared["hour"] = prepared["measured_at"].dt.hour
    prepared["day_of_week"] = prepared["measured_at"].dt.dayofweek
    prepared["month"] = prepared["measured_at"].dt.month
    prepared["day_of_year"] = prepared["measured_at"].dt.dayofyear
    prepared["is_weekend"] = prepared["day_of_week"].isin([5, 6]).astype(int)
    prepared["is_working_hour"] = prepared["hour"].between(8, 17).astype(int)
    prepared["tariff_zone"] = prepared["hour"].map(tariff_zone)
    prepared["tariff_zone_code"] = prepared["tariff_zone"].map({"night": 0, "half_peak": 1, "peak": 2})

    prepared["hdd_18"] = np.maximum(0, 18 - prepared["temperature_c"])
    prepared["cdd_22"] = np.maximum(0, prepared["temperature_c"] - 22)
    prepared["hour_sin"] = np.sin(2 * np.pi * prepared["hour"] / 24)
    prepared["hour_cos"] = np.cos(2 * np.pi * prepared["hour"] / 24)
    prepared["month_sin"] = np.sin(2 * np.pi * prepared["month"] / 12)
    prepared["month_cos"] = np.cos(2 * np.pi * prepared["month"] / 12)

    prepared["lag_1h"] = prepared["total_consumption_kwh"].shift(1)
    prepared["lag_24h"] = prepared["total_consumption_kwh"].shift(24)
    prepared["lag_168h"] = prepared["total_consumption_kwh"].shift(168)
    prepared["rolling_24h_mean"] = prepared["total_consumption_kwh"].shift(1).rolling(24).mean()
    prepared["rolling_24h_std"] = prepared["total_consumption_kwh"].shift(1).rolling(24).std()

    prepared["kwh_per_m2"] = prepared["total_consumption_kwh"] / prepared["area_m2"]
    prepared["object_name"] = OBJECT["name"]
    return prepared.dropna().reset_index(drop=True)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database was not found: {DB_PATH}. Run Lab 1 scripts first.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = load_hourly_dataset()
    prepared = add_features(raw)
    prepared.to_csv(OUTPUT_PATH, index=False)

    print(f"Prepared Lab 2 dataset: {OUTPUT_PATH}")
    print(f"Rows: {len(prepared)}")
    print(f"Columns: {len(prepared.columns)}")


if __name__ == "__main__":
    main()
