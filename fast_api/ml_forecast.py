import json, os
import numpy as np
import pandas as pd
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

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