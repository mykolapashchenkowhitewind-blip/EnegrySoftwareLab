import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from config import OBJECT, PROJECT_ROOT


RESULTS_PATH = PROJECT_ROOT / "data" / "lab3" / "simulation_results.csv"
LAB3_DIR = PROJECT_ROOT / "data" / "lab3"
FIGURES_DIR = PROJECT_ROOT / "reports" / "lab3_figures"
REPORT_PATH = PROJECT_ROOT / "docs" / "lab3_report.md"
ARCHITECTURE_PATH = PROJECT_ROOT / "docs" / "lab3_architecture.md"

PV_CAPEX_UAH_PER_KW = 26000
BATTERY_CAPEX_UAH_PER_KWH = 12000


def save_figure(name: str) -> None:
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / name, dpi=150)
    plt.close()


def calculate_energy_metrics(df: pd.DataFrame) -> pd.DataFrame:
    total_load = df["load_kwh"].sum()
    total_pv = df["pv_generation_kwh"].sum()
    pv_self_consumed = (df["pv_to_load_kwh"] + df["battery_charge_from_pv_kwh"]).sum()
    discharged = df["battery_discharge_kwh"].sum()
    charged = (df["battery_charge_from_pv_kwh"] + df["battery_charge_from_grid_kwh"]).sum()
    cycles = discharged / OBJECT["battery_capacity_kwh"]

    metrics = [
        ("total_consumption_kwh", total_load),
        ("total_pv_generation_kwh", total_pv),
        ("pv_coverage_percent", total_pv / total_load * 100 if total_load else 0),
        ("pv_self_consumption_percent", pv_self_consumed / total_pv * 100 if total_pv else 0),
        ("grid_import_kwh", df["grid_import_kwh"].sum()),
        ("grid_export_kwh", df["grid_export_kwh"].sum()),
        ("battery_charged_kwh", charged),
        ("battery_discharged_kwh", discharged),
        ("approx_battery_cycles", cycles),
        ("min_soc_percent", df["battery_soc_percent"].min()),
        ("max_soc_percent", df["battery_soc_percent"].max()),
        ("avg_soc_percent", df["battery_soc_percent"].mean()),
    ]
    return pd.DataFrame(metrics, columns=["metric", "value"])


def calculate_economic_metrics(df: pd.DataFrame) -> pd.DataFrame:
    baseline_cost = df["baseline_cost_without_pv_battery_uah"].sum()
    import_cost = df["import_cost_uah"].sum()
    export_revenue = df["export_revenue_uah"].sum()
    net_cost = df["net_cost_uah"].sum()
    weekly_savings = baseline_cost - net_cost
    annual_savings = weekly_savings * 52
    capex = OBJECT["solar_capacity_kw"] * PV_CAPEX_UAH_PER_KW + OBJECT["battery_capacity_kwh"] * BATTERY_CAPEX_UAH_PER_KWH
    payback_years = capex / annual_savings if annual_savings > 0 else None

    metrics = [
        ("baseline_cost_without_pv_battery_uah", baseline_cost),
        ("import_cost_with_ems_uah", import_cost),
        ("export_revenue_uah", export_revenue),
        ("net_cost_with_ems_uah", net_cost),
        ("weekly_savings_uah", weekly_savings),
        ("projected_annual_savings_uah", annual_savings),
        ("assumed_capex_uah", capex),
        ("simple_payback_years", payback_years if payback_years is not None else 0),
    ]
    return pd.DataFrame(metrics, columns=["metric", "value"])


def create_figures(df: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["savings_uah"] = df["baseline_cost_without_pv_battery_uah"] - df["net_cost_uah"]

    plt.figure(figsize=(12, 5))
    plt.plot(df["timestamp"], df["load_kwh"], label="load", linewidth=1.2)
    plt.plot(df["timestamp"], df["pv_generation_kwh"], label="PV generation", linewidth=1.2)
    plt.plot(df["timestamp"], df["grid_import_kwh"], label="grid import", linewidth=1.2)
    plt.plot(df["timestamp"], df["grid_export_kwh"], label="grid export", linewidth=1.2)
    plt.title("Energy Balance")
    plt.xlabel("Time")
    plt.ylabel("kWh")
    plt.legend()
    save_figure("01_energy_balance.png")

    plt.figure(figsize=(12, 4))
    plt.plot(df["timestamp"], df["battery_soc_percent"], color="tab:green")
    plt.axhline(20, color="tab:red", linestyle="--", linewidth=1)
    plt.axhline(90, color="tab:red", linestyle="--", linewidth=1)
    plt.title("Battery SOC")
    plt.xlabel("Time")
    plt.ylabel("SOC, percent")
    save_figure("02_battery_soc.png")

    plt.figure(figsize=(12, 4))
    plt.bar(df["timestamp"], df["grid_import_kwh"], label="import", width=0.035)
    plt.bar(df["timestamp"], -df["grid_export_kwh"], label="export", width=0.035)
    plt.title("Grid Import and Export")
    plt.xlabel("Time")
    plt.ylabel("kWh")
    plt.legend()
    save_figure("03_grid_import_export.png")

    sources = pd.DataFrame(
        {
            "source": ["PV direct", "Battery", "Grid"],
            "kwh": [df["pv_to_load_kwh"].sum(), df["battery_discharge_kwh"].sum(), df["grid_import_kwh"].sum()],
        }
    )
    plt.figure(figsize=(7, 5))
    sns.barplot(data=sources, x="source", y="kwh")
    plt.title("Consumption Sources")
    plt.xlabel("Source")
    plt.ylabel("kWh")
    save_figure("04_consumption_sources.png")

    savings = df.groupby("tariff_zone", as_index=False)["savings_uah"].sum()
    plt.figure(figsize=(7, 5))
    sns.barplot(data=savings, x="tariff_zone", y="savings_uah")
    plt.title("Savings by Tariff Zone")
    plt.xlabel("Tariff zone")
    plt.ylabel("UAH")
    save_figure("05_tariff_zone_savings.png")

    cost = pd.DataFrame(
        {
            "scenario": ["Baseline", "EMS net cost"],
            "cost_uah": [df["baseline_cost_without_pv_battery_uah"].sum(), df["net_cost_uah"].sum()],
        }
    )
    plt.figure(figsize=(7, 5))
    sns.barplot(data=cost, x="scenario", y="cost_uah")
    plt.title("Cost Comparison")
    plt.xlabel("Scenario")
    plt.ylabel("UAH")
    save_figure("06_cost_comparison.png")


def write_architecture() -> None:
    ARCHITECTURE_PATH.write_text(
        """# Lab 3 EMS Architecture

```mermaid
flowchart LR
    Weather["Weather data: irradiation, temperature"] --> PV["Solar PV model"]
    LoadData["Lab 1 / Lab 2 load profile"] --> Load["University load"]
    Tariff["3-zone tariff"] --> EMS["EMS controller"]
    PV --> EMS
    Load --> EMS
    Battery["Battery model"] <--> EMS
    Grid["Grid model"] <--> EMS
    EMS --> Results["Simulation results and metrics"]
```
""",
        encoding="utf-8",
    )


def write_report(energy: pd.DataFrame, economic: pd.DataFrame) -> None:
    REPORT_PATH.write_text(
        f"""# Lab 3 Report

**Theme:** EMS energy-flow control simulation  
**Discipline:** Programne zabezpechennia enerhetychnoho menedzhmentu  
**Student:** Pashchenko Mykola  
**Group:** TR-51mp  
**Variant:** 8, University

## Goal

The goal is to model and test an EMS for a University object with solar PV, battery storage, grid connection, and hourly load. The controller decides when to use PV directly, charge or discharge the battery, import energy, and export surplus energy.

## System Parameters

- Load profile: average 85 kW, range 50-130 kW.
- Solar PV capacity: {OBJECT['solar_capacity_kw']} kW.
- Battery capacity: {OBJECT['battery_capacity_kwh']} kWh.
- Initial SOC: 50 percent.
- SOC limits: 20-90 percent.
- Simulation period: 7 days.
- Time step: 1 hour.
- Tariff: 3-zone tariff.

## Control Algorithm

For each hour, the EMS calculates PV generation and compares it with load. If PV exceeds load, the surplus charges the battery and then exports to the grid. If PV is not enough, the controller discharges the battery during peak or selected half-peak hours and imports the remaining deficit from the grid. During the night tariff zone, the battery may charge from the grid when SOC is low because electricity is cheaper.

## Energy Metrics

```text
{energy.round(3).to_string(index=False)}
```

## Economic Metrics

```text
{economic.round(3).to_string(index=False)}
```

## Visualizations

Figures are saved in `reports/lab3_figures/`:

- `01_energy_balance.png`
- `02_battery_soc.png`
- `03_grid_import_export.png`
- `04_consumption_sources.png`
- `05_tariff_zone_savings.png`
- `06_cost_comparison.png`

## Conclusion

The EMS reduces grid import by using PV generation directly and by shifting part of the energy through the battery. The battery is most useful in expensive tariff periods, while the night tariff is used for additional charging when SOC is low. The economic result is measured by comparing the baseline cost without PV/battery to the net EMS cost after import payments and export revenue.
""",
        encoding="utf-8",
    )


def main() -> None:
    if not RESULTS_PATH.exists():
        raise FileNotFoundError(f"Simulation results were not found: {RESULTS_PATH}. Run lab3_simulate_ems.py first.")

    LAB3_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(RESULTS_PATH)
    energy = calculate_energy_metrics(df)
    economic = calculate_economic_metrics(df)
    energy.to_csv(LAB3_DIR / "energy_metrics.csv", index=False)
    economic.to_csv(LAB3_DIR / "economic_metrics.csv", index=False)
    create_figures(df)
    write_architecture()
    write_report(energy, economic)

    print(f"Energy metrics saved: {LAB3_DIR / 'energy_metrics.csv'}")
    print(f"Economic metrics saved: {LAB3_DIR / 'economic_metrics.csv'}")
    print(f"Report saved: {REPORT_PATH}")


if __name__ == "__main__":
    main()
