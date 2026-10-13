// Row of key numbers: tool condition on the left, plant KPIs on the right

function Tile({ label, value, unit, hint, color }) {
  return (
    <div className="tile">
      <div className="tile-label">{label}</div>
      <div className="tile-value" style={{ color }}>
        {value ?? "-"} <span className="unit">{value != null && unit}</span>
      </div>
      {hint && <div className="tile-hint">{hint}</div>}
    </div>
  );
}

// Green / orange / red depending on two thresholds (works both ways)
function levelColor(value, warning, critical, higherIsWorse = true) {
  if (value == null) return undefined;
  const worse = (a, b) => (higherIsWorse ? a >= b : a < b);
  if (worse(value, critical)) return "#ef4444";
  if (worse(value, warning)) return "#f59e0b";
  return "#22c55e";
}

export default function KpiTiles({ status }) {
  const { condition, kpis, limits, machine } = status;
  const running = machine.state === "running";
  const c = running ? condition : null;
  // Health thresholds follow the wear thresholds (health = 100% - wear / limit)
  const healthAt = (wear) => 100 * (1 - wear / limits.wear_limit);

  return (
    <div className="tiles">
      <Tile label="Tool health" value={c?.health} unit="%" hint={`tool #${machine.tool_id}`} color={levelColor(c?.health, healthAt(limits.wear_warning), healthAt(limits.wear_critical), false)} />
      <Tile
        label="Estimated wear"
        value={c?.wear_mm}
        unit="mm"
        hint={`limit ${limits.wear_limit} mm`}
        color={levelColor(c?.wear_mm, limits.wear_warning, limits.wear_critical)}
      />
      <Tile
        label="Remaining life"
        value={c?.rul_min}
        unit="min"
        hint="of cutting"
        color={levelColor(c?.rul_min, limits.rul_warning, limits.rul_critical, false)}
      />
      <Tile label="Signals" value={c ? (c.anomaly ? "Abnormal" : "Normal") : null} hint={c && `score ${c.anomaly_score}`} color={c?.anomaly ? "#f59e0b" : "#22c55e"} />
      <Tile label="Availability" value={kpis.availability} unit="%" hint="time running" />
      <Tile label="Tool changes" value={`${kpis.planned_changes} / ${kpis.failures}`} hint="planned / failures" color={kpis.failures > 0 ? "#ef4444" : undefined} />
      <Tile label="Tool life used" value={kpis.tool_life_used} unit="%" hint="at planned changes" />
    </div>
  );
}
