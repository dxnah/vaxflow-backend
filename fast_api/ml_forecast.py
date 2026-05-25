import json, os
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from .auth import require_admin

# ─── Router ───────────────────────────────────────────────────────────────────
router = APIRouter(prefix="/api/ml", tags=["ML Forecast"])

# ─── Paths ────────────────────────────────────────────────────────────────────
_DEFAULT_PATH = Path(__file__).parent / "vaxflow_forecast_monthly.json"
_JSON_PATH    = Path(os.environ.get("VAXFLOW_FORECAST_JSON", _DEFAULT_PATH))
_PKL_PATH     = Path(__file__).parent / "vaxflow_arv_model.pkl"
_DATASET_PATH = Path(__file__).parent / "vaxflow_synthesized_dataset_final.xlsx"

# ─── In-memory state ──────────────────────────────────────────────────────────
_FORECAST_DATA = []
_MODEL_PAYLOAD = None
_DATASET       = None


# ─── Loaders ──────────────────────────────────────────────────────────────────
def _load_forecast():
    global _FORECAST_DATA
    if _JSON_PATH.exists():
        with open(_JSON_PATH, "r") as f:
            _FORECAST_DATA = json.load(f)
    return _FORECAST_DATA


def _load_model():
    global _MODEL_PAYLOAD
    try:
        import joblib
        if _PKL_PATH.exists():
            _MODEL_PAYLOAD = joblib.load(_PKL_PATH)
            r2 = (_MODEL_PAYLOAD.get("test_metrics") or {}).get("R2", None)
            print(f"✅ Model loaded — {_MODEL_PAYLOAD.get('model_name')}  R²={r2}")
    except Exception as e:
        print(f"Warning: Could not load model — {e}")


def _load_dataset():
    global _DATASET
    try:
        if _DATASET_PATH.exists():
            df = pd.read_excel(_DATASET_PATH)
            _DATASET = df.sort_values(["year", "month"]).reset_index(drop=True)
    except Exception as e:
        print(f"Warning: Could not load dataset — {e}")


# ─── Feature engineering ──────────────────────────────────────────────────────
def _build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Mirrors the training pipeline in vaxflow_ml.ipynb exactly.
    Produces the same 37 features the pkl was trained on:
      lags 1/2/3/6/12 · rolling 3/6 (shift-then-roll) · month sin/cos
      temp×breeding · stray×waste · bite_per_dog · stockout_lag_1 · year_trend
    Drops: arv_doses_administered, rig_vials_used, date, bite_cases_total,
           category_1/2/3_cases, pep_completion_rate
    """
    df = df.copy().sort_values(["year", "month"]).reset_index(drop=True)

    # Lag features
    for lag in [1, 2, 3, 6, 12]:
        df[f"arv_lag_{lag}"] = df["arv_doses_administered"].shift(lag)

    # Rolling averages — shift first to prevent leakage
    df["arv_roll_3"] = df["arv_doses_administered"].shift(1).rolling(window=3).mean()
    df["arv_roll_6"] = df["arv_doses_administered"].shift(1).rolling(window=6).mean()

    # Cyclical month encoding
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)

    # Interaction features
    df["temp_x_breeding"] = df["temperature_c"] * df["breeding_season_cycle"]
    df["stray_x_waste"]   = df["stray_density_index"] * (10 - df["waste_management_index"])
    df["bite_per_dog"]    = df["bite_cases_total"] / (df["dog_population"] / 1000)

    # Lagged stockout flag
    df["stockout_lag_1"] = df["stockout_flag"].shift(1).fillna(0)

    # Year trend (distance from first year in dataset)
    df["year_trend"] = df["year"] - int(df["year"].min())

    # Drop leakage columns and rows with NaN from lag warm-up
    df = df.drop(columns=[
        "arv_doses_administered",
        "rig_vials_used",
        "bite_cases_total",
        "category_1_cases",
        "category_2_cases",
        "category_3_cases",
        "pep_completion_rate",
        "date",
    ], errors="ignore")
    df = df.dropna().reset_index(drop=True)

    return df


# ─── Background retrain ───────────────────────────────────────────────────────
def _do_retrain() -> dict:
    """
    Retrains Ridge (α=1.0) on the current dataset.
    Feature engineering is identical to vaxflow_ml.ipynb.
    Overwrites pkl + forecast JSON, hot-reloads memory.
    Returns test_metrics dict. Raises on failure.
    """
    import joblib
    from sklearn.linear_model import Ridge
    from sklearn.metrics import (
        mean_absolute_error, mean_squared_error,
        r2_score, mean_absolute_percentage_error,
    )

    # 1. Load fresh dataset
    df_raw = pd.read_excel(_DATASET_PATH)
    df_raw = df_raw.sort_values(["year", "month"]).reset_index(drop=True)

    # 2. Build feature matrix — same pipeline as notebook
    df_fe = _build_features(df_raw)
    if len(df_fe) < 30:
        raise ValueError(f"Too few rows after feature engineering: {len(df_fe)}")

    # 3. X / y split — feature_cols must exactly match the 37-column pkl
    TARGET = "arv_doses_administered"
    # _build_features already dropped TARGET and all leakage columns,
    # and also dropped year/month from the feature set via the drop list.
    # Remaining columns are the model features.
    DROP_FROM_X = ["year", "month"]
    feature_cols = [c for c in df_fe.columns if c not in DROP_FROM_X]

    X = df_fe[feature_cols]
    y = df_raw.iloc[df_raw.index.isin(
        df_raw.sort_values(["year","month"]).reset_index(drop=True).index
    )]["arv_doses_administered"]

    # Re-align y to the rows that survived dropna in _build_features
    # by re-reading arv_doses_administered from the raw df in the same order
    df_raw_sorted  = df_raw.sort_values(["year","month"]).reset_index(drop=True)
    df_fe_internal = df_raw_sorted.copy()
    for lag in [1, 2, 3, 6, 12]:
        df_fe_internal[f"arv_lag_{lag}"] = df_fe_internal["arv_doses_administered"].shift(lag)
    df_fe_internal["arv_roll_3"]    = df_fe_internal["arv_doses_administered"].shift(1).rolling(3).mean()
    df_fe_internal["arv_roll_6"]    = df_fe_internal["arv_doses_administered"].shift(1).rolling(6).mean()
    df_fe_internal["stockout_lag_1"] = df_fe_internal["stockout_flag"].shift(1).fillna(0)
    df_fe_internal = df_fe_internal.dropna().reset_index(drop=True)
    y = df_fe_internal["arv_doses_administered"]

    n         = len(df_fe)
    train_end = int(n * 0.70)
    val_end   = train_end + int(n * 0.15)

    X_train, y_train = X.iloc[:train_end],  y.iloc[:train_end]
    X_test,  y_test  = X.iloc[val_end:],    y.iloc[val_end:]

    # 4. Train
    model = Ridge(alpha=1.0, fit_intercept=True)
    model.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = model.predict(X_test)
    test_metrics = {
        "R2":       round(float(r2_score(y_test, y_pred)), 4),
        "MAE":      round(float(mean_absolute_error(y_test, y_pred)), 2),
        "RMSE":     round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 2),
        "MAPE_pct": round(float(mean_absolute_percentage_error(y_test, y_pred) * 100), 2),
    }

    if test_metrics["R2"] < 0:
        raise ValueError(
            f"Retrain produced negative R²={test_metrics['R2']}. "
            "Dataset may be too small or features misaligned."
        )

    print(
        f"✅ Retrain — R²={test_metrics['R2']}  "
        f"MAE={test_metrics['MAE']}  MAPE={test_metrics['MAPE_pct']}%  "
        f"rows={n}  features={len(feature_cols)}"
    )

    # 6. Save pkl
    payload = {
        "model":        model,
        "model_name":   "Linear Regression",
        "feature_cols": feature_cols,
        "split_ratio":  "70:15:15 chronological",
        "test_metrics": test_metrics,
        "trained_on": {
            "years":   f"{int(df_fe_internal['year'].min())}–{int(df_fe_internal['year'].max())}",
            "samples": n,
        },
    }
    joblib.dump(payload, _PKL_PATH)

    # 7. Regenerate forecast JSON
    MONTH_NAMES = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December",
    ]
    y_all   = model.predict(X)
    records = []
    for i in range(len(df_fe)):
        pred   = max(0, round(float(y_all[i])))
        actual = int(y.iloc[i])
        split  = "train" if i < train_end else ("validation" if i < val_end else "test")
        records.append({
            "year":        int(df_fe_internal.iloc[i]["year"]),
            "month":       int(df_fe_internal.iloc[i]["month"]),
            "monthName":   MONTH_NAMES[int(df_fe_internal.iloc[i]["month"]) - 1],
            "predicted":   pred,
            "actual":      actual,
            "recommended": round(pred * 1.12),
            "split":       split,
        })

    with open(_JSON_PATH, "w") as f:
        json.dump(records, f, indent=2)

    # 8. Hot-reload in memory
    global _FORECAST_DATA, _MODEL_PAYLOAD, _DATASET
    _MODEL_PAYLOAD = payload
    _FORECAST_DATA = records
    _DATASET       = df_raw.sort_values(["year", "month"]).reset_index(drop=True)

    return test_metrics


def _retrain_and_reload():
    """Background-task wrapper with full traceback logging."""
    print("🔄 Auto-retrain started...")
    try:
        metrics = _do_retrain()
        print(f"✅ Model reloaded in memory. R²={metrics['R2']}")
    except Exception as e:
        import traceback
        print(f"❌ Auto-retrain failed: {e}")
        traceback.print_exc()


# ─── Startup load ─────────────────────────────────────────────────────────────
def _startup_load():
    _load_dataset()
    _load_model()
    _load_forecast()

    r2 = (_MODEL_PAYLOAD or {}).get("test_metrics", {}).get("R2", None)
    if r2 is None or r2 < 0:
        reason = "missing" if r2 is None else f"negative R²={r2}"
        print(f"⚠️  Startup retrain — pkl {reason}. Retraining now...")
        try:
            _do_retrain()
        except Exception as e:
            print(f"❌ Startup retrain failed: {e}")
    else:
        print(f"✅ Startup — using existing pkl  R²={r2}")


_startup_load()


# ─── Helpers ──────────────────────────────────────────────────────────────────
def _get_records(year: Optional[int] = None, month: Optional[int] = None):
    data = _FORECAST_DATA
    if year  is not None: data = [r for r in data if r["year"]  == year]
    if month is not None: data = [r for r in data if r["month"] == month]
    return data


# ─── Pydantic schema ──────────────────────────────────────────────────────────
class MonthlyActual(BaseModel):
    year:  int   = Field(..., example=2026)
    month: int   = Field(..., ge=1, le=12, example=6)
    arv_doses_administered:        int   = Field(..., example=1712)
    bite_cases_total:              int   = Field(..., example=340)
    category_1_cases:              int   = Field(..., example=65)
    category_2_cases:              int   = Field(..., example=140)
    category_3_cases:              int   = Field(..., example=135)
    temperature_c:                 float = Field(..., example=29.2)
    rainfall_mm:                   float = Field(..., example=145.0)
    humidity_percent:              float = Field(..., example=80.5)
    heat_index_c:                  float = Field(..., example=33.1)
    pep_completion_rate:           float = Field(..., example=0.82)
    stockout_flag:                 int   = Field(0,   example=0)
    rig_availability_rate:         float = Field(..., example=0.93)
    procurement_delay_days:        int   = Field(0,   example=0)
    dog_vaccination_campaign_flag: int   = Field(0,   example=0)
    extreme_weather_flag:          int   = Field(0,   example=0)
    holiday_season_flag:           int   = Field(0,   example=0)
    school_vacation_flag:          int   = Field(0,   example=1)


# ─── POST /actuals/ ───────────────────────────────────────────────────────────
@router.post("/actuals/")
def submit_monthly_actual(
    data: MonthlyActual,
    background_tasks: BackgroundTasks,
    _admin: dict = Depends(require_admin),
):
    """Save actual monthly data then retrain the model in the background."""
    global _DATASET
    if _DATASET is None:
        raise HTTPException(status_code=500, detail="Dataset not loaded.")

    try:
        df   = pd.read_excel(_DATASET_PATH)
        df   = df.sort_values(["year", "month"]).reset_index(drop=True)
        mask = (df["year"] == data.year) & (df["month"] == data.month)

        if df[mask].shape[0] > 0:
            for field, value in data.model_dump().items():
                if field in df.columns:
                    df.loc[mask, field] = value
            action = "updated"
        else:
            same_month = df[df["month"] == data.month]
            base       = same_month.iloc[-1].to_dict() if len(same_month) > 0 else {}
            new_row    = {**base, **data.model_dump()}
            df         = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df         = df.sort_values(["year", "month"]).reset_index(drop=True)
            action     = "appended"

        df.to_excel(_DATASET_PATH, index=False)
        background_tasks.add_task(_retrain_and_reload)

        return {
            "status":                 action,
            "year":                   data.year,
            "month":                  data.month,
            "arv_doses_administered": data.arv_doses_administered,
            "message": (
                "Data saved. Model is retraining in the background (~10 seconds). "
                "Poll GET /api/ml/retrain/status/ to see updated metrics."
            ),
            "retraining": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save data: {e}")


# ─── POST /reload/ ────────────────────────────────────────────────────────────
@router.post("/reload/")
def reload_model(_admin: dict = Depends(require_admin)):
    """Force-reload pkl, dataset, and JSON from disk without retraining."""
    try:
        _load_forecast()
        _load_model()
        _load_dataset()
        return {
            "status":           "reloaded",
            "model_name":       (_MODEL_PAYLOAD or {}).get("model_name"),
            "test_r2":          (_MODEL_PAYLOAD or {}).get("test_metrics", {}).get("R2"),
            "forecast_records": len(_FORECAST_DATA),
            "dataset_rows":     len(_DATASET) if _DATASET is not None else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload failed: {e}")


# ─── POST /retrain/ ───────────────────────────────────────────────────────────
@router.post("/retrain/")
def trigger_retrain(
    background_tasks: BackgroundTasks,
    _admin: dict = Depends(require_admin),
):
    """Manually trigger a full retrain (admin only). Returns immediately."""
    background_tasks.add_task(_retrain_and_reload)
    return {
        "status":  "retrain_started",
        "message": "Poll GET /api/ml/retrain/status/ in ~15 seconds.",
    }


# ─── GET /retrain/status/ ─────────────────────────────────────────────────────
@router.get("/retrain/status/")
def retrain_status():
    """Returns current in-memory model metrics. Poll after submitting actuals."""
    if _MODEL_PAYLOAD is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")
    return {
        "model_name":       _MODEL_PAYLOAD.get("model_name"),
        "test_r2":          _MODEL_PAYLOAD.get("test_metrics", {}).get("R2"),
        "test_mape":        _MODEL_PAYLOAD.get("test_metrics", {}).get("MAPE_pct"),
        "test_mae":         _MODEL_PAYLOAD.get("test_metrics", {}).get("MAE"),
        "trained_on":       _MODEL_PAYLOAD.get("trained_on", {}),
        "forecast_records": len(_FORECAST_DATA),
        "dataset_rows":     len(_DATASET) if _DATASET is not None else 0,
    }


# ─── POST /predict/ ───────────────────────────────────────────────────────────
@router.post("/predict/")
def predict_arv_demand(
    year:  int = Query(..., description="Year to predict"),
    month: int = Query(..., ge=1, le=12, description="Month 1-12"),
):
    """Predict ARV demand for any year/month using the current deployed model."""
    if _MODEL_PAYLOAD is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")
    if _DATASET is None:
        raise HTTPException(status_code=500, detail="Dataset not loaded.")

    model        = _MODEL_PAYLOAD["model"]
    feature_cols = _MODEL_PAYLOAD["feature_cols"]

    # Build features for the full dataset so lag values are accurate
    df_fe = _build_features(_DATASET.copy())

    # Find the row matching the requested year/month
    match = df_fe[(df_fe["year"] == year) & (df_fe["month"] == month)] \
        if "year" in df_fe.columns else pd.DataFrame()

    if match.empty:
        # Fall back to the most recent row for the same month
        same_month = df_fe[df_fe["month"] == month] if "month" in df_fe.columns else pd.DataFrame()
        if same_month.empty:
            raise HTTPException(status_code=404, detail=f"No data available for month {month}.")
        base_row = same_month.iloc[-1].copy()
        # Patch the year-dependent features
        base_row["year"]        = year
        base_row["year_trend"]  = year - int(df_fe["year"].min()) if "year" in df_fe.columns else 0
        base_row["month_sin"]   = np.sin(2 * np.pi * month / 12)
        base_row["month_cos"]   = np.cos(2 * np.pi * month / 12)
    else:
        base_row = match.iloc[0].copy()

    # Build input vector in the exact column order the model expects
    try:
        input_values = [float(base_row[col]) for col in feature_cols]
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Missing feature: {e}")

    X_input         = pd.DataFrame([input_values], columns=feature_cols)
    predicted_raw   = float(model.predict(X_input)[0])
    predicted_doses = max(0, round(predicted_raw))
    recommended     = round(predicted_doses * 1.12)

    MONTH_NAMES = [
        "January","February","March","April","May","June",
        "July","August","September","October","November","December",
    ]

    return {
        "input": {
            "year":      year,
            "month":     month,
            "monthName": MONTH_NAMES[month - 1],
        },
        "prediction": {
            "predicted_doses":   predicted_doses,
            "recommended_order": recommended,
            "safety_buffer_pct": 12,
            "unit":              "ARV doses",
        },
        "model_info": {
            "model_name": _MODEL_PAYLOAD.get("model_name"),
            "test_r2":    _MODEL_PAYLOAD.get("test_metrics", {}).get("R2"),
            "test_mape":  _MODEL_PAYLOAD.get("test_metrics", {}).get("MAPE_pct"),
            "test_mae":   _MODEL_PAYLOAD.get("test_metrics", {}).get("MAE"),
        },
    }


# ─── GET /forecast/ ───────────────────────────────────────────────────────────
@router.get("/forecast/")
def get_full_forecast(
    year:  Optional[int] = Query(None),
    month: Optional[int] = Query(None, ge=1, le=12),
):
    records = _get_records(year, month)
    if not records:
        raise HTTPException(status_code=404, detail="No forecast data found.")
    return records


@router.get("/forecast/years/")
def get_available_years():
    years = sorted(set(r["year"] for r in _FORECAST_DATA))
    return {"years": years, "count": len(years)}


@router.get("/forecast/year/{year}/")
def get_forecast_by_year(year: int):
    records = _get_records(year=year)
    if not records:
        raise HTTPException(status_code=404, detail=f"No forecast data for {year}.")
    tp = sum(r["predicted"]   for r in records)
    ta = sum(r["actual"]      for r in records)
    tr = sum(r["recommended"] for r in records)
    return {
        "year":    year,
        "months":  records,
        "summary": {
            "total_predicted":   tp,
            "total_actual":      ta,
            "total_recommended": tr,
            "avg_per_month":     round(tp / len(records)),
            "months_count":      len(records),
            "split":             records[0]["split"] if records else None,
        },
    }


@router.get("/forecast/summary/")
def get_yearly_summary():
    from collections import defaultdict
    by_year = defaultdict(list)
    for r in _FORECAST_DATA:
        by_year[r["year"]].append(r)
    return [
        {
            "year":             yr,
            "totalPredicted":   sum(r["predicted"]   for r in recs),
            "totalActual":      sum(r["actual"]       for r in recs),
            "totalRecommended": sum(r["recommended"]  for r in recs),
            "avgPerMonth":      round(sum(r["predicted"] for r in recs) / len(recs)),
            "monthsCount":      len(recs),
            "split":            recs[0]["split"],
        }
        for yr, recs in sorted(by_year.items())
    ]


@router.get("/forecast/metrics/")
def get_model_metrics():
    if _MODEL_PAYLOAD is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")
    return {
        "model_name":   _MODEL_PAYLOAD.get("model_name", "Unknown"),
        "split_ratio":  _MODEL_PAYLOAD.get("split_ratio", "70:15:15 chronological"),
        "test_metrics": _MODEL_PAYLOAD.get("test_metrics", {}),
        "trained_on":   _MODEL_PAYLOAD.get("trained_on", {}),
    }