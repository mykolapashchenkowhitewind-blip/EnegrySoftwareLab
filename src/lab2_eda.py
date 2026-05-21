import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from config import PROJECT_ROOT


DATA_PATH = PROJECT_ROOT / "data" / "lab2" / "analysis_dataset.csv"
LAB2_DIR = PROJECT_ROOT / "data" / "lab2"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
REPORT_PATH = PROJECT_ROOT / "docs" / "lab2_report.md"


def save_current_figure(name: str) -> None:
    path = FIGURES_DIR / name
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()


def load_dataset() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, parse_dates=["measured_at"])


def write_statistics(df: pd.DataFrame) -> None:
    numeric_columns = [
        "total_consumption_kwh",
        "temperature_c",
        "irradiation_w_m2",
        "hdd_18",
        "cdd_22",
        "kwh_per_m2",
    ]
    df[numeric_columns].describe().T.to_csv(LAB2_DIR / "descriptive_statistics.csv")
    df.isna().sum().rename("missing_values").to_csv(LAB2_DIR / "missing_values.csv")

    q1 = df["total_consumption_kwh"].quantile(0.25)
    q3 = df["total_consumption_kwh"].quantile(0.75)
    iqr = q3 - q1
    outliers = df[
        (df["total_consumption_kwh"] < q1 - 1.5 * iqr)
        | (df["total_consumption_kwh"] > q3 + 1.5 * iqr)
    ]
    pd.DataFrame(
        {
            "metric": ["q1", "q3", "iqr", "outlier_count"],
            "value": [q1, q3, iqr, len(outliers)],
        }
    ).to_csv(LAB2_DIR / "outlier_summary.csv", index=False)

    autocorr_rows = []
    for lag in [1, 24, 48, 168]:
        autocorr_rows.append({"lag_hours": lag, "autocorrelation": df["total_consumption_kwh"].autocorr(lag)})
    pd.DataFrame(autocorr_rows).to_csv(LAB2_DIR / "autocorrelation.csv", index=False)


def create_figures(df: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(12, 4))
    sns.lineplot(data=df, x="measured_at", y="total_consumption_kwh", linewidth=0.8)
    plt.title("Consumption Across the Year")
    plt.xlabel("Time")
    plt.ylabel("kWh")
    save_current_figure("01_consumption_timeseries.png")

    plt.figure(figsize=(8, 5))
    sns.histplot(df["total_consumption_kwh"], bins=40, kde=True)
    plt.title("Consumption Distribution")
    plt.xlabel("kWh")
    save_current_figure("02_consumption_distribution.png")

    plt.figure(figsize=(10, 5))
    sns.boxplot(data=df, x="hour", y="total_consumption_kwh")
    plt.title("Consumption by Hour")
    plt.xlabel("Hour")
    plt.ylabel("kWh")
    save_current_figure("03_boxplot_by_hour.png")

    daily_profile = df.groupby("hour", as_index=False)["total_consumption_kwh"].mean()
    plt.figure(figsize=(9, 5))
    sns.lineplot(data=daily_profile, x="hour", y="total_consumption_kwh", marker="o")
    plt.title("Typical Daily Profile")
    plt.xlabel("Hour")
    plt.ylabel("Average kWh")
    save_current_figure("04_daily_profile.png")

    weekend_profile = df.groupby(["hour", "is_weekend"], as_index=False)["total_consumption_kwh"].mean()
    weekend_profile["day_type"] = weekend_profile["is_weekend"].map({0: "workday", 1: "weekend"})
    plt.figure(figsize=(9, 5))
    sns.lineplot(data=weekend_profile, x="hour", y="total_consumption_kwh", hue="day_type", marker="o")
    plt.title("Workday vs Weekend Profile")
    plt.xlabel("Hour")
    plt.ylabel("Average kWh")
    save_current_figure("05_workday_vs_weekend.png")

    monthly = df.groupby("month", as_index=False)["total_consumption_kwh"].sum()
    plt.figure(figsize=(9, 5))
    sns.barplot(data=monthly, x="month", y="total_consumption_kwh")
    plt.title("Monthly Consumption Dynamics")
    plt.xlabel("Month")
    plt.ylabel("Total kWh")
    save_current_figure("06_monthly_dynamics.png")

    heatmap_data = df.pivot_table(
        values="total_consumption_kwh",
        index="hour",
        columns="day_of_week",
        aggfunc="mean",
    )
    plt.figure(figsize=(9, 6))
    sns.heatmap(heatmap_data, cmap="viridis")
    plt.title("Heatmap: Hour x Day of Week")
    plt.xlabel("Day of week")
    plt.ylabel("Hour")
    save_current_figure("07_heatmap_hour_weekday.png")

    plt.figure(figsize=(8, 5))
    sns.scatterplot(data=df.sample(min(1500, len(df)), random_state=51), x="temperature_c", y="total_consumption_kwh", alpha=0.45)
    plt.title("Consumption vs Temperature")
    plt.xlabel("Temperature, C")
    plt.ylabel("kWh")
    save_current_figure("08_temperature_consumption.png")

    corr_cols = [
        "total_consumption_kwh",
        "temperature_c",
        "irradiation_w_m2",
        "hdd_18",
        "cdd_22",
        "hour",
        "is_weekend",
        "tariff_zone_code",
        "lag_24h",
        "rolling_24h_mean",
    ]
    plt.figure(figsize=(10, 8))
    sns.heatmap(df[corr_cols].corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("Correlation Matrix")
    save_current_figure("09_correlation_matrix.png")

    monthly_temp = df.groupby("month", as_index=False)[["temperature_c", "total_consumption_kwh"]].mean()
    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.plot(monthly_temp["month"], monthly_temp["total_consumption_kwh"], color="tab:blue", marker="o")
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Average kWh", color="tab:blue")
    ax2 = ax1.twinx()
    ax2.plot(monthly_temp["month"], monthly_temp["temperature_c"], color="tab:red", marker="s")
    ax2.set_ylabel("Average temperature, C", color="tab:red")
    plt.title("Monthly Consumption and Temperature")
    save_current_figure("10_monthly_temperature.png")


def write_report_stub(df: pd.DataFrame) -> None:
    stats = pd.read_csv(LAB2_DIR / "descriptive_statistics.csv")
    outliers = pd.read_csv(LAB2_DIR / "outlier_summary.csv")
    autocorr = pd.read_csv(LAB2_DIR / "autocorrelation.csv")

    text = f"""# Lab 2 Report

**Theme:** Аналіз даних та прогнозування енергоспоживання  
**Discipline:** Програмне забезпечення енергетичного менеджменту  
**Student:** Pashchenko Mykola  
**Group:** TR-51mp  
**Variant:** 8, University

## Dataset

The dataset is built from Lab 1 SQLite data and contains {len(df)} hourly records after feature engineering. The original object has 14 meters, 5200 m2 area, 350 kW installed power, and a 3-zone tariff.

## Exploratory Analysis

Generated files:

- `data/lab2/descriptive_statistics.csv`
- `data/lab2/missing_values.csv`
- `data/lab2/outlier_summary.csv`
- `data/lab2/autocorrelation.csv`
- `reports/figures/*.png`

Key consumption statistics:

```text
{stats.to_string(index=False)}
```

Outlier summary:

```text
{outliers.to_string(index=False)}
```

Autocorrelation:

```text
{autocorr.to_string(index=False)}
```

## Factor Analysis

HDD is calculated as `max(0, 18 - temperature_c)`. CDD is calculated as `max(0, temperature_c - 22)`. Correlations are visualized in `reports/figures/09_correlation_matrix.png`.

## Modeling and Forecast

Model comparison and forecast sections are appended after running `src/lab2_train_models.py` and `src/lab2_forecast.py`.
"""
    REPORT_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Prepared dataset was not found: {DATA_PATH}. Run lab2_prepare_dataset.py first.")

    LAB2_DIR.mkdir(parents=True, exist_ok=True)
    df = load_dataset()
    write_statistics(df)
    create_figures(df)
    write_report_stub(df)
    print(f"EDA complete. Figures: {FIGURES_DIR}")
    print(f"Report started: {REPORT_PATH}")


if __name__ == "__main__":
    main()
