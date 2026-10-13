"""
Predictive maintenance service for the CNC milling machine.

A background loop plays the role of the data acquisition system:
every cycle it reads the machine, runs the models, stores everything
in the historian and evaluates the alarms. The dashboard only reads.

Run from the project root:
    uvicorn api.main:app --port 8000
Docs: http://localhost:8000/docs
"""
import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from api import config
from api.alarms import AlarmManager, is_critical
from api.historian import Historian
from api.machine import MillingMachine
from api.monitoring import ConditionMonitor
from features import WEAR_LIMIT_MM

machine = MillingMachine()
monitor = ConditionMonitor()
historian = Historian()
alarms = AlarmManager(historian)
settings = {"auto_replace": False}
latest = {"result": None, "tool_id": None}


def replace_tool(kind):
    """Planned tool change: log it with the wear measured on the removed tool."""
    historian.log_maintenance(machine.tool_id, kind, machine.cut_time, machine.true_wear())
    machine.stop("tool change", config.TOOL_CHANGE_CYCLES)
    alarms.tool_changed()  # the action resolves the tool alarms


def run_one_cycle():
    reading = machine.next_cycle()

    if reading is None:  # machine stopped (tool change or repair)
        historian.save_reading("stopped", machine.tool_id)
        return

    if reading["tool_id"] != latest["tool_id"]:  # a new tool has just been installed
        latest["tool_id"] = reading["tool_id"]
        monitor.new_tool()
        alarms.tool_changed()

    if machine.has_failed():  # nobody changed the tool in time
        historian.log_maintenance(machine.tool_id, "failure", machine.cut_time, machine.true_wear())
        alarms.tool_failure(machine.tool_id)
        machine.stop("repair after failure", config.REPAIR_CYCLES)
        historian.save_reading("stopped", machine.tool_id)
        return

    result = monitor.analyse(reading)
    latest["result"] = result
    historian.save_reading("running", machine.tool_id, reading, result)
    alarms.evaluate(result, machine.tool_id)

    # Auto-replace reacts to the first critical reading (no debounce): some tools wear out in a
    # few minutes, and a failure costs much more than a tool changed a bit early.
    if settings["auto_replace"] and is_critical(result):
        replace_tool("planned (auto)")


async def acquisition_loop():
    while True:
        run_one_cycle()
        await asyncio.sleep(config.CYCLE_SECONDS)


@asynccontextmanager
async def lifespan(app):
    task = asyncio.create_task(acquisition_loop())
    yield
    task.cancel()


app = FastAPI(title="CNC Milling Machine - Predictive Maintenance", lifespan=lifespan)

# Every route is "async" so it runs on the same thread as the acquisition loop (no race conditions)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/status")
async def status():
    """Live state of the machine, latest model outputs and KPIs."""
    log = historian.maintenance_log()
    planned = [m for m in log if m["kind"].startswith("planned")]
    return {
        "machine": {
            "state": machine.state,
            "stop_reason": machine.stop_reason,
            "tool_id": machine.tool_id,
            "cut_time": machine.cut_time,
            "job": {"doc": float(machine.experiment["doc"].iloc[0]),
                    "feed": float(machine.experiment["feed"].iloc[0]),
                    "material": "cast iron" if machine.experiment["material"].iloc[0] == 1 else "steel"},
        },
        "condition": latest["result"],
        "kpis": {
            "availability": historian.availability(),
            "planned_changes": len(planned),
            "failures": len(log) - len(planned),
            # Wear at removal / limit: 100% = tool fully used, lower = changed too early
            "tool_life_used": round(100 * sum(m["measured_wear_mm"] for m in planned) / len(planned) / WEAR_LIMIT_MM)
            if planned else None,
        },
        "limits": {"wear_limit": WEAR_LIMIT_MM, "wear_warning": config.WEAR_WARNING_MM, "wear_critical": config.WEAR_CRITICAL_MM,
                   "rul_warning": config.RUL_WARNING_MIN, "rul_critical": config.RUL_CRITICAL_MIN,
                   "anomaly": monitor.anomaly_threshold},
        "settings": settings,
    }


@app.get("/history")
async def history(limit: int = 200):
    """Last cycles stored in the historian (for the trend charts)."""
    return historian.last_readings(limit)


@app.get("/alarms")
async def list_alarms(limit: int = 30):
    return historian.alarms(limit)


@app.post("/alarms/{alarm_id}/acknowledge")
async def acknowledge(alarm_id: int):
    historian.acknowledge_alarm(alarm_id)
    return {"acknowledged": alarm_id}


@app.post("/maintenance/replace-tool")
async def replace_tool_now():
    if machine.state == "stopped":
        raise HTTPException(409, "Machine is already stopped")
    replace_tool("planned")
    return {"replaced_tool": machine.tool_id}


@app.get("/maintenance")
async def maintenance_log():
    return historian.maintenance_log()


class Settings(BaseModel):
    auto_replace: bool


@app.put("/settings")
async def update_settings(new_settings: Settings):
    settings.update(new_settings.model_dump())
    return settings


@app.get("/models")
async def list_models():
    """Cross-validated scores computed in the notebooks."""
    names = ["anomaly_detector", "wear_estimator", "rul_predictor"]
    return [json.loads((config.MODELS_DIR / f"{name}_metrics.json").read_text()) for name in names]
