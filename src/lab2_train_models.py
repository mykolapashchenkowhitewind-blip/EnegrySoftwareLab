import pickle

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from config import PROJECT_ROOT


DATA_PATH = PROJECT_ROOT / "data" / "lab2" / "analysis_dataset.csv"
LAB2_DIR = PROJECT_ROOT / "data" / "lab2"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"
MODEL_PATH = PROJECT_ROOT / "models" / "lab2_best_model.pkl"
REPORT_PATH = PROJECT_ROOT / "docs" / "lab2_report.md"

TARGET = "total_consumption_kwh"
SIMPLE_FEATURES = ["temperature_c", "hour"]
MODEL_FEATURES = [
    "temperature_c",
    "irradiation_w_m2",
    "hdd_18",
    "cdd_22",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
    "is_weekend",
    "is_working_hour",
    "tariff_zone_code",
    "lag_1h",
    "lag_24h",
    "lag_168h",
    "rolling_24h_mean",
    "rolling_24h_std",
]


def mape(y_true: pd.Series, y_pred: np.ndarray) -> float:
    denominator = np.maximum(np.abs(y_true), 1e-9)
    return float(np.mean(np.abs((y_true - y_pred) / denominator)) * 100)


def metrics(y_true: pd.Series, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "r2": r2_score(y_true, y_pred),
        "rmse": mean_squared_error(y_true, y_pred) ** 0.5,
        "mae": mean_absolute_error(y_true, y_pred),
        "mape": mape(y_true, y_pred),
    }


def chronological_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_index = int(len(df) * 0.8)
    return df.iloc[:split_index].copy(), df.iloc[split_index:].copy()


def fit_models(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, object, pd.DataFrame]:
    models = {
        "Persistence_24h": None,
        "Simple_Linear_Regression": LinearRegression(),
        "Multiple_Linear_Regression": Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())]),
        "Polynomial_Regression": Pipeline(
            [
                ("poly", PolynomialFeatures(degree=2, include_bias=False)),
                ("scaler", StandardScaler()),
                ("model", LinearRegression()),
            ]
        ),
        "Random_Forest": RandomForestRegressor(n_estimators=120, random_state=51, n_jobs=-1, min_samples_leaf=2),
        "Gradient_Boosting": GradientBoostingRegressor(random_state=51, n_estimators=160, learning_rate=0.06, max_depth=3),
    }

    rows = []
    predictions = {}
    fitted = {}

    for name, model in models.items():
        if name == "Persistence_24h":
            y_pred = test["lag_24h"].to_numpy()
            fitted[name] = "lag_24h"
        elif name == "Simple_Linear_Regression":
            model.fit(train[SIMPLE_FEATURES], train[TARGET])
            y_pred = model.predict(test[SIMPLE_FEATURES])
            fitted[name] = model
        else:
            model.fit(train[MODEL_FEATURES], train[TARGET])
            y_pred = model.predict(test[MODEL_FEATURES])
            fitted[name] = model

        model_metrics = metrics(test[TARGET], y_pred)
        rows.append({"model": name, **model_metrics})
        predictions[name] = y_pred

    comparison = pd.DataFrame(rows).sort_values(["rmse", "mae"]).reset_index(drop=True)
    best_name = comparison.loc[0, "model"]
    best_model = fitted[best_name]

    pred_df = test[["measured_at", TARGET]].copy()
    pred_df["prediction_kwh"] = predictions[best_name]
    pred_df["residual_kwh"] = pred_df[TARGET] - pred_df["prediction_kwh"]
    pred_df["model"] = best_name
    return comparison, best_model, pred_df


def save_model(best_model: object, comparison: pd.DataFrame) -> None:
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": best_model,
        "best_model_name": comparison.loc[0, "model"],
        "features": MODEL_FEATURES,
        "simple_features": SIMPLE_FEATURES,
        "target": TARGET,
    }
    with MODEL_PATH.open("wb") as file:
        pickle.dump(payload, file)


def create_model_figures(pred_df: pd.DataFrame, comparison: pd.DataFrame, best_model: object, train: pd.DataFrame) -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    sample = pred_df.head(24 * 21)
    plt.figure(figsize=(12, 5))
    plt.plot(sample["measured_at"], sample[TARGET], label="actual", linewidth=1.3)
    plt.plot(sample["measured_at"], sample["prediction_kwh"], label="predicted", linewidth=1.3)
    plt.title(f"Actual vs Predicted: {comparison.loc[0, 'model']}")
    plt.xlabel("Time")
    plt.ylabel("kWh")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "11_actual_vs_predicted.png", dpi=150)
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.hist(pred_df["residual_kwh"], bins=40)
    plt.title("Residual Distribution")
    plt.xlabel("Residual, kWh")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "12_residual_distribution.png", dpi=150)
    plt.close()

    if hasattr(best_model, "feature_importances_"):
        importances = pd.DataFrame({"feature": MODEL_FEATURES, "importance": best_model.feature_importances_})
        importances = importances.sort_values("importance", ascending=False).head(12)
        plt.figure(figsize=(9, 5))
        plt.barh(importances["feature"][::-1], importances["importance"][::-1])
        plt.title("Feature Importance")
        plt.xlabel("Importance")
        plt.tight_layout()
        plt.savefig(FIGURES_DIR / "13_feature_importance.png", dpi=150)
        plt.close()
        importances.to_csv(LAB2_DIR / "feature_importance.csv", index=False)
    elif hasattr(best_model, "named_steps") and hasattr(best_model.named_steps.get("model"), "coef_"):
        coefficients = pd.DataFrame({"feature": MODEL_FEATURES, "coefficient": best_model.named_steps["model"].coef_})
        coefficients.reindex(coefficients["coefficient"].abs().sort_values(ascending=False).index).head(12).to_csv(
            LAB2_DIR / "feature_importance.csv", index=False
        )


def append_report(comparison: pd.DataFrame, pred_df: pd.DataFrame) -> None:
    best = comparison.iloc[0]
    text = f"""

## Model Comparison

```text
{comparison.round(4).to_string(index=False)}
```

Best model by RMSE: **{best['model']}**.

The best model reached:

- R2: {best['r2']:.4f}
- RMSE: {best['rmse']:.4f} kWh
- MAE: {best['mae']:.4f} kWh
- MAPE: {best['mape']:.2f} percent

Residuals were saved to `data/lab2/residuals.csv`. Actual-vs-predicted and residual plots were saved in `reports/figures/`.
"""
    with REPORT_PATH.open("a", encoding="utf-8") as file:
        file.write(text)


def main() -> None:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Prepared dataset was not found: {DATA_PATH}. Run lab2_prepare_dataset.py first.")

    df = pd.read_csv(DATA_PATH, parse_dates=["measured_at"])
    train, test = chronological_split(df)
    comparison, best_model, pred_df = fit_models(train, test)

    comparison.to_csv(LAB2_DIR / "model_comparison.csv", index=False)
    pred_df.to_csv(LAB2_DIR / "residuals.csv", index=False)
    save_model(best_model, comparison)
    create_model_figures(pred_df, comparison, best_model, train)
    append_report(comparison, pred_df)

    print(f"Model comparison saved: {LAB2_DIR / 'model_comparison.csv'}")
    print(f"Best model: {comparison.loc[0, 'model']}")
    print(f"Saved model: {MODEL_PATH}")


if __name__ == "__main__":
    main()
