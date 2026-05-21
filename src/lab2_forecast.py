import pickle
from datetime import timedelta

import numpy as np
import pandas as pd

from config import PROJECT_ROOT


DATA_PATH = PROJECT_ROOT / "data" / "lab2" / "analysis_dataset.csv"
LAB2_DIR = PROJECT_ROOT / "data" / "lab2"
MODEL_PATH = PROJECT_ROOT / "models" / "lab2_best_model.pkl"
REPORT_PATH = PROJECT_ROOT / "docs" / "lab2_report.md"

TARIFF_PRICES = {"night": 2.64, "half_peak": 5.28, "peak": 7.92}


def tariff_zone(hour: int) -> str:
    if hour >= 23 or hour < 7:
        return "night"
    if 8 <= hour < 11 or 20 <= hour < 22:
        return "peak"
    return "half_peak"


def build_next_month_features(history: pd.DataFrame, payload: dict) -> pd.DataFrame:
    last_time = history["measured_at"].max()
    start = last_time + timedelta(hours=1)
    periods = 24 * 31
    future = pd.DataFrame({"measured_at": pd.date_range(start=start, periods=periods, freq="h")})

    climatology = history.groupby(["month", "day_of_week", "hour"], as_index=False)[
        ["temperature_c", "irradiation_w_m2", "total_consumption_kwh"]
    ].mean()

    future["hour"] = future["measured_at"].dt.hour
    future["day_of_week"] = future["measured_at"].dt.dayofweek
    future["month"] = future["measured_at"].dt.month
    future["day_of_year"] = future["measured_at"].dt.dayofyear
    future = future.merge(climatology, on=["month", "day_of_week", "hour"], how="left")

    fallback = history.groupby(["month", "hour"], as_index=False)[["temperature_c", "irradiation_w_m2", "total_consumption_kwh"]].mean()
    future = future.merge(fallback, on=["month", "hour"], how="left", suffixes=("", "_fallback"))
    for column in ["temperature_c", "irradiation_w_m2", "total_consumption_kwh"]:
        future[column] = future[column].fillna(future[f"{column}_fallback"])
        future[column] = future[column].fillna(history[column].mean())
        future = future.drop(columns=[f"{column}_fallback"])

    future["is_weekend"] = future["day_of_week"].isin([5, 6]).astype(int)
    future["is_working_hour"] = future["hour"].between(8, 17).astype(int)
    future["tariff_zone"] = future["hour"].map(tariff_zone)
    future["tariff_zone_code"] = future["tariff_zone"].map({"night": 0, "half_peak": 1, "peak": 2})
    future["hdd_18"] = np.maximum(0, 18 - future["temperature_c"])
    future["cdd_22"] = np.maximum(0, future["temperature_c"] - 22)
    future["hour_sin"] = np.sin(2 * np.pi * future["hour"] / 24)
    future["hour_cos"] = np.cos(2 * np.pi * future["hour"] / 24)
    future["month_sin"] = np.sin(2 * np.pi * future["month"] / 12)
    future["month_cos"] = np.cos(2 * np.pi * future["month"] / 12)

    combined = pd.concat(
        [
            history[["measured_at", "total_consumption_kwh"]].tail(200),
            future[["measured_at", "total_consumption_kwh"]],
        ],
        ignore_index=True,
    )
    combined["lag_1h"] = combined["total_consumption_kwh"].shift(1)
    combined["lag_24h"] = combined["total_consumption_kwh"].shift(24)
    combined["lag_168h"] = combined["total_consumption_kwh"].shift(168)
    combined["rolling_24h_mean"] = combined["total_consumption_kwh"].shift(1).rolling(24).mean()
    combined["rolling_24h_std"] = combined["total_consumption_kwh"].shift(1).rolling(24).std()

    future = future.merge(
        combined[["measured_at", "lag_1h", "lag_24h", "lag_168h", "rolling_24h_mean", "rolling_24h_std"]],
        on="measured_at",
        how="left",
    )
    for feature in ["lag_1h", "lag_24h", "lag_168h", "rolling_24h_mean", "rolling_24h_std"]:
        future[feature] = future[feature].fillna(history[feature].median())

    return future


def predict(payload: dict, future: pd.DataFrame) -> pd.DataFrame:
    model_name = payload["best_model_name"]
    if model_name == "Persistence_24h":
        future["forecast_kwh"] = future["lag_24h"]
    elif model_name == "Simple_Linear_Regression":
        future["forecast_kwh"] = payload["model"].predict(future[payload["simple_features"]])
    else:
        future["forecast_kwh"] = payload["model"].predict(future[payload["features"]])

    future["forecast_kwh"] = future["forecast_kwh"].clip(lower=0)
    future["tariff_price_uah_per_kwh"] = future["tariff_zone"].map(TARIFF_PRICES)
    future["forecast_cost_uah"] = future["forecast_kwh"] * future["tariff_price_uah_per_kwh"]
    return future


def append_report(forecast: pd.DataFrame, residuals: pd.DataFrame, model_name: str) -> None:
    total_kwh = forecast["forecast_kwh"].sum()
    total_cost = forecast["forecast_cost_uah"].sum()
    residual_std = residuals["residual_kwh"].std()
    lower = total_kwh - 1.96 * residual_std * np.sqrt(len(forecast))
    upper = total_kwh + 1.96 * residual_std * np.sqrt(len(forecast))
    by_tariff = forecast.groupby("tariff_zone", as_index=False).agg(
        forecast_kwh=("forecast_kwh", "sum"),
        forecast_cost_uah=("forecast_cost_uah", "sum"),
    )

    text = f"""

## Next-Month Forecast

Best model used for forecasting: **{model_name}**.

- Forecast horizon: {len(forecast)} hourly records.
- Expected consumption: {total_kwh:.2f} kWh.
- Expected cost: {total_cost:.2f} UAH.
- Approximate 95 percent interval for total consumption: {lower:.2f} to {upper:.2f} kWh.

Forecast by tariff zone:

```text
{by_tariff.round(2).to_string(index=False)}
```

## Analytical Conclusion

The University object has a clear daily and weekly pattern: working hours are generally higher than night hours, while weekend consumption is lower but still present because the object operates 24/7. Temperature-related features, lagged consumption, and rolling statistics are useful predictors because the generated load includes seasonal behavior and stable operational cycles. The best model was selected by the lowest RMSE on the chronological test set, which represents the last 20 percent of the year. The next-month forecast can be used as an operational estimate of expected energy demand and tariff-zone cost.
"""
    with REPORT_PATH.open("a", encoding="utf-8") as file:
        file.write(text)


def main() -> None:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Saved model was not found: {MODEL_PATH}. Run lab2_train_models.py first.")

    history = pd.read_csv(DATA_PATH, parse_dates=["measured_at"])
    residuals = pd.read_csv(LAB2_DIR / "residuals.csv", parse_dates=["measured_at"])
    with MODEL_PATH.open("rb") as file:
        payload = pickle.load(file)

    future = build_next_month_features(history, payload)
    forecast = predict(payload, future)
    output_columns = ["measured_at", "tariff_zone", "forecast_kwh", "tariff_price_uah_per_kwh", "forecast_cost_uah"]
    forecast[output_columns].to_csv(LAB2_DIR / "next_month_forecast.csv", index=False)
    append_report(forecast, residuals, payload["best_model_name"])

    print(f"Forecast saved: {LAB2_DIR / 'next_month_forecast.csv'}")
    print(f"Total forecast kWh: {forecast['forecast_kwh'].sum():.2f}")
    print(f"Total forecast cost UAH: {forecast['forecast_cost_uah'].sum():.2f}")


if __name__ == "__main__":
    main()
