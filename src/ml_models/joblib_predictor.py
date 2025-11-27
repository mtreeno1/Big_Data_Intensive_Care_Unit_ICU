"""
Joblib-based ML model predictor for ICU risk scoring
- Loads a scikit-learn model from joblib
- Prepares features from streaming vital signs
- Outputs risk_score [0,1] and risk_level
"""
from __future__ import annotations
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import numpy as np

from config.config import settings

logger = logging.getLogger(__name__)

try:
    # scikit-learn vendors joblib; prefer external joblib if available
    import joblib  # type: ignore
except Exception:  # pragma: no cover
    joblib = None  # type: ignore


RISK_THRESHOLDS = {
    "CRITICAL": 0.8,
    "HIGH": 0.6,
    "MEDIUM": 0.3,
}


def to_risk_level(score: float) -> str:
    if score >= RISK_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    if score >= RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    if score >= RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "LOW"


class RiskModelPredictor:
    """Wrapper around a joblib-trained model for risk prediction."""

    def __init__(self, model_path: Optional[Path] = None):
        model_path = Path(model_path or settings.MODEL_PATH)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found at {model_path}")
        if joblib is None:
            raise ImportError("joblib is required to load the trained model")

        self.model = joblib.load(str(model_path))
        self.feature_names: Optional[List[str]] = None

        # Try to infer expected feature names from the model/pipeline
        for attr in ("feature_names_in_", "n_features_in_"):
            if hasattr(self.model, attr):
                try:
                    names = getattr(self.model, "feature_names_in_", None)
                    if names is not None:
                        self.feature_names = [str(n) for n in names]
                except Exception:
                    pass
                break

        # Fallback default feature order similar to dataset columns
        self.default_feature_order = [
            "heart_rate",
            "spo2",
            "systolic_bp",
            "diastolic_bp",
            "temperature",
            # Optional extras if model expects them; will be filled if present
            "respiratory_rate",
        ]
        logger.info(f"✅ Loaded ML risk model from {model_path}")
        if self.feature_names:
            logger.info(f"📥 Model expects features: {self.feature_names}")
        else:
            logger.info(f"📥 Using default feature order: {self.default_feature_order}")

    def _extract_base_features(self, reading: Dict[str, Any]) -> Dict[str, float]:
        vitals = reading.get("vital_signs", {})
        bp = vitals.get("blood_pressure", {}) or {}
        # Support both dict and "120/80" form (handled elsewhere too)
        if isinstance(bp, str) and "/" in bp:
            try:
                s, d = bp.split("/")
                systolic = float(s)
                diastolic = float(d)
            except Exception:
                systolic = float("nan")
                diastolic = float("nan")
        else:
            systolic = bp.get("systolic")
            diastolic = bp.get("diastolic")

        base = {
            "heart_rate": float(vitals.get("heart_rate", np.nan)),
            "spo2": float(vitals.get("spo2", np.nan)),
            "temperature": float(vitals.get("temperature", np.nan)),
            "respiratory_rate": float(vitals.get("respiratory_rate", np.nan)),
            "systolic_bp": float(systolic) if systolic is not None else np.nan,
            "diastolic_bp": float(diastolic) if diastolic is not None else np.nan,
        }
        return base

    def _vectorize(self, features: Dict[str, float]) -> np.ndarray:
        # If the model exposes feature names, align to them; otherwise use default order
        order = self.feature_names or self.default_feature_order

        # Map possible dataset column names to our normalized feature keys
        synonyms = {
            "Heart Rate (bpm)": "heart_rate",
            "SpO2 Level (%)": "spo2",
            "Systolic Blood Pressure (mmHg)": "systolic_bp",
            "Diastolic Blood Pressure (mmHg)": "diastolic_bp",
            "Body Temperature (°C)": "temperature",
            "Temperature (°C)": "temperature",
            "Respiratory Rate": "respiratory_rate",
            "Respiratory Rate (bpm)": "respiratory_rate",
        }

        vals = []
        for name in order:
            key = synonyms.get(str(name), str(name))
            vals.append(float(features.get(key, np.nan)))
        arr = np.array([vals], dtype=np.float32)
        # Replace NaNs with sensible defaults via simple imputation (median-like):
        # For SpO2 default ~97, HR ~80, temp ~37.0, RR ~18, BP 120/80
        defaults = {
            "heart_rate": 80.0,
            "spo2": 97.0,
            "temperature": 37.0,
            "respiratory_rate": 18.0,
            "systolic_bp": 120.0,
            "diastolic_bp": 80.0,
        }
        for i, name in enumerate(order):
            key = synonyms.get(str(name), str(name))
            if np.isnan(arr[0, i]):
                arr[0, i] = defaults.get(key, 0.0)
        return arr

    def predict(self, reading: Dict[str, Any]) -> Dict[str, Any]:
        base = self._extract_base_features(reading)
        x = self._vectorize(base)

        risk_score: float
        proba_used = False
        try:
            # Prefer probability of positive class if available
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba(x)
                if proba is not None and len(proba.shape) == 2 and proba.shape[1] >= 2:
                    risk_score = float(proba[0, 1])
                    proba_used = True
                else:
                    # Some regressors expose predict_proba incorrectly; fall back
                    pred = self.model.predict(x)
                    risk_score = float(pred[0])
            else:
                pred = self.model.predict(x)
                risk_score = float(pred[0])
        except Exception as e:
            logger.error(f"❌ Model prediction failed: {e}")
            return {
                "risk_score": 0.0,
                "risk_level": "UNKNOWN",
                "model": "joblib",
                "error": str(e),
            }

        # Clamp to [0,1] if it's a regressor output
        risk_score = max(0.0, min(1.0, risk_score))
        level = to_risk_level(risk_score)
        return {
            "risk_score": round(risk_score, 4),
            "risk_level": level,
            "model": "joblib",
            "proba_used": proba_used,
        }

