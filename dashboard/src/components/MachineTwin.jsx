import { COLORS } from "../status.js";

// Live synoptic view of the milling machine (SVG).
// The tool colour follows the estimated wear, the spindle spins only while cutting,
// the beacon shows the overall status.

// Blend from grey (new) to red (worn) for a value between 0 and 1
function wearColor(ratio) {
  const r = Math.min(1, Math.max(0, ratio));
  return `rgb(${Math.round(148 + 107 * r)}, ${Math.round(163 - 120 * r)}, ${Math.round(184 - 140 * r)})`;
}

export default function MachineTwin({ status, overall, lastReading }) {
  const { machine, condition, limits } = status;
  const running = machine.state === "running";
  const wearRatio = running && condition ? condition.wear_mm / limits.wear_limit : 0;
  const beacon = COLORS[overall.level];
  const value = (key, digits = 2) => (running && lastReading?.[key] != null ? lastReading[key].toFixed(digits) : "-");

  return (
    <svg viewBox="0 0 440 380" className="twin">
      {/* Floor and base */}
      <rect x="20" y="340" width="400" height="14" rx="3" fill="#1e293b" />
      <rect x="60" y="300" width="300" height="40" rx="4" fill="#334155" />

      {/* Column */}
      <rect x="70" y="60" width="60" height="240" fill="#475569" />

      {/* Status beacon */}
      <rect x="94" y="40" width="12" height="20" fill="#64748b" />
      <circle cx="100" cy="32" r="12" fill={beacon} className={overall.level === "critical" ? "blink" : ""} />
      <text x="122" y="37" className="twin-label" fill={beacon}>{overall.label}</text>

      {/* Head with spindle motor */}
      <rect x="70" y="70" width="230" height="50" rx="4" fill="#64748b" />
      <circle cx="260" cy="95" r="20" fill="#1e293b" />
      <g className={running ? "spin" : ""} style={{ transformOrigin: "260px 95px" }}>
        <rect x="257" y="77" width="6" height="36" fill="#94a3b8" />
        <rect x="242" y="92" width="36" height="6" fill="#94a3b8" />
      </g>

      {/* Spindle and cutting tool */}
      <rect x="245" y="120" width="30" height="50" fill="#475569" />
      <rect x="254" y="170" width="12" height="70" fill={wearColor(wearRatio)} />
      <polygon points="254,240 266,240 260,252" fill={wearColor(wearRatio)} />

      {/* Table and workpiece */}
      <rect x="150" y="285" width="200" height="15" fill="#94a3b8" />
      <rect x="200" y="252" width="120" height="33" rx="2" fill="#78716c" />

      {/* Sensor tags, placed where the real sensors are */}
      <text x="290" y="68" className="twin-label">motor current {value("current_dc")}</text>
      <text x="285" y="150" className="twin-label">spindle vib {value("vib_spindle", 3)}</text>
      <text x="285" y="168" className="twin-label">spindle AE {value("ae_spindle", 3)}</text>
      <text x="150" y="214" className="twin-label">tool #{machine.tool_id}</text>
      <text x="130" y="232" className="twin-label">{running ? `${machine.cut_time} min cut` : ""}</text>
      <text x="200" y="322" className="twin-label">table vib {value("vib_table", 3)} | AE {value("ae_table", 3)}</text>
      <text x="20" y="374" className="twin-label">
        job: {machine.job.material}, depth {machine.job.doc} mm, feed {machine.job.feed} mm/rev
      </text>
    </svg>
  );
}
