# Predictive Maintenance – CNC Milling Machine

Predict **when** the cutting tool of a CNC milling machine will be worn out, and plan the
tool change before it fails. Built on real run-to-failure data (NASA Milling dataset).


## Architecture

The diagrams below are written in [Mermaid](https://mermaid.js.org/) and render directly on GitHub / GitLab.

### System overview

```mermaid
flowchart LR
    subgraph OFFLINE["Offline – training (notebooks/)"]
        NASA[("NASA Milling dataset<br/>mill.mat")]
        DL["scripts/download_data.py"]
        FEAT["features.py<br/>shared feature engineering"]
        NB1["01_data_preparation"]
        CSV[("data/milling_features.csv")]
        NB2["02_anomaly_detection<br/>Isolation Forest"]
        NB3["03_wear_estimation<br/>Random Forest"]
        NB4["04_rul_prediction<br/>Random Forest"]
        MODELS[("models/*.joblib<br/>+ *_metrics.json")]

        DL -->|download| NASA
        NASA --> NB1
        FEAT -.-> NB1
        NB1 --> CSV
        CSV --> NB2 & NB3 & NB4
        NB2 & NB3 & NB4 --> MODELS
    end

    subgraph API["Online – FastAPI service (api/, port 8000)"]
        LOOP["acquisition_loop<br/>1 cycle / second"]
        MACHINE["MillingMachine<br/>machine.py<br/>simulator: replays NASA tools + noise"]
        MONITOR["ConditionMonitor<br/>monitoring.py<br/>anomaly · wear · RUL · health"]
        ALARMS["AlarmManager<br/>alarms.py<br/>debounced rules"]
        HIST["Historian<br/>historian.py"]
        DB[("SQLite historian.db<br/>readings · alarms · maintenance")]
        REST["REST endpoints<br/>/status /history /alarms<br/>/maintenance /settings /models"]
        CFG["config.py<br/>thresholds & timings"]

        LOOP --> MACHINE
        LOOP --> MONITOR
        LOOP --> ALARMS
        LOOP --> HIST
        ALARMS --> HIST
        HIST --> DB
        REST --> HIST
        REST -->|replace tool| MACHINE
        CFG -.-> LOOP
    end

    subgraph UI["Dashboard – React + Vite (dashboard/, port 5173)"]
        APP["App.jsx<br/>polls every 1 s"]
        COMP["KpiTiles · MachineTwin · TrendChart<br/>AlarmPanel · MaintenancePanel · ModelCards"]
        PROXY["Vite proxy /api → :8000"]
        APP --> COMP
        APP --> PROXY
    end

    CSV -->|tool runs to replay| MACHINE
    MODELS -->|joblib.load| MONITOR
    FEAT -.->|build_model_input| MONITOR
    PROXY -->|HTTP JSON| REST
    OPERATOR(["Operator"]) -->|ack alarm · replace tool · auto-replace| APP
```

### One acquisition cycle

```mermaid
sequenceDiagram
    autonumber
    participant L as acquisition_loop
    participant M as MillingMachine
    participant C as ConditionMonitor
    participant H as Historian (SQLite)
    participant A as AlarmManager

    L->>M: next_cycle()
    alt machine stopped (tool change / repair)
        M-->>L: None
        L->>H: save_reading("stopped")
    else tool worn beyond 0.5 mm
        L->>H: log_maintenance("failure")
        L->>A: tool_failure()
        L->>M: stop("repair", REPAIR_CYCLES)
    else running
        M-->>L: sensor reading (current, vibration, AE)
        L->>C: analyse(reading)
        C-->>L: anomaly, wear_mm, rul_min, health
        L->>H: save_reading("running", reading, result)
        L->>A: evaluate(result)
        A->>H: raise / clear alarms (debounced 3 cycles)
        opt auto_replace and critical
            L->>H: log_maintenance("planned (auto)")
            L->>M: stop("tool change", TOOL_CHANGE_CYCLES)
        end
    end
```

### Alarm life cycle

```mermaid
stateDiagram-v2
    [*] --> Active: condition true for 3 cycles
    Active --> Acknowledged: operator acknowledges
    Active --> Cleared: condition false for 3 cycles / tool changed
    Acknowledged --> Cleared: condition false for 3 cycles / tool changed
    Cleared --> [*]
```


## Limits of this demo (vs. a real plant)

- The simulator replays the same 13 tools the models were trained on, so live predictions look a bit
  better than the notebook scores. The notebook scores are the honest numbers.
- 16 tools is a small dataset: real projects collect hundreds of tool lives.
- A real plant reads the sensors from the PLC (OPC UA / MQTT), stores them in a real historian,
  and sends work orders to a maintenance system (CMMS). Here everything is in one process.
# PredMaint
