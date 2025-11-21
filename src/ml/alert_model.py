"""Training and inference utilities for the vital-sign alert classifier."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)

FEATURE_MAP: Dict[str, str] = {
    "heart_rate": "Heart Rate (bpm)",
    "spo2": "SpO2 Level (%)",
    "systolic_bp": "Systolic Blood Pressure (mmHg)",
    "diastolic_bp": "Diastolic Blood Pressure (mmHg)",
    "temperature": "Body Temperature (°C)",
}

TARGET_MAP: Dict[str, str] = {
    "heart_rate_alert": "Heart Rate Alert",
    "spo2_alert": "SpO2 Level Alert",
    "blood_pressure_alert": "Blood Pressure Alert",
    "temperature_alert": "Temperature Alert",
}

OUTPUT_KEY_MAP: Dict[str, str] = {
    "heart_rate_alert": "heart_rate",
    "spo2_alert": "spo2",
    "blood_pressure_alert": "blood_pressure",
    "temperature_alert": "temperature",
}

ALERT_NORMAL_TOKEN = "normal"


def _clean_column_names(columns: Iterable[str]) -> Dict[str, str]:
    """Return rename map that fixes encoding artefacts."""
    rename_map: Dict[str, str] = {}
    for col in columns:
        fixed = col.replace("�", "°")
        fixed = fixed.strip()
        if fixed != col:
            rename_map[col] = fixed
    return rename_map


def _to_alert_flag(value: Any) -> int:
    """Map alert strings to binary flags."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return 0
    token = str(value).strip().lower()
    return 0 if token == ALERT_NORMAL_TOKEN else 1


@dataclass
class AlertModelTrainer:
    """Train a multi-output classifier that predicts vital alerts."""

    input_path: Path
    model_path: Path
    metrics_path: Optional[Path] = None
    test_size: float = 0.2
    random_state: int = 42
    estimator_kwargs: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.input_path = Path(self.input_path)
        self.model_path = Path(self.model_path)
        if self.metrics_path is not None:
            self.metrics_path = Path(self.metrics_path)
        self.feature_names: List[str] = list(FEATURE_MAP.keys())
        self.label_names: List[str] = list(TARGET_MAP.keys())
        self.pipeline: Optional[Pipeline] = None

    def train(self) -> Dict[str, Any]:
        """Run the full training workflow and return evaluation metrics."""
        logger.info("Loading training data from %s", self.input_path)
        df = pd.read_excel(self.input_path)
        if rename_map := _clean_column_names(df.columns):
            df = df.rename(columns=rename_map)
        required_columns = set(FEATURE_MAP.values()) | set(TARGET_MAP.values())
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        X = df[[FEATURE_MAP[name] for name in self.feature_names]].copy()
        X.columns = self.feature_names
        y = df[[TARGET_MAP[name] for name in self.label_names]].copy()
        y.columns = self.label_names
        y = y.apply(lambda col: col.map(_to_alert_flag))

        stratify_vector = (y.sum(axis=1) > 0).astype(int)
        if stratify_vector.nunique() < 2:
            stratify_vector = None

        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=stratify_vector,
        )

        base_estimator = RandomForestClassifier(
            n_estimators=self.estimator_kwargs.get("n_estimators", 300),
            max_depth=self.estimator_kwargs.get("max_depth"),
            n_jobs=-1,
            random_state=self.random_state,
            class_weight="balanced",
        )

        self.pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("classifier", MultiOutputClassifier(base_estimator)),
        ])

        logger.info("Training alert model...")
        self.pipeline.fit(X_train, y_train)

        y_pred = pd.DataFrame(self.pipeline.predict(X_test), columns=self.label_names)
        metrics = self._build_metrics(y_test, y_pred)
        metrics["train_samples"] = int(len(X_train))
        metrics["test_samples"] = int(len(X_test))

        if self.metrics_path:
            self._save_metrics(metrics)
        self._save_model()
        logger.info("Training complete. Subset accuracy: %.3f", metrics["subset_accuracy"])
        return metrics

    def _build_metrics(self, y_true: pd.DataFrame, y_pred: pd.DataFrame) -> Dict[str, Any]:
        """Compute evaluation metrics for each output."""
        y_true_arr = y_true.values
        y_pred_arr = y_pred.values
        subset_acc = accuracy_score(y_true_arr, y_pred_arr)
        per_label: Dict[str, Dict[str, float]] = {}

        for idx, label in enumerate(self.label_names):
            per_label[label] = {
                "accuracy": accuracy_score(y_true_arr[:, idx], y_pred_arr[:, idx]),
                "precision": precision_score(y_true_arr[:, idx], y_pred_arr[:, idx], zero_division=0),
                "recall": recall_score(y_true_arr[:, idx], y_pred_arr[:, idx], zero_division=0),
                "f1": f1_score(y_true_arr[:, idx], y_pred_arr[:, idx], zero_division=0),
                "positive_rate": float(y_pred_arr[:, idx].mean()),
            }

        return {
            "subset_accuracy": subset_acc,
            "per_label": per_label,
        }

    def _save_model(self) -> None:
        if self.pipeline is None:
            raise RuntimeError("Model has not been trained")
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        artifact = {
            "pipeline": self.pipeline,
            "feature_names": self.feature_names,
            "label_names": self.label_names,
        }
        joblib.dump(artifact, self.model_path)
        logger.info("Saved model to %s", self.model_path)

    def _save_metrics(self, metrics: Dict[str, Any]) -> None:
        if self.metrics_path is None:
            return
        self.metrics_path.parent.mkdir(parents=True, exist_ok=True)
        with self.metrics_path.open("w", encoding="utf-8") as fh:
            json.dump(metrics, fh, indent=2)
        logger.info("Saved metrics to %s", self.metrics_path)


def train_alert_model(
    input_path: Path,
    model_path: Path,
    metrics_path: Optional[Path] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    estimator_kwargs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convenience helper to train the alert model."""
    trainer = AlertModelTrainer(
        input_path=input_path,
        model_path=model_path,
        metrics_path=metrics_path,
        test_size=test_size,
        random_state=random_state,
        estimator_kwargs=estimator_kwargs or {},
    )
    return trainer.train()


class AlertInferenceService:
    """Load a trained model and score incoming vitals."""

    def __init__(self, model_path: Path, threshold: float = 0.5):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Alert model not found at {self.model_path}")
        artifact = joblib.load(self.model_path)
        if isinstance(artifact, dict) and "pipeline" in artifact:
            self.pipeline = artifact["pipeline"]
            self.feature_names = artifact.get("feature_names", list(FEATURE_MAP.keys()))
            self.label_names = artifact.get("label_names", list(TARGET_MAP.keys()))
        else:
            self.pipeline = artifact
            self.feature_names = list(FEATURE_MAP.keys())
            self.label_names = list(TARGET_MAP.keys())
        self.threshold = threshold

    def predict(self, vital_signs: Dict[str, Any]) -> Dict[str, Any]:
        row = [self._extract_feature(name, vital_signs) for name in self.feature_names]
        frame = pd.DataFrame([row], columns=self.feature_names)
        predictions = self.pipeline.predict(frame)[0]
        probas = None
        if hasattr(self.pipeline, "predict_proba"):
            probas = self.pipeline.predict_proba(frame)
        return self._format_output(predictions, probas)

    def _format_output(self, predictions: np.ndarray, probas: Any) -> Dict[str, Any]:
        alerts: Dict[str, Dict[str, Any]] = {}
        confidences: List[float] = []
        for idx, label in enumerate(self.label_names):
            probability = None
            if probas is not None:
                prob_matrix = probas[idx]
                if prob_matrix.ndim == 2 and prob_matrix.shape[1] > 1:
                    probability = float(prob_matrix[0, 1])
            raw_flag = bool(predictions[idx])
            if probability is not None:
                is_alert = probability >= self.threshold
            else:
                is_alert = raw_flag
            key = OUTPUT_KEY_MAP.get(label, label)
            alerts[key] = {
                "is_alert": is_alert,
                "raw_prediction": raw_flag,
                "confidence": probability,
                "source": "alert_model",
            }
            if probability is not None:
                confidences.append(probability)
        alert_count = sum(1 for entry in alerts.values() if entry["is_alert"])
        summary = {
            "alert_count": alert_count,
            "has_alert": alert_count > 0,
            "max_confidence": max(confidences) if confidences else None,
            "threshold": self.threshold,
        }
        return {"alerts": alerts, "summary": summary}

    def _extract_feature(self, feature: str, vital_signs: Dict[str, Any]) -> Any:
        if not isinstance(vital_signs, dict):
            return np.nan
        if feature == "heart_rate":
            return vital_signs.get("heart_rate")
        if feature == "spo2":
            return vital_signs.get("spo2")
        if feature == "temperature":
            return vital_signs.get("temperature")
        if feature == "systolic_bp":
            return vital_signs.get("blood_pressure", {}).get("systolic")
        if feature == "diastolic_bp":
            return vital_signs.get("blood_pressure", {}).get("diastolic")
        return np.nan

    @classmethod
    def from_settings(cls, settings: Any) -> Optional["AlertInferenceService"]:
        model_location = getattr(settings, "ALERT_MODEL_PATH", None)
        if not model_location:
            logger.info("No alert model path configured; skipping ML integration")
            return None
        model_path = Path(model_location)
        if not model_path.is_absolute():
            project_root = Path(__file__).resolve().parents[2]
            model_path = (project_root / model_path).resolve()
        if not model_path.exists():
            logger.warning("Alert model not found at %s; streaming will continue without ML alerts", model_path)
            return None
        threshold = float(getattr(settings, "ALERT_MODEL_THRESHOLD", 0.5))
        try:
            service = cls(model_path=model_path, threshold=threshold)
            logger.info("Loaded alert model from %s", model_path)
            return service
        except Exception as exc:
            logger.error("Failed to load alert model: %s", exc)
            return None
