# Lab 3 Report

**Theme:** EMS energy-flow control simulation  
**Discipline:** Programne zabezpechennia enerhetychnoho menedzhmentu  
**Student:** Pashchenko Mykola  
**Group:** TR-51mp  
**Variant:** 8, University

## Goal

The goal is to model and test an EMS for a University object with solar PV, battery storage, grid connection, and hourly load. The controller decides when to use PV directly, charge or discharge the battery, import energy, and export surplus energy.

## System Parameters

- Load profile: average 85 kW, range 50-130 kW.
- Solar PV capacity: 140.0 kW.
- Battery capacity: 110.0 kWh.
- Initial SOC: 50 percent.
- SOC limits: 20-90 percent.
- Simulation period: 7 days.
- Time step: 1 hour.
- Tariff: 3-zone tariff.

## Control Algorithm

For each hour, the EMS calculates PV generation and compares it with load. If PV exceeds load, the surplus charges the battery and then exports to the grid. If PV is not enough, the controller discharges the battery during peak or selected half-peak hours and imports the remaining deficit from the grid. During the night tariff zone, the battery may charge from the grid when SOC is low because electricity is cheaper.

## Energy Metrics

```text
                     metric     value
      total_consumption_kwh 12559.921
    total_pv_generation_kwh  4280.083
        pv_coverage_percent    34.077
pv_self_consumption_percent   100.000
            grid_import_kwh  8327.620
            grid_export_kwh     0.000
        battery_charged_kwh   519.051
     battery_discharged_kwh   471.269
      approx_battery_cycles     4.284
            min_soc_percent    20.000
            max_soc_percent    83.820
            avg_soc_percent    40.274
```

## Economic Metrics

```text
                              metric       value
baseline_cost_without_pv_battery_uah   65906.280
            import_cost_with_ems_uah   39023.433
                  export_revenue_uah       0.000
               net_cost_with_ems_uah   39023.433
                  weekly_savings_uah   26882.847
        projected_annual_savings_uah 1397908.024
                   assumed_capex_uah 4960000.000
                simple_payback_years       3.548
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
