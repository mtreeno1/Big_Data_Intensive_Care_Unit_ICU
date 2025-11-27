#!/usr/bin/env python3
import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import joblib

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

# Map cột CSV -> feature chuẩn trong pipeline
FEATURE_MAP = {
    "heart_rate": "Heart Rate (bpm)",
    "spo2": "SpO2 Level (%)",
    "systolic_bp": "Systolic Blood Pressure (mmHg)",
    "diastolic_bp": "Diastolic Blood Pressure (mmHg)",
    "temperature": "Body Temperature (°C)",
    # Respiratory rate không có trong CSV -> gán mặc định
}

ALERT_COLS = [
    "Heart Rate Alert",
    "SpO2 Level Alert",
    "Blood Pressure Alert",
    "Temperature Alert",
]

def derive_label(row) -> int:
    # Bất kỳ alert khác "Normal" => dương tính (1)
    for c in ALERT_COLS:
        val = str(row.get(c, "")).strip().lower()
        if val and val != "normal":
            return 1
    return 0

def load_data(path: Path):
    df = pd.read_csv(path)

    # Nhãn
    y = df.apply(derive_label, axis=1).astype(int).values

    # Lấy 5 feature có trong CSV
    X = df[
        [
            FEATURE_MAP["heart_rate"],
            FEATURE_MAP["spo2"],
            FEATURE_MAP["systolic_bp"],
            FEATURE_MAP["diastolic_bp"],
            FEATURE_MAP["temperature"],
        ]
    ].copy()

    # Thêm respiratory_rate mặc định (để khớp RiskModelPredictor)
    X["Respiratory Rate (bpm)"] = 18.0

    # Thứ tự features phải KHỚP với predictor:
    # ["heart_rate","spo2","systolic_bp","diastolic_bp","temperature","respiratory_rate"]
    X_model = np.column_stack(
        [
            X[FEATURE_MAP["heart_rate"]].astype(float).values,
            X[FEATURE_MAP["spo2"]].astype(float).values,
            X[FEATURE_MAP["systolic_bp"]].astype(float).values,
            X[FEATURE_MAP["diastolic_bp"]].astype(float).values,
            X[FEATURE_MAP["temperature"]].astype(float).values,
            X["Respiratory Rate (bpm)"].astype(float).values,
        ]
    )
    return X_model, y

def train_model(X: np.ndarray, y: np.ndarray):
    pipe = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=200)),
        ]
    )
    pipe.fit(X, y)
    return pipe

def main():
    ap = argparse.ArgumentParser(description="Train ICU risk model from patients_data_with_alerts.csv")
    ap.add_argument("--data", required=True, help="Path to patients_data_with_alerts.csv")
    ap.add_argument("--out", required=True, help="Path to save trained model (.joblib)")
    args = ap.parse_args()

    data_path = Path(args.data)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    X, y = load_data(data_path)
    model = train_model(X, y)

    # Quick train metrics
    y_prob = model.predict_proba(X)[:, 1]
    y_hat = (y_prob >= 0.5).astype(int)
    acc = accuracy_score(y, y_hat)
    f1 = f1_score(y, y_hat)
    try:
        auc = roc_auc_score(y, y_prob)
    except Exception:
        auc = None

    print(f"Train metrics: acc={acc:.3f}, f1={f1:.3f}, auc={None if auc is None else round(auc,3)}")

    joblib.dump(model, str(out_path))
    print(f"Saved model to: {out_path}")

if __name__ == "__main__":
    main()

