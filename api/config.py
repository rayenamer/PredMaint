"""All the settings of the service in one place."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = ROOT / "models"
RUNS_CSV = ROOT / "data" / "milling_features.csv"
DATABASE = ROOT / "data" / "historian.db"

# Simulation speed: one cycle every second = one minute of cutting
CYCLE_SECONDS = 1.0
MINUTES_PER_CYCLE = 1.0
SENSOR_NOISE = 0.03  # +-3% random noise on every sensor value

# Downtime (in cycles)
TOOL_CHANGE_CYCLES = 3  # planned tool change: short stop
REPAIR_CYCLES = 15  # tool failure: scrap parts, inspection, repair

# Alarm thresholds. The RUL model is ~5 min off near end of life, so the limits keep a safety margin.
# Tuned on the simulator: ~1 failure for 40 tools, ~70% of the tool life used.
RUL_WARNING_MIN = 15
RUL_CRITICAL_MIN = 8
WEAR_WARNING_MM = 0.35
WEAR_CRITICAL_MM = 0.42
DEBOUNCE_CYCLES = 3  # a condition must last this many cycles to raise (or clear) an alarm
RUL_SMOOTHING_CYCLES = 5  # RUL shown = median of the last predictions
