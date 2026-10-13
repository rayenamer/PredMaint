"""
Alarm management.

An alarm is raised only when its condition lasts DEBOUNCE_CYCLES cycles in a row
(one noisy reading must not wake up the operator), and cleared the same way.
Life cycle:  ACTIVE  ->  ACKNOWLEDGED (by the operator)  ->  CLEARED (condition gone)
"""
from api import config


def is_critical(result):
    return result["rul_min"] < config.RUL_CRITICAL_MIN or result["wear_mm"] >= config.WEAR_CRITICAL_MM


def is_warning(result):
    return result["rul_min"] < config.RUL_WARNING_MIN or result["wear_mm"] >= config.WEAR_WARNING_MM


RULES = [
    {
        "rule": "tool_critical",
        "severity": "critical",
        "condition": is_critical,
        "message": f"Tool at end of life (RUL < {config.RUL_CRITICAL_MIN} min or wear > {config.WEAR_CRITICAL_MM} mm)",
        "action": "Stop and replace the tool now",
    },
    {
        "rule": "tool_warning",
        "severity": "warning",
        "condition": is_warning,
        "message": f"Tool end of life soon (RUL < {config.RUL_WARNING_MIN} min or wear > {config.WEAR_WARNING_MM} mm)",
        "action": "Plan a tool change at the end of the current part",
    },
    {
        "rule": "abnormal_signals",
        "severity": "warning",
        "condition": lambda result: result["anomaly"],
        "message": "Abnormal current / vibration / acoustic signature",
        "action": "Check tool edge, workpiece clamping and coolant",
    },
]


class AlarmManager:
    def __init__(self, historian):
        self.historian = historian
        self.reset()

    def reset(self):
        self.true_count = {rule["rule"]: 0 for rule in RULES}
        self.false_count = {rule["rule"]: 0 for rule in RULES}

    def evaluate(self, result, tool_id):
        for rule in RULES:
            name = rule["rule"]
            open_alarm = self.historian.open_alarm(name)

            if rule["condition"](result):
                self.true_count[name] += 1
                self.false_count[name] = 0
                if self.true_count[name] >= config.DEBOUNCE_CYCLES and not open_alarm:
                    self.historian.raise_alarm(name, rule["severity"], rule["message"], rule["action"], tool_id)
            else:
                self.false_count[name] += 1
                self.true_count[name] = 0
                if self.false_count[name] >= config.DEBOUNCE_CYCLES and open_alarm:
                    self.historian.clear_alarm(open_alarm["id"])

    def tool_failure(self, tool_id):
        self.historian.raise_alarm(
            "tool_failure", "critical",
            "Tool worn beyond limit - parts out of tolerance, machine stopped",
            "Repair: replace tool, inspect spindle, scrap the last parts",
            tool_id,
        )

    def tool_changed(self):
        """A new tool removes every tool-related condition."""
        self.historian.clear_all_alarms()
        self.reset()
