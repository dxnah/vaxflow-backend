import os
import json
import joblib
import numpy as np
import pandas as pd

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "model_artifacts")

SAFETY_BUFFER = 0.15


class DoseForecastModel:
    """Wraps the trained RandomForestRegressor for monthly dose prediction."""

    def __init__(self):
        self.model = joblib.load(os.path.join(ARTIFACTS_DIR, "model.pkl"))
        with open(os.path.join(ARTIFACTS_DIR, "features.json")) as f:
            self.feature_cols = json.load(f)
        with open(os.path.join(ARTIFACTS_DIR, "meta.json")) as f:
            self.meta = json.load(f)

    def predict(self, data) -> dict:
        month_sin = np.sin(2 * np.pi * data.month / 12)
        month_cos = np.cos(2 * np.pi * data.month / 12)

        # Auto-estimate lag features from bite count
        # (~3.2 doses per bite based on training data average)
        DOSES_PER_BITE = 3.2
        estimated_doses = data.bite_count * DOSES_PER_BITE
        lag1    = estimated_doses
        lag2    = estimated_doses * 0.95
        lag3    = estimated_doses * 0.90
        rolling3 = (lag1 + lag2 + lag3) / 3

        row = {
            "bite_count":      data.bite_count,
            "dog_bites":       data.dog_bites,
            "cat_bites":       data.cat_bites,
            "high_risk_bites": data.high_risk_bites,
            "head_bites":      data.head_bites,
            "year":            data.year,
            "month":           data.month,
            "month_sin":       month_sin,
            "month_cos":       month_cos,
            "lag1_doses":      lag1,
            "lag2_doses":      lag2,
            "lag3_doses":      lag3,
            "rolling3":        rolling3,
        }

        X         = pd.DataFrame([row], columns=self.feature_cols)
        predicted = float(self.model.predict(X)[0])
        predicted = max(0.0, round(predicted, 1))

        mae   = self.meta.get("mae", 15.0)
        lower = max(0.0, round(predicted - mae, 1))
        upper = round(predicted * (1 + SAFETY_BUFFER), 1)

        head_ratio = data.head_bites / max(data.bite_count, 1)

        if data.high_risk_bites >= 5 or head_ratio > 0.15:
            risk_level = "HIGH"
            recommendation = (
                f"Order at least {int(upper)} doses this month. "
                "Elevated Category III or high head-bite ratio detected. "
                "Ensure ERIG/RIG stock is also replenished."
            )
        elif predicted > 350:
            risk_level = "MODERATE-HIGH"
            recommendation = (
                f"Order {int(upper)} doses. Peak-season demand expected. "
                "Consider pre-ordering next month's supply early."
            )
        elif predicted > 250:
            risk_level = "MODERATE"
            recommendation = (
                f"Order {int(upper)} doses (includes {int(SAFETY_BUFFER * 100)}% safety buffer). "
                "Demand is within normal seasonal range."
            )
        else:
            risk_level = "LOW"
            recommendation = (
                f"Order approximately {int(upper)} doses. "
                "Low-demand period — verify existing stock before requisition."
            )

        return {
             "predicted_doses": predicted,
             "minimum_stock":   lower,
             "recommended_order": upper,
             "risk_level":      risk_level,
             "recommendation":  recommendation,
            }


# Single shared instance — loaded once at startup
ml_model = DoseForecastModel()