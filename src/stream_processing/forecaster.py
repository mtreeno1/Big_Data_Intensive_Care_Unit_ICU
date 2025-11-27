"""
Simple time-series forecaster for vital signs
- Maintains sliding windows per patient and vital
- Uses linear regression (slope) to extrapolate future values
- Forecast at given horizon seconds
"""
from __future__ import annotations
from typing import Dict, Deque, Tuple
from collections import defaultdict, deque
from datetime import datetime
import numpy as np

# Vitals we forecast
VITAL_KEYS = [
    "heart_rate",
    "spo2",
    "temperature",
    "respiratory_rate",
]

BP_KEYS = ["systolic", "diastolic"]


class VitalForecaster:
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        # patient_id -> vital -> deque[(t_seconds, value)]
        self.buffers: Dict[str, Dict[str, Deque[Tuple[float, float]]]] = defaultdict(lambda: defaultdict(lambda: deque(maxlen=self.window_size)))

    @staticmethod
    def _to_seconds(ts: datetime) -> float:
        return ts.timestamp()

    def update(self, patient_id: str, timestamp: datetime, vitals: Dict) -> None:
        t = self._to_seconds(timestamp)
        for key in VITAL_KEYS:
            if key in vitals and vitals[key] is not None:
                try:
                    val = float(vitals[key])
                except Exception:
                    continue
                self.buffers[patient_id][key].append((t, val))

        # Blood pressure optional
        bp = vitals.get("blood_pressure")
        if isinstance(bp, dict):
            for bp_k in BP_KEYS:
                if bp_k in bp and bp[bp_k] is not None:
                    try:
                        val = float(bp[bp_k])
                    except Exception:
                        continue
                    self.buffers[patient_id][f"bp_{bp_k}"].append((t, val))

    def _forecast_series(self, series: Deque[Tuple[float, float]], horizon_sec: float) -> float | None:
        if len(series) < 3:
            return None
        # linear regression on (t, y)
        ts = np.array([p[0] for p in series], dtype=np.float64)
        ys = np.array([p[1] for p in series], dtype=np.float64)
        t0 = ts[-1]
        # Normalize time to improve conditioning
        x = ts - ts[0]
        try:
            coef = np.polyfit(x, ys, 1)  # y = a*x + b
            a, b = coef[0], coef[1]
        except Exception:
            return float(ys[-1])
        x_h = (t0 + horizon_sec) - ts[0]
        y_h = a * x_h + b
        return float(y_h)

    def forecast_vitals(self, patient_id: str, timestamp: datetime, vitals: Dict, horizon_sec: int = 300) -> Dict:
        """Return forecasted vitals dict at horizon_sec."""
        # Ensure buffer updated with current observation
        self.update(patient_id, timestamp, vitals)

        fc: Dict[str, float] = {}
        buf = self.buffers.get(patient_id, {})
        for key in VITAL_KEYS:
            s = buf.get(key)
            if s:
                y_h = self._forecast_series(s, horizon_sec)
                if y_h is not None:
                    fc[key] = y_h
        # Forecast BP
        bp_f: Dict[str, float] = {}
        for bp_k in BP_KEYS:
            s = buf.get(f"bp_{bp_k}")
            if s:
                y_h = self._forecast_series(s, horizon_sec)
                if y_h is not None:
                    bp_f[bp_k] = y_h
        if bp_f:
            fc["blood_pressure"] = bp_f
        return fc

