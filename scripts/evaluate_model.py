#!/usr/bin/env python3
"""
Evaluate trained ICU risk model on patients_data_with_alerts.csv

- Loads model from config.settings.MODEL_PATH
- Uses RiskModelPredictor to score each row
- Derives ground-truth label from alert columns (any non-Normal => positive)
- Computes ROC-AUC, PR-AUC, Accuracy, Precision, Recall, F1
- Finds best threshold by F1 if requested
- Saves detailed predictions and summary report

Usage:
    python scripts/evaluate_model.py [--data data/patients_data_with_alerts.csv] [--out data/models]

Outputs:
    - <out>/eval_predictions.csv
    - <out>/eval_report.json
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from typing import List, Dict, Any

import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

# Ensure src is on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.config import settings
from src.ml_models.joblib_predictor import RiskModelPredictor


ALERT_COLUMNS = [
    "Heart Rate Alert",
    "SpO2 Level Alert",
    "Blood Pressure Alert",
    "Temperature Alert",
]


def derive_label(row: pd.Series) -> int:
    """Binary label: 1 if any alert is not 'Normal'.
    Treat values like 'High', 'Low', 'Abnormal' as positive alerts.
    """
    for col in ALERT_COLUMNS:
        val = str(row.get(col, "")).strip().lower()
        if val and val != "normal":
            return 1
    return 0


def row_to_reading(row: pd.Series) -> Dict[str, Any]:
    """Convert dataset row to streaming-like reading dict expected by predictor."""
    # Dataset column names
    hr = row.get("Heart Rate (bpm)")
    spo2 = row.get("SpO2 Level (%)")
    sbp = row.get("Systolic Blood Pressure (mmHg)")
    dbp = row.get("Diastolic Blood Pressure (mmHg)")
    temp = row.get("Body Temperature (°C)") or row.get("Temperature (°C)")

    reading = {
        "patient_id": f"PT-{int(row.get('Patient Number', -1)) if pd.notna(row.get('Patient Number')) else 'UNK'}",
        "timestamp": None,
        "vital_signs": {
            "heart_rate": float(hr) if pd.notna(hr) else np.nan,
            "spo2": float(spo2) if pd.notna(spo2) else np.nan,
            "temperature": float(temp) if pd.notna(temp) else np.nan,
            "respiratory_rate": np.nan,  # not present in dataset
            "blood_pressure": {
                "systolic": float(sbp) if pd.notna(sbp) else np.nan,
                "diastolic": float(dbp) if pd.notna(dbp) else np.nan,
            },
        },
    }
    return reading


def find_best_threshold(y_true: np.ndarray, y_scores: np.ndarray) -> Dict[str, Any]:
    """Grid search thresholds to maximize F1."""
    thresholds = np.linspace(0.05, 0.95, 19)
    best = {"threshold": 0.5, "f1": -1.0, "precision": 0.0, "recall": 0.0, "accuracy": 0.0}
    for t in thresholds:
        y_pred = (y_scores >= t).astype(int)
        prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
        acc = accuracy_score(y_true, y_pred)
        if f1 > best["f1"]:
            best = {"threshold": float(t), "f1": float(f1), "precision": float(prec), "recall": float(rec), "accuracy": float(acc)}
    return best


def evaluate(data_path: Path, out_dir: Path) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_path)
    # Derive labels
    y_true = df.apply(derive_label, axis=1).values.astype(int)

    predictor = RiskModelPredictor(settings.MODEL_PATH)

    scores: List[float] = []
    levels: List[str] = []

    for _, row in df.iterrows():
        reading = row_to_reading(row)
        pred = predictor.predict(reading)
        scores.append(float(pred.get("risk_score", 0.0)))
        levels.append(str(pred.get("risk_level", "UNKNOWN")))

    y_scores = np.array(scores, dtype=float)

    # Metrics
    metrics: Dict[str, Any] = {}
    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_scores))
    except Exception:
        metrics["roc_auc"] = None
    try:
        metrics["pr_auc"] = float(average_precision_score(y_true, y_scores))
    except Exception:
        metrics["pr_auc"] = None

    # Default threshold 0.5
    y_pred_05 = (y_scores >= 0.5).astype(int)
    prec, rec, f1, _ = precision_recall_fscore_support(y_true, y_pred_05, average="binary", zero_division=0)
    acc = accuracy_score(y_true, y_pred_05)
    cm = confusion_matrix(y_true, y_pred_05)

    metrics.update({
        "threshold_default": 0.5,
        "accuracy": float(acc),
        "precision": float(prec),
        "recall": float(rec),
        "f1": float(f1),
        "confusion_matrix": cm.tolist(),
    })

    # Best F1 threshold
    best = find_best_threshold(y_true, y_scores)
    y_pred_best = (y_scores >= best["threshold"]).astype(int)
    cm_best = confusion_matrix(y_true, y_pred_best)
    metrics["best_threshold"] = best
    metrics["confusion_matrix_best"] = cm_best.tolist()

    # Save predictions
    df_out = df.copy()
    df_out["risk_score"] = y_scores
    df_out["risk_level"] = levels
    df_out["label"] = y_true
    df_out["pred_label_default"] = y_pred_05
    df_out["pred_label_best"] = y_pred_best
    df_out.to_csv(out_dir / "eval_predictions.csv", index=False)

    # Save report
    report_path = out_dir / "eval_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Evaluate risk model")
    parser.add_argument("--data", type=str, default=str(ROOT / "data" / "patients_data_with_alerts.csv"))
    parser.add_argument("--out", type=str, default=str(ROOT / "data" / "models"))
    args = parser.parse_args()

    data_path = Path(args.data)
    out_dir = Path(args.out)

    if not data_path.exists():
        print(f"❌ Data not found: {data_path}")
        return 1

    try:
        metrics = evaluate(data_path, out_dir)
        print("✅ Evaluation complete. Summary:")
        print(json.dumps(metrics, indent=2))
        return 0
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

