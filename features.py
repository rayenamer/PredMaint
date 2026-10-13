"""
Feature engineering shared by the training notebooks and the API.

One "run" of the NASA Milling dataset = one cut of the milling machine,
recorded by 6 sensors (9000 samples each). Each run is summarised by
one number per sensor, then compared with the values of the same tool
when it was new (the "baseline"), like real condition monitoring does.
"""
import numpy as np
import pandas as pd
import scipy.io

# Tool is considered worn out at 0.5 mm flank wear (ISO 8688 end-of-life criterion)
WEAR_LIMIT_MM = 0.5

# One summary value per sensor: (name in mill.mat, our name, how to summarise)
SIGNALS = [
    ("smcAC", "current_ac", "rms"),  # spindle motor current, AC part
    ("smcDC", "current_dc", "mean"),  # spindle motor current, DC part
    ("vib_table", "vib_table", "rms"),  # table vibration
    ("vib_spindle", "vib_spindle", "rms"),  # spindle vibration
    ("AE_table", "ae_table", "mean"),  # acoustic emission at the table
    ("AE_spindle", "ae_spindle", "mean"),  # acoustic emission at the spindle
]
SIGNAL_NAMES = [name for _, name, _ in SIGNALS]

# Cutting conditions of the job
CONDITIONS = ["doc", "feed", "material"]  # depth of cut (mm), feed (mm/rev), 1=cast iron 2=steel

# Sensor values relative to the new tool (used alone by the anomaly detector)
SIGNAL_FEATURES = [f"{name}_rel" for name in SIGNAL_NAMES]

# Inputs of the wear and RUL models, in this exact order
FEATURES = SIGNAL_FEATURES + CONDITIONS + ["cut_time"]


def summarise_signal(samples, method):
    """Keep the stable middle of the cut (skip tool entry and exit)."""
    middle = samples[2000:7000]
    if method == "rms":
        return float(np.std(middle))
    return float(np.mean(middle))


def load_mill_runs(path):
    """Read mill.mat and return one row per run with sensor summaries."""
    runs = scipy.io.loadmat(path)["mill"][0]
    rows = []
    for run in runs:
        row = {
            "case": int(run["case"][0, 0]),  # one case = one tool used until worn
            "run": int(run["run"][0, 0]),
            "cut_time": float(run["time"][0, 0]),  # minutes of cutting so far
            "wear_mm": float(run["VB"][0, 0]),  # flank wear measured with a microscope (NaN = not measured)
            "doc": float(run["DOC"][0, 0]),
            "feed": float(run["feed"][0, 0]),
            "material": int(run["material"][0, 0]),
        }
        for mat_name, name, method in SIGNALS:
            row[name] = summarise_signal(run[mat_name].ravel(), method)
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["case", "cut_time"]).reset_index(drop=True)


def add_relative_features(df):
    """Divide each signal by its value on the first run of the same tool (new tool = 1.0)."""
    df = df.copy()
    for name in SIGNAL_NAMES:
        df[f"{name}_rel"] = df[name] / df.groupby("case")[name].transform("first")
    return df


def relative_to_baseline(signals, baseline):
    """Same as add_relative_features, for one live reading."""
    return {f"{name}_rel": signals[name] / baseline[name] for name in SIGNAL_NAMES}


def build_model_input(reading, baseline):
    """One live reading (dict) + the tool baseline -> 1-row table for the models."""
    row = relative_to_baseline(reading, baseline)
    row.update({key: reading[key] for key in CONDITIONS + ["cut_time"]})
    return pd.DataFrame([row])[FEATURES]
