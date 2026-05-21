# Lab 2 Report

**Theme:** Аналіз даних та прогнозування енергоспоживання  
**Discipline:** Програмне забезпечення енергетичного менеджменту  
**Student:** Pashchenko Mykola  
**Group:** TR-51mp  
**Variant:** 8, University

## Dataset

The dataset is built from Lab 1 SQLite data and contains 8592 hourly records after feature engineering. The original object has 14 meters, 5200 m2 area, 350 kW installed power, and a 3-zone tariff.

## Exploratory Analysis

Generated files:

- `data/lab2/descriptive_statistics.csv`
- `data/lab2/missing_values.csv`
- `data/lab2/outlier_summary.csv`
- `data/lab2/autocorrelation.csv`
- `reports/figures/*.png`

Key consumption statistics:

```text
           Unnamed: 0  count       mean        std        min       25%      50%        75%        max
total_consumption_kwh 8592.0  74.427857  20.984891  48.710800 53.230875 69.83835  94.886625 117.944900
        temperature_c 8592.0  10.279153  10.923968 -10.860000  0.400000 10.41000  20.132500  30.840000
     irradiation_w_m2 8592.0 154.249006 225.395804   0.000000  0.000000 24.32000 224.865000 879.620000
               hdd_18 8592.0   9.337853   8.967195   0.000000  0.000000  7.59000  17.600000  28.860000
               cdd_22 8592.0   0.600702   1.574547   0.000000  0.000000  0.00000   0.000000   8.840000
           kwh_per_m2 8592.0   0.014313   0.004036   0.009367  0.010237  0.01343   0.018247   0.022682
```

Outlier summary:

```text
       metric     value
           q1 53.230875
           q3 94.886625
          iqr 41.655750
outlier_count  0.000000
```

Autocorrelation:

```text
 lag_hours  autocorrelation
         1         0.894397
        24         0.715620
        48         0.458108
       168         0.972344
```

## Factor Analysis

HDD is calculated as `max(0, 18 - temperature_c)`. CDD is calculated as `max(0, temperature_c - 22)`. Correlations are visualized in `reports/figures/09_correlation_matrix.png`.

## Modeling and Forecast

Model comparison and forecast sections are appended after running `src/lab2_train_models.py` and `src/lab2_forecast.py`.


## Model Comparison

```text
                     model     r2    rmse     mae    mape
             Random_Forest 0.9691  3.8680  3.1375  4.0278
         Gradient_Boosting 0.9675  3.9621  3.2005  4.1085
     Polynomial_Regression 0.9639  4.1812  3.4401  4.5105
Multiple_Linear_Regression 0.9507  4.8815  3.8631  5.0217
           Persistence_24h 0.4351 16.5287 10.2771 13.7035
  Simple_Linear_Regression 0.0962 20.9071 16.6998 21.0000
```

Best model by RMSE: **Random_Forest**.

The best model reached:

- R2: 0.9691
- RMSE: 3.8680 kWh
- MAE: 3.1375 kWh
- MAPE: 4.03 percent

Residuals were saved to `data/lab2/residuals.csv`. Actual-vs-predicted and residual plots were saved in `reports/figures/`.


## Next-Month Forecast

Best model used for forecasting: **Random_Forest**.

- Forecast horizon: 744 hourly records.
- Expected consumption: 58435.49 kWh.
- Expected cost: 306794.25 UAH.
- Approximate 95 percent interval for total consumption: 58228.69 to 58642.29 kWh.

Forecast by tariff zone:

```text
tariff_zone  forecast_kwh  forecast_cost_uah
  half_peak      30376.14          160386.01
      night      14360.19           37910.91
       peak      13699.16          108497.33
```

## Analytical Conclusion

The University object has a clear daily and weekly pattern: working hours are generally higher than night hours, while weekend consumption is lower but still present because the object operates 24/7. Temperature-related features, lagged consumption, and rolling statistics are useful predictors because the generated load includes seasonal behavior and stable operational cycles. The best model was selected by the lowest RMSE on the chronological test set, which represents the last 20 percent of the year. The next-month forecast can be used as an operational estimate of expected energy demand and tariff-zone cost.
