import pandas as pd

from config import OBJECT, PROJECT_ROOT
from lab3_components import Battery, Grid, SolarPV


INPUT_PATH = PROJECT_ROOT / "data" / "lab3" / "simulation_input.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "lab3" / "simulation_results.csv"


def simulate_step(row: pd.Series, pv: SolarPV, battery: Battery, grid: Grid) -> dict:
    load_kwh = float(row["load_kwh"])
    tariff_zone = row["tariff_zone"]
    tariff_price = float(row["tariff_price_uah_per_kwh"])
    pv_generation = pv.generation(float(row["irradiation_w_m2"]), float(row["temperature_c"]))

    pv_to_load = min(load_kwh, pv_generation)
    remaining_load = load_kwh - pv_to_load
    surplus_pv = pv_generation - pv_to_load

    battery_charge_from_pv = 0.0
    battery_charge_from_grid = 0.0
    battery_discharge = 0.0
    grid_import = 0.0
    grid_export = 0.0

    if surplus_pv > 0:
        battery_charge_from_pv = battery.charge(surplus_pv)
        surplus_pv -= battery_charge_from_pv
        grid_export = grid.export_energy(surplus_pv)
    else:
        if tariff_zone == "peak":
            battery_discharge = battery.discharge(remaining_load)
            remaining_load -= battery_discharge
        elif tariff_zone == "half_peak" and battery.soc_percent > 45:
            battery_discharge = battery.discharge(remaining_load * 0.65)
            remaining_load -= battery_discharge

        grid_import = grid.import_energy(remaining_load)

    if tariff_zone == "night" and battery.soc_percent < 70:
        requested_charge = min(OBJECT["battery_capacity_kwh"] * 0.18, grid.import_limit_kw - grid_import)
        if requested_charge > 0:
            battery_charge_from_grid = battery.charge(requested_charge)
            grid_import += battery_charge_from_grid

    import_cost = grid.import_cost(grid_import, tariff_price)
    export_revenue = grid.export_revenue(grid_export)
    baseline_cost = load_kwh * tariff_price
    net_cost = import_cost - export_revenue
    battery.apply_self_discharge()

    return {
        "timestamp": row["timestamp"],
        "load_kwh": load_kwh,
        "pv_generation_kwh": pv_generation,
        "pv_to_load_kwh": pv_to_load,
        "battery_charge_from_pv_kwh": battery_charge_from_pv,
        "battery_charge_from_grid_kwh": battery_charge_from_grid,
        "battery_discharge_kwh": battery_discharge,
        "battery_soc_percent": battery.soc_percent,
        "grid_import_kwh": grid_import,
        "grid_export_kwh": grid_export,
        "tariff_zone": tariff_zone,
        "tariff_price_uah_per_kwh": tariff_price,
        "import_cost_uah": import_cost,
        "export_revenue_uah": export_revenue,
        "net_cost_uah": net_cost,
        "baseline_cost_without_pv_battery_uah": baseline_cost,
    }


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Simulation input was not found: {INPUT_PATH}. Run lab3_prepare_input.py first.")

    data = pd.read_csv(INPUT_PATH, parse_dates=["timestamp"])
    pv = SolarPV(capacity_kw=OBJECT["solar_capacity_kw"])
    battery = Battery(
        capacity_kwh=OBJECT["battery_capacity_kwh"],
        max_charge_kw=45.0,
        max_discharge_kw=45.0,
        initial_soc_percent=50.0,
    )
    grid = Grid(import_limit_kw=OBJECT["installed_power_kw"], export_limit_kw=OBJECT["solar_capacity_kw"])

    results = [simulate_step(row, pv, battery, grid) for _, row in data.iterrows()]
    output = pd.DataFrame(results)
    output.to_csv(OUTPUT_PATH, index=False)

    print(f"Simulation results saved: {OUTPUT_PATH}")
    print(f"Rows: {len(output)}")
    print(f"Total net cost UAH: {output['net_cost_uah'].sum():.2f}")


if __name__ == "__main__":
    main()
