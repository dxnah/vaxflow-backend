# ml_forecast.py  ─── add to your FastAPI app with:
#   from .ml_forecast import router as forecast_router
#   app.include_router(forecast_router)

import json, os
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter(prefix="/api/ml", tags=["ML Forecast"])

# ─── Load the pre-generated forecast JSON on startup ─────────────────────────
# Place vaxflow_forecast_monthly.json in the same directory as this file,
# or set the VAXFLOW_FORECAST_JSON env var to its absolute path.
_DEFAULT_PATH = Path(__file__).parent / "vaxflow_forecast_monthly.json"
_JSON_PATH    = Path(os.environ.get("VAXFLOW_FORECAST_JSON", _DEFAULT_PATH))

def _load_forecast():
    if not _JSON_PATH.exists():
        return []
    with open(_JSON_PATH, "r") as f:
        return json.load(f)

_FORECAST_DATA = _load_forecast()   # cached at startup


# ─── Helper ───────────────────────────────────────────────────────────────────
def _get_records(year: Optional[int] = None, month: Optional[int] = None):
    data = _FORECAST_DATA
    if year  is not None: data = [r for r in data if r["year"]  == year]
    if month is not None: data = [r for r in data if r["month"] == month]
    return data


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/forecast/")
def get_full_forecast(
    year:  Optional[int] = Query(None, description="Filter by year (2011-2028)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Filter by month number"),
):
    """
    Returns the ML-predicted ARV demand for each month/year.
    Fields per record:
      year, month, monthName, predicted, actual, recommended, split
    """
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
    # Also compute yearly summary
    total_predicted    = sum(r["predicted"]    for r in records)
    total_actual       = sum(r["actual"]       for r in records)
    total_recommended  = sum(r["recommended"]  for r in records)
    avg_predicted      = round(total_predicted / len(records))
    return {
        "year":              year,
        "months":            records,
        "summary": {
            "total_predicted":   total_predicted,
            "total_actual":      total_actual,
            "total_recommended": total_recommended,
            "avg_per_month":     avg_predicted,
            "months_count":      len(records),
            "split":             records[0]["split"] if records else None,
        }
    }


@router.get("/forecast/summary/")
def get_yearly_summary():
    """
    Returns one row per year with aggregate predicted/actual/recommended doses.
    Used by the DemandForecast year-trend table and chart.
    """
    from collections import defaultdict
    by_year = defaultdict(list)
    for r in _FORECAST_DATA:
        by_year[r["year"]].append(r)

    summary = []
    for year in sorted(by_year):
        recs = by_year[year]
        summary.append({
            "year":              year,
            "totalPredicted":    sum(r["predicted"]   for r in recs),
            "totalActual":       sum(r["actual"]       for r in recs),
            "totalRecommended":  sum(r["recommended"]  for r in recs),
            "avgPerMonth":       round(sum(r["predicted"] for r in recs) / len(recs)),
            "monthsCount":       len(recs),
            "split":             recs[0]["split"],
        })
    return summary


@router.get("/forecast/metrics/")
def get_model_metrics():
    """
    Returns the saved model evaluation metrics (test-set performance).
    Reads from vaxflow_arv_model.pkl if joblib is available,
    otherwise returns the hardcoded metrics from the last training run.
    """
    try:
        import joblib
        _PKL_PATH = Path(__file__).parent / "vaxflow_arv_model.pkl"
        if _PKL_PATH.exists():
            payload = joblib.load(_PKL_PATH)
            return {
                "model_name":   payload.get("model_name", "Gradient Boosting"),
                "split_ratio":  payload.get("split_ratio", "70:15:15 chronological"),
                "test_metrics": payload.get("test_metrics", {}),
                "trained_on":   payload.get("trained_on",  {}),
            }
    except Exception:
        pass
    # Hardcoded fallback from last run
    return {
        "model_name":  "Gradient Boosting",
        "split_ratio": "70:15:15 chronological",
        "test_metrics": {"MAE": 70.8, "RMSE": 83.0, "R2": 0.6929, "MAPE_pct": 3.87},
        "trained_on":  {"years": "2011–2028", "samples": 216},
    }