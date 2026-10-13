"""
Simulated milling machine.

There is no real machine here, so we replay the real NASA run-to-failure
experiments: every new tool follows the measurements of one real tool
(picked at random), interpolated minute by minute, with some sensor noise.
The true wear is hidden from the models - it is only used to decide when
the tool actually fails, like in real life.
"""
import random

import numpy as np
import pandas as pd

from api import config
from features import CONDITIONS, SIGNAL_NAMES, WEAR_LIMIT_MM


class MillingMachine:
    def __init__(self):
        runs = pd.read_csv(config.RUNS_CSV)
        # Only replay tools that really reached the wear limit
        self.experiments = [tool for _, tool in runs.groupby("case") if tool["failure_time"].notna().any()]
        self.tool_id = 0
        self.state = "running"  # "running" or "stopped"
        self.stop_reason = None
        self.stop_cycles_left = 0
        self._install_new_tool()

    def _install_new_tool(self):
        self.tool_id += 1
        self.experiment = random.choice(self.experiments)
        # Start one cycle before the first recorded cut, so the first reading is the new-tool baseline
        self.cut_time = self.experiment["cut_time"].iloc[0] - config.MINUTES_PER_CYCLE

    def true_wear(self):
        """Real wear of the tool (in a factory you only know it by stopping and measuring)."""
        measured = self.experiment.dropna(subset=["wear_mm"])
        return float(np.interp(self.cut_time, measured["cut_time"], measured["wear_mm"].cummax()))

    def has_failed(self):
        return self.true_wear() >= WEAR_LIMIT_MM

    def stop(self, reason, cycles):
        self.state = "stopped"
        self.stop_reason = reason
        self.stop_cycles_left = cycles

    def next_cycle(self):
        """Advance one cycle. Returns the sensor reading, or None while the machine is stopped."""
        if self.state == "stopped":
            self.stop_cycles_left -= 1
            if self.stop_cycles_left <= 0:
                self._install_new_tool()
                self.state, self.stop_reason = "running", None
            return None

        self.cut_time += config.MINUTES_PER_CYCLE
        reading = {"tool_id": self.tool_id, "cut_time": self.cut_time}
        for name in SIGNAL_NAMES:
            value = np.interp(self.cut_time, self.experiment["cut_time"], self.experiment[name])
            reading[name] = float(value) * random.gauss(1, config.SENSOR_NOISE)
        for name in CONDITIONS:
            reading[name] = float(self.experiment[name].iloc[0])
        return reading
