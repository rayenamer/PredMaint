"""
Historian: stores every cycle, alarm and maintenance action in SQLite.

Real plants use a time-series database (OSIsoft PI, InfluxDB, TimescaleDB...);
SQLite keeps the same idea with zero setup. The database is reset at each start.
"""
import sqlite3
from datetime import datetime

from api import config

SCHEMA = """
CREATE TABLE readings (
    id INTEGER PRIMARY KEY,
    time TEXT, state TEXT, tool_id INTEGER, cut_time REAL,
    current_ac REAL, current_dc REAL, vib_table REAL, vib_spindle REAL, ae_table REAL, ae_spindle REAL,
    anomaly_score REAL, wear_mm REAL, rul_min REAL, health REAL
);
CREATE TABLE alarms (
    id INTEGER PRIMARY KEY,
    rule TEXT, severity TEXT, message TEXT, action TEXT, tool_id INTEGER,
    raised_at TEXT, acknowledged_at TEXT, cleared_at TEXT
);
CREATE TABLE maintenance (
    id INTEGER PRIMARY KEY,
    time TEXT, tool_id INTEGER, kind TEXT, tool_life_min REAL, measured_wear_mm REAL
);
"""


def now():
    return datetime.now().strftime("%H:%M:%S")


class Historian:
    def __init__(self):
        config.DATABASE.unlink(missing_ok=True)
        self.db = sqlite3.connect(config.DATABASE, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def _insert(self, table, row):
        columns = ", ".join(row)
        placeholders = ", ".join("?" for _ in row)
        cursor = self.db.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(row.values()))
        self.db.commit()
        return cursor.lastrowid

    def _select(self, sql, params=()):
        return [dict(row) for row in self.db.execute(sql, params)]

    # ---- readings
    def save_reading(self, state, tool_id, reading=None, result=None):
        row = {"time": now(), "state": state, "tool_id": tool_id}
        if reading:
            row.update({key: reading[key] for key in ["cut_time", "current_ac", "current_dc", "vib_table",
                                                       "vib_spindle", "ae_table", "ae_spindle"]})
        if result:
            row.update({key: result[key] for key in ["anomaly_score", "wear_mm", "rul_min", "health"]})
        self._insert("readings", row)

    def last_readings(self, limit):
        rows = self._select("SELECT * FROM readings ORDER BY id DESC LIMIT ?", (limit,))
        return rows[::-1]

    def availability(self):
        """Percentage of cycles where the machine was running."""
        row = self._select("SELECT AVG(state = 'running') * 100 AS value FROM readings")[0]
        return round(row["value"] or 100, 1)

    # ---- alarms
    def raise_alarm(self, rule, severity, message, action, tool_id):
        alarm = {"rule": rule, "severity": severity, "message": message, "action": action,
                 "tool_id": tool_id, "raised_at": now()}
        return self._insert("alarms", alarm)

    def open_alarm(self, rule):
        rows = self._select("SELECT * FROM alarms WHERE rule = ? AND cleared_at IS NULL", (rule,))
        return rows[0] if rows else None

    def acknowledge_alarm(self, alarm_id):
        self.db.execute("UPDATE alarms SET acknowledged_at = ? WHERE id = ? AND acknowledged_at IS NULL", (now(), alarm_id))
        self.db.commit()

    def clear_alarm(self, alarm_id):
        self.db.execute("UPDATE alarms SET cleared_at = ? WHERE id = ?", (now(), alarm_id))
        self.db.commit()

    def clear_all_alarms(self):
        self.db.execute("UPDATE alarms SET cleared_at = ? WHERE cleared_at IS NULL", (now(),))
        self.db.commit()

    def alarms(self, limit):
        return self._select("SELECT * FROM alarms ORDER BY id DESC LIMIT ?", (limit,))

    # ---- maintenance
    def log_maintenance(self, tool_id, kind, tool_life_min, measured_wear_mm):
        self._insert("maintenance", {"time": now(), "tool_id": tool_id, "kind": kind,
                                     "tool_life_min": round(tool_life_min, 1),
                                     "measured_wear_mm": round(measured_wear_mm, 3)})

    def maintenance_log(self):
        return self._select("SELECT * FROM maintenance ORDER BY id DESC")
