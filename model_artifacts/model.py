import argparse
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ── Config ────────────────────────────────────────────────────────────────────
DEFAULT_DATA     = "monthly_doses.csv"
ARTIFACTS_DIR    = "model_artifacts"
FEATURE_COLS     = [
    "bite_count", "dog_bites", "cat_bites", "high_risk_bites", "head_bites",
    "year", "month", "month_sin", "month_cos",
    "lag1_doses", "lag2_doses", "lag3_doses", "rolling3",
]
TARGET           = "doses_needed"
TRAIN_RATIO      = 0.80
N_ESTIMATORS     = 200
MAX_DEPTH        = 10
RANDOM_STATE     = 42


def train(data_path: str):
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path).dropna(subset=FEATURE_COLS + [TARGET])
    print(f"  {len(df)} rows after dropping nulls")

    X = df[FEATURE_COLS]
    y = df[TARGET]

    # Chronological split — never shuffle time-series data
    split     = int(len(df) * TRAIN_RATIO)
    X_train   = X.iloc[:split]
    X_test    = X.iloc[split:]
    y_train   = y.iloc[:split]
    y_test    = y.iloc[split:]

    print(f"  Train: {len(X_train)} rows | Test: {len(X_test)} rows")

    # ── Train ─────────────────────────────────────────────────────────────────
    model = RandomForestRegressor(
        n_estimators = N_ESTIMATORS,
        max_depth    = MAX_DEPTH,
        random_state = RANDOM_STATE,
    )
    model.fit(X_train, y_train)

    # ── Evaluate ──────────────────────────────────────────────────────────────
    preds = model.predict(X_test)
    mae   = mean_absolute_error(y_test, preds)
    rmse  = mean_squared_error(y_test, preds) ** 0.5
    r2    = r2_score(y_test, preds)

    print(f"\nEvaluation on test set:")
    print(f"  MAE  : {mae:.2f}  doses")
    print(f"  RMSE : {rmse:.2f} doses")
    print(f"  R²   : {r2:.4f}")

    # ── Save artifacts ────────────────────────────────────────────────────────
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    model_path    = os.path.join(ARTIFACTS_DIR, "model.pkl")
    features_path = os.path.join(ARTIFACTS_DIR, "features.json")
    meta_path     = os.path.join(ARTIFACTS_DIR, "meta.json")

    joblib.dump(model, model_path)

    with open(features_path, "w") as f:
        json.dump(FEATURE_COLS, f)

    meta = {
        "model_name"  : "RandomForestRegressor",
        "mae"         : round(mae, 2),
        "rmse"        : round(rmse, 2),
        "r2"          : round(r2, 4),
        "n_estimators": N_ESTIMATORS,
        "max_depth"   : MAX_DEPTH,
        "train_size"  : len(X_train),
        "test_size"   : len(X_test),
        "features"    : FEATURE_COLS,
        "target"      : TARGET,
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nArtifacts saved to ./{ARTIFACTS_DIR}/")
    print(f"  model.pkl    — trained RandomForestRegressor")
    print(f"  features.json — feature column order")
    print(f"  meta.json    — model metadata & evaluation metrics")

    return mae, rmse, r2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train VaxFlow dose forecast model")
    parser.add_argument("--data", default=DEFAULT_DATA, help="Path to monthly_doses.csv")
    args = parser.parse_args()
    train(args.data)