"""
Condition monitoring: runs the 3 models on every reading of the machine.
"""
import json
import statistics

import joblib

from api import config
from features import SIGNAL_FEATURES, SIGNAL_NAMES, WEAR_LIMIT_MM, build_model_input


class ConditionMonitor:
    def __init__(self):
        self.anomaly_model = joblib.load(config.MODELS_DIR / "anomaly_detector.joblib")
        self.wear_model = joblib.load(config.MODELS_DIR / "wear_estimator.joblib")
        self.rul_model = joblib.load(config.MODELS_DIR / "rul_predictor.joblib")
        # One reading at a time: a single thread is faster than a thread pool
        for model in (self.anomaly_model, self.wear_model, self.rul_model):
            model.n_jobs = 1
        anomaly_metrics = json.loads((config.MODELS_DIR / "anomaly_detector_metrics.json").read_text())
        self.anomaly_threshold = anomaly_metrics["threshold"]
        self.new_tool()

    def new_tool(self):
        """Call after every tool change: the next reading becomes the new baseline."""
        self.baseline = None
        self.recent_rul = []

    def analyse(self, reading):
        if self.baseline is None:
            self.baseline = {name: reading[name] for name in SIGNAL_NAMES}
        X = build_model_input(reading, self.baseline)

        anomaly_score = float(-self.anomaly_model.score_samples(X[SIGNAL_FEATURES])[0])
        wear_mm = float(self.wear_model.predict(X)[0])
        rul_raw = max(0.0, float(self.rul_model.predict(X)[0]))

        # Single predictions are noisy: show the median of the last few
        self.recent_rul = (self.recent_rul + [rul_raw])[-config.RUL_SMOOTHING_CYCLES:]
        rul_min = statistics.median(self.recent_rul)

        return {
            "anomaly_score": round(anomaly_score, 3),
            "anomaly": anomaly_score > self.anomaly_threshold,
            "wear_mm": round(wear_mm, 3),
            "rul_min": round(rul_min, 1),
            "health": round(max(0.0, min(100.0, 100 * (1 - wear_mm / WEAR_LIMIT_MM))), 1),
        }
