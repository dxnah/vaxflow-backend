import json, os
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional

from .auth import get_current_user

router = APIRouter(
    prefix="/api/ml",
    tags=["ML Forecast"],
    dependencies=[Depends(get_current_user)],  # add this
)

router = APIRouter(prefix="/api/ml", tags=["ML Forecast"])

# ─── Load forecast JSON ───────────────────────────────────────────────────────
_DEFAULT_PATH = Path(__file__).parent / "vaxflow_forecast_monthly.json"
_JSON_PATH    = Path(os.environ.get("VAXFLOW_FORECAST_JSON", _DEFAULT_PATH))

def _load_forecast():
    if not _JSON_PATH.exists():
        return []
    with open(_JSON_PATH, "r") as f:
        return json.load(f)

_FORECAST_DATA = _load_forecast()

# ─── Load trained model ───────────────────────────────────────────────────────
_PKL_PATH      = Path(__file__).parent / "vaxflow_arv_model.pkl"
_MODEL_PAYLOAD = None

def _load_model():
    global _MODEL_PAYLOAD
    try:
        import joblib
        if _PKL_PATH.exists():
            _MODEL_PAYLOAD = joblib.load(_PKL_PATH)
    except Exception as e:
        print(f"Warning: Could not load model — {e}")

_load_model()

# ─── Load dataset ─────────────────────────────────────────────────────────────
_DATASET_PATH = Path(__file__).parent / "vaxflow_synthesized_dataset_final.xlsx"
_DATASET      = None

def _load_dataset():
    global _DATASET
    try:
        if _DATASET_PATH.exists():
            df = pd.read_excel(_DATASET_PATH)
            _DATASET = df.sort_values(['year', 'month']).reset_index(drop=True)
    except Exception as e:
        print(f"Warning: Could not load dataset — {e}")

_load_dataset()

# ─── Helper ───────────────────────────────────────────────────────────────────
def _get_records(year: Optional[int] = None, month: Optional[int] = None):
    data = _FORECAST_DATA
    if year  is not None: data = [r for r in data if r["year"]  == year]
    if month is not None: data = [r for r in data if r["month"] == month]
    return data


class MonthlyActual(BaseModel):
    year:  int = Field(..., example=2026)
    month: int = Field(..., ge=1, le=12, example=6)
    arv_doses_administered:      int   = Field(..., example=1712)
    bite_cases_total:            int   = Field(..., example=340)
    category_1_cases:            int   = Field(..., example=65)
    category_2_cases:            int   = Field(..., example=140)
    category_3_cases:            int   = Field(..., example=135)
    temperature_c:               float = Field(..., example=29.2)
    rainfall_mm:                 float = Field(..., example=145.0)
    humidity_percent:            float = Field(..., example=80.5)
    heat_index_c:                float = Field(..., example=33.1)
    pep_completion_rate:         float = Field(..., example=0.82)
    stockout_flag:               int   = Field(0, example=0)
    rig_availability_rate:       float = Field(..., example=0.93)
    procurement_delay_days:      int   = Field(0, example=0)
    dog_vaccination_campaign_flag: int = Field(0, example=0)
    extreme_weather_flag:        int   = Field(0, example=0)
    holiday_season_flag:         int   = Field(0, example=0)
    school_vacation_flag:        int   = Field(0, example=1)


def _retrain_and_reload():
    """
    Retrains the model in-process (no subprocess, no notebook needed).
    Runs automatically after /actuals/ is called.
    Called as a background task so the API response returns immediately.
    """
    global _FORECAST_DATA, _MODEL_PAYLOAD, _DATASET

    try:
        import joblib
        from sklearn.linear_model import Ridge
        from sklearn.metrics import (
            mean_absolute_error, mean_squared_error,
            r2_score, mean_absolute_percentage_error
        )

        print("🔄 Auto-retrain started...")

        # ── 1. Load updated dataset ───────────────────────────────────────────
        df = pd.read_excel(_DATASET_PATH)
        df = df.sort_values(['year', 'month']).reset_index(drop=True)

        # ── 2. Feature engineering (identical to notebook) ────────────────────
        df_fe = df.copy()

        for lag in [1, 2, 3, 6, 12]:
            df_fe[f'arv_lag_{lag}'] = df_fe['arv_doses_administered'].shift(lag)

        df_fe['arv_roll_3'] = df_fe['arv_doses_administered'].shift(1).rolling(3).mean()
        df_fe['arv_roll_6'] = df_fe['arv_doses_administered'].shift(1).rolling(6).mean()

        df_fe['month_sin'] = np.sin(2 * np.pi * df_fe['month'] / 12)
        df_fe['month_cos'] = np.cos(2 * np.pi * df_fe['month'] / 12)

        df_fe['temp_x_breeding'] = df_fe['temperature_c'] * df_fe['breeding_season_cycle']
        df_fe['stray_x_waste']   = df_fe['stray_density_index'] * (10 - df_fe['waste_management_index'])
        df_fe['bite_per_dog']    = df_fe['bite_cases_total'] / (df_fe['dog_population'] / 1000)
        df_fe['year_trend']      = df_fe['year'] - df_fe['year'].min()

        df_fe = df_fe.drop(columns=['rig_vials_used'], errors='ignore')
        df_fe = df_fe.dropna().reset_index(drop=True)

        # ── 3. Prepare X, y ───────────────────────────────────────────────────
        TARGET     = 'arv_doses_administered'
        DROP_COLS  = [TARGET, 'date'] if 'date' in df_fe.columns else [TARGET]
        feature_cols = [c for c in df_fe.columns if c not in DROP_COLS]

        X = df_fe[feature_cols]
        y = df_fe[TARGET]

        n         = len(df_fe)
        train_end = int(n * 0.70)
        val_end   = int(n * 0.85)

        X_train, y_train = X.iloc[:train_end],       y.iloc[:train_end]
        X_test,  y_test  = X.iloc[val_end:],         y.iloc[val_end:]

        # ── 4. Retrain ────────────────────────────────────────────────────────
        model = Ridge(alpha=1.0, fit_intercept=True)
        model.fit(X_train, y_train)

        y_pred_test = model.predict(X_test)
        test_metrics = {
            'R2':       round(float(r2_score(y_test, y_pred_test)), 4),
            'MAE':      round(float(mean_absolute_error(y_test, y_pred_test)), 2),
            'RMSE':     round(float(np.sqrt(mean_squared_error(y_test, y_pred_test))), 2),
            'MAPE_pct': round(float(mean_absolute_percentage_error(y_test, y_pred_test) * 100), 2),
        }

        print(f"✅ Retrain complete — R²={test_metrics['R2']}  MAE={test_metrics['MAE']}  MAPE={test_metrics['MAPE_pct']}%")

        # ── 5. Save new .pkl ──────────────────────────────────────────────────
        payload = {
            'model':        model,
            'model_name':   'Linear Regression',
            'feature_cols': feature_cols,
            'split_ratio':  '70:15:15 chronological',
            'test_metrics': test_metrics,
            'trained_on': {
                'years':   f"{int(df_fe['year'].min())}–{int(df_fe['year'].max())}",
                'samples': len(df_fe),
            }
        }
        joblib.dump(payload, _PKL_PATH)

        # ── 6. Regenerate forecast JSON ───────────────────────────────────────
        MONTH_NAMES = ['January','February','March','April','May','June',
                       'July','August','September','October','November','December']

        y_all = model.predict(X)
        records = []
        for i, (_, row) in enumerate(df_fe.iterrows()):
            pred   = max(0, round(float(y_all[i])))
            actual = int(row[TARGET])
            split  = 'train' if i < train_end else ('validation' if i < val_end else 'test')
            records.append({
                'year':        int(row['year']),
                'month':       int(row['month']),
                'monthName':   MONTH_NAMES[int(row['month']) - 1],
                'predicted':   pred,
                'actual':      actual,
                'recommended': round(pred * 1.12),
                'split':       split,
            })

        with open(_JSON_PATH, 'w') as f:
            json.dump(records, f, indent=2)

        # ── 7. Reload everything in memory ────────────────────────────────────
        _MODEL_PAYLOAD = payload
        _FORECAST_DATA = records
        _DATASET       = df.sort_values(['year','month']).reset_index(drop=True)

        print(f"✅ Model reloaded in memory. R²={test_metrics['R2']}")

    except Exception as e:
        print(f"❌ Auto-retrain failed: {e}")


@router.post("/actuals/")
def submit_monthly_actual(data: MonthlyActual, background_tasks: BackgroundTasks):
    """
    Submit actual monthly data — saves to dataset and automatically
    retrains the model in the background. No manual steps needed.
    The dashboard will show updated predictions within ~10 seconds.
    """
    global _DATASET
    if _DATASET is None:
        raise HTTPException(status_code=500, detail="Dataset not found.")

    try:
        df = pd.read_excel(_DATASET_PATH)
        df = df.sort_values(['year', 'month']).reset_index(drop=True)

        exists = df[(df['year'] == data.year) & (df['month'] == data.month)]

        if len(exists) > 0:
            for field, value in data.model_dump().items():
                if field in df.columns:
                    df.loc[
                        (df['year'] == data.year) & (df['month'] == data.month),
                        field
                    ] = value
            action = "updated"
        else:
            same_month_last = df[df['month'] == data.month]
            base = same_month_last.iloc[-1].to_dict() if len(same_month_last) > 0 else {}
            new_row = {**base, **data.model_dump()}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df = df.sort_values(['year', 'month']).reset_index(drop=True)
            action = "appended"

        df.to_excel(_DATASET_PATH, index=False)
        background_tasks.add_task(_retrain_and_reload)

        return {
            "status":  action,
            "year":    data.year,
            "month":   data.month,
            "arv_doses_administered": data.arv_doses_administered,
            "message": "Data saved. Model is retraining in the background (~10 seconds). "
                       "Refresh the dashboard after a moment to see updated predictions.",
            "retraining": True,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save data: {e}")
    
@router.post("/reload/")
def reload_model():
    """
    Reloads the model, dataset, and forecast JSON from disk.
    Call this after running the retraining notebook and copying new files.
    """
    global _FORECAST_DATA, _MODEL_PAYLOAD, _DATASET
    try:
        _FORECAST_DATA = _load_forecast()
        _load_model()
        _load_dataset()
        return {
            "status": "reloaded",
            "model_name": _MODEL_PAYLOAD.get("model_name") if _MODEL_PAYLOAD else None,
            "test_r2":    _MODEL_PAYLOAD.get("test_metrics", {}).get("R2") if _MODEL_PAYLOAD else None,
            "forecast_records": len(_FORECAST_DATA),
            "dataset_rows": len(_DATASET) if _DATASET is not None else 0,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reload failed: {e}")


@router.get("/retrain/status/")
def retrain_status():
    """
    Check current model status — call this after submitting actuals
    to confirm the retrain completed.
    """
    if _MODEL_PAYLOAD is None:
        raise HTTPException(status_code=500, detail="Model not loaded.")
    return {
        "model_name":    _MODEL_PAYLOAD.get("model_name"),
        "test_r2":       _MODEL_PAYLOAD.get("test_metrics", {}).get("R2"),
        "test_mape":     _MODEL_PAYLOAD.get("test_metrics", {}).get("MAPE_pct"),
        "test_mae":      _MODEL_PAYLOAD.get("test_metrics", {}).get("MAE"),
        "trained_on":    _MODEL_PAYLOAD.get("trained_on", {}),
        "forecast_records": len(_FORECAST_DATA),
        "dataset_rows":  len(_DATASET) if _DATASET is not None else 0,
    }

# ─── POST /predict/ — just send year and month ────────────────────────────────

@router.post("/predict/")
def predict_arv_demand(
    year:  int = Query(..., description="Year to predict (e.g. 2026)"),
    month: int = Query(..., ge=1, le=12, description="Month number (1-12)"),
):
    """
    Predict ARV dose demand for any month and year.
    Just send year and month as query parameters — all other features are
    looked up automatically from the training dataset.
    """
    if _MODEL_PAYLOAD is None:
        raise HTTPException(status_code=500, detail="Model not loaded. Run the notebook first.")
    if _DATASET is None:
        raise HTTPException(status_code=500, detail="Dataset not found. Place vaxflow_synthesized_dataset_final.xlsx in the fast_api folder.")

    model        = _MODEL_PAYLOAD["model"]
    feature_cols = _MODEL_PAYLOAD["feature_cols"]
    df           = _DATASET.copy()

    match = df[(df['year'] == year) & (df['month'] == month)]
    if match.empty:
        same_month = df[df['month'] == month]
        if same_month.empty:
            raise HTTPException(status_code=404, detail=f"No data available for month {month}.")
        base_row = same_month.iloc[-1].copy()
        base_row['year'] = year
    else:
        base_row = match.iloc[0].copy()

    df_sorted  = df.sort_values(['year', 'month']).reset_index(drop=True)
    target_idx = df_sorted[(df_sorted['year'] == base_row['year']) &
                           (df_sorted['month'] == month)].index

    def get_lag(lag):
        if len(target_idx) > 0:
            idx = target_idx[0]
            if idx - lag >= 0:
                return float(df_sorted.iloc[idx - lag]['arv_doses_administered'])
        return float(df[df['month'] == month]['arv_doses_administered'].mean())

    arv_lag_1  = get_lag(1)
    arv_lag_2  = get_lag(2)
    arv_lag_3  = get_lag(3)
    arv_lag_6  = get_lag(6)
    arv_lag_12 = get_lag(12)
    arv_roll_3 = float(np.mean([get_lag(1), get_lag(2), get_lag(3)]))
    arv_roll_6 = float(np.mean([get_lag(1), get_lag(2), get_lag(3),
                                 get_lag(4), get_lag(5), get_lag(6)]))

    month_sin       = np.sin(2 * np.pi * month / 12)
    month_cos       = np.cos(2 * np.pi * month / 12)
    temp_x_breeding = float(base_row['temperature_c']) * float(base_row['breeding_season_cycle'])
    stray_x_waste   = float(base_row['stray_density_index']) * (10 - float(base_row['waste_management_index']))
    bite_per_dog    = float(base_row['bite_cases_total']) / (float(base_row['dog_population']) / 1000)
    year_trend      = year - int(df['year'].min())

    feature_dict = {
        "year": year, "month": month,
        "temperature_c":                 float(base_row['temperature_c']),
        "rainfall_mm":                   float(base_row['rainfall_mm']),
        "humidity_percent":              float(base_row['humidity_percent']),
        "heat_index_c":                  float(base_row['heat_index_c']),
        "dog_population":                float(base_row['dog_population']),
        "dog_population_growth_rate":    float(base_row['dog_population_growth_rate']),
        "urban_density":                 float(base_row['urban_density']),
        "vaccination_coverage_rate":     float(base_row['vaccination_coverage_rate']),
        "bite_cases_total":              float(base_row['bite_cases_total']),
        "category_1_cases":              float(base_row['category_1_cases']),
        "category_2_cases":              float(base_row['category_2_cases']),
        "category_3_cases":              float(base_row['category_3_cases']),
        "pep_completion_rate":           float(base_row['pep_completion_rate']),
        "breeding_season_cycle":         float(base_row['breeding_season_cycle']),
        "waste_management_index":        float(base_row['waste_management_index']),
        "rabies_confirmation_rate":      float(base_row['rabies_confirmation_rate']),
        "stockout_flag":                 float(base_row['stockout_flag']),
        "rig_availability_rate":         float(base_row['rig_availability_rate']),
        "cold_chain_capacity_index":     float(base_row['cold_chain_capacity_index']),
        "procurement_delay_days":        float(base_row['procurement_delay_days']),
        "dog_vaccination_campaign_flag": float(base_row['dog_vaccination_campaign_flag']),
        "public_awareness_score":        float(base_row['public_awareness_score']),
        "travel_accessibility_index":    float(base_row['travel_accessibility_index']),
        "poverty_index":                 float(base_row['poverty_index']),
        "stray_density_index":           float(base_row['stray_density_index']),
        "extreme_weather_flag":          float(base_row['extreme_weather_flag']),
        "holiday_season_flag":           float(base_row['holiday_season_flag']),
        "school_vacation_flag":          float(base_row['school_vacation_flag']),
        "arv_lag_1": arv_lag_1, "arv_lag_2": arv_lag_2, "arv_lag_3": arv_lag_3,
        "arv_lag_6": arv_lag_6, "arv_lag_12": arv_lag_12,
        "arv_roll_3": arv_roll_3, "arv_roll_6": arv_roll_6,
        "month_sin": month_sin, "month_cos": month_cos,
        "temp_x_breeding": temp_x_breeding, "stray_x_waste": stray_x_waste,
        "bite_per_dog": bite_per_dog, "year_trend": year_trend,
    }

    try:
        input_values = [feature_dict[col] for col in feature_cols]
    except KeyError as e:
        raise HTTPException(status_code=422, detail=f"Missing feature: {e}")

    X_input           = pd.DataFrame([input_values], columns=feature_cols)
    predicted_raw     = float(model.predict(X_input)[0])
    predicted_doses   = max(0, round(predicted_raw))
    recommended_order = round(predicted_doses * 1.12)

    MONTH_NAMES = ['January','February','March','April','May','June',
                   'July','August','September','October','November','December']

    return {
        "input": {"year": year, "month": month, "monthName": MONTH_NAMES[month - 1]},
        "prediction": {
            "predicted_doses":   predicted_doses,
            "recommended_order": recommended_order,
            "safety_buffer_pct": 12,
            "unit":              "ARV doses",
        },
        "model_info": {
            "model_name": _MODEL_PAYLOAD.get("model_name"),
            "test_r2":    _MODEL_PAYLOAD.get("test_metrics", {}).get("R2"),
            "test_mape":  _MODEL_PAYLOAD.get("test_metrics", {}).get("MAPE_pct"),
        }
    }

# ─── GET Endpoints ────────────────────────────────────────────────────────────

@router.get("/forecast/")
def get_full_forecast(
    year:  Optional[int] = Query(None, description="Filter by year (2011-2028)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month number"),
):
    """Returns the ML-predicted ARV demand for each month/year."""
    records = _get_records(year, month)
    if not records:
        raise HTTPException(status_code=404, detail="No forecast data for the requested period.")
    return records


@router.get("/forecast/years/")
def get_available_years():
    """Returns the list of years present in the forecast dataset."""
    years = sorted(set(r["year"] for r in _FORECAST_DATA))
    return {"years": years, "count": len(years)}


@router.get("/forecast/year/{year}/")
def get_forecast_by_year(year: int):
    """Returns all 12 monthly predictions for a specific year."""
    records = _get_records(year=year)
    if not records:
        raise HTTPException(status_code=404, detail=f"No forecast data for year {year}.")
    total_predicted   = sum(r["predicted"]   for r in records)
    total_actual      = sum(r["actual"]      for r in records)
    total_recommended = sum(r["recommended"] for r in records)
    return {
        "year":    year,
        "months":  records,
        "summary": {
            "total_predicted":   total_predicted,
            "total_actual":      total_actual,
            "total_recommended": total_recommended,
            "avg_per_month":     round(total_predicted / len(records)),
            "months_count":      len(records),
            "split":             records[0]["split"] if records else None,
        }
    }


@router.get("/forecast/summary/")
def get_yearly_summary():
    """Returns one row per year with aggregate predicted/actual/recommended doses."""
    from collections import defaultdict
    by_year = defaultdict(list)
    for r in _FORECAST_DATA:
        by_year[r["year"]].append(r)
    summary = []
    for year in sorted(by_year):
        recs = by_year[year]
        summary.append({
            "year":             year,
            "totalPredicted":   sum(r["predicted"]   for r in recs),
            "totalActual":      sum(r["actual"]       for r in recs),
            "totalRecommended": sum(r["recommended"]  for r in recs),
            "avgPerMonth":      round(sum(r["predicted"] for r in recs) / len(recs)),
            "monthsCount":      len(recs),
            "split":            recs[0]["split"],
        })
    return summary


@router.get("/forecast/metrics/")
def get_model_metrics():
    """Returns the saved model evaluation metrics (test-set performance)."""
    if _MODEL_PAYLOAD is None:
        raise HTTPException(status_code=500, detail="Model file not found. Run the notebook first.")
    return {
        "model_name":   _MODEL_PAYLOAD.get("model_name", "Unknown"),
        "split_ratio":  _MODEL_PAYLOAD.get("split_ratio", "70:15:15 chronological"),
        "test_metrics": _MODEL_PAYLOAD.get("test_metrics", {}),
        "trained_on":   _MODEL_PAYLOAD.get("trained_on", {}),
    }