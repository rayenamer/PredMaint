import { useEffect, useState } from "react";
import * as api from "./api.js";
import { overallStatus } from "./status.js";
import KpiTiles from "./components/KpiTiles.jsx";
import MachineTwin from "./components/MachineTwin.jsx";
import AlarmPanel from "./components/AlarmPanel.jsx";
import MaintenancePanel from "./components/MaintenancePanel.jsx";
import TrendChart from "./components/TrendChart.jsx";
import ModelCards from "./components/ModelCards.jsx";

const REFRESH_MS = 1000;
const HISTORY_SIZE = 240; // cycles shown on the trend charts

export default function App() {
  const [status, setStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [alarms, setAlarms] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [models, setModels] = useState([]);
  const [error, setError] = useState(null);

  // Everything comes from the historian: refreshing the page loses nothing
  const refresh = async () => {
    try {
      const [s, h, a, m] = await Promise.all([
        api.fetchStatus(),
        api.fetchHistory(HISTORY_SIZE),
        api.fetchAlarms(),
        api.fetchMaintenance(),
      ]);
      setStatus(s);
      setHistory(h);
      setAlarms(a);
      setMaintenance(m);
      setError(null);
    } catch {
      setError("API not reachable - is FastAPI running on port 8000?");
    }
  };

  useEffect(() => {
    api.fetchModels().then(setModels).catch(() => {});
    refresh();
    const timer = setInterval(refresh, REFRESH_MS);
    return () => clearInterval(timer);
  }, []);

  // Operator actions: call the API then refresh right away
  const acknowledge = (id) => api.acknowledgeAlarm(id).then(refresh);
  const replaceTool = () => api.replaceTool().then(refresh);
  const toggleAuto = (enabled) => api.saveSettings({ auto_replace: enabled }).then(refresh);

  if (!status) return <div className="app">{error ?? "Loading..."}</div>;

  const overall = overallStatus(status.machine, alarms);
  const lastReading = [...history].reverse().find((row) => row.state === "running");
  const { limits } = status;

  return (
    <div className="app">
      <header>
        <div>
          <h1>CNC Milling Machine #1 - Predictive Maintenance</h1>
          <p className="muted">Matsuura MC-510V · sensors replayed from NASA run-to-failure experiments</p>
        </div>
        <span className={`badge ${overall.level}`}>{overall.label}</span>
      </header>

      {error && <div className="error">{error}</div>}

      <KpiTiles status={status} />

      <main className="grid">
        <section className="card">
          <h2>Machine view</h2>
          <MachineTwin status={status} overall={overall} lastReading={lastReading} />
        </section>
        <section className="side">
          <AlarmPanel alarms={alarms} onAcknowledge={acknowledge} />
        </section>
      </main>

      <section className="charts">
        <TrendChart
          history={history} dataKey="wear_mm" title="Estimated tool wear" unit="mm" color="#facc15"
          thresholds={[
            { value: limits.wear_limit, label: "limit", color: "#ef4444" },
            { value: limits.wear_critical, label: "replace", color: "#f97316" },
          ]}
        />
        <TrendChart
          history={history} dataKey="rul_min" title="Remaining useful life" unit="min" color="#38bdf8"
          thresholds={[
            { value: limits.rul_warning, label: "plan change", color: "#f59e0b" },
            { value: limits.rul_critical, label: "replace", color: "#ef4444" },
          ]}
        />
        <TrendChart
          history={history} dataKey="anomaly_score" title="Anomaly score" unit="0-1" color="#a78bfa"
          thresholds={[{ value: limits.anomaly, label: "abnormal", color: "#f59e0b" }]}
        />
        <TrendChart history={history} dataKey="current_dc" title="Spindle motor current (DC)" unit="sensor V" color="#22c55e" />
      </section>

      <section className="grid">
        <MaintenancePanel status={status} log={maintenance} onReplaceTool={replaceTool} onToggleAuto={toggleAuto} />
        <ModelCards models={models} />
      </section>
    </div>
  );
}
