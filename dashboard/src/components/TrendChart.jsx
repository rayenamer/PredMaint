import { CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

// Trend of one value from the historian, with optional threshold lines.
// Gaps in the line = machine stopped (tool change or repair).
export default function TrendChart({ history, dataKey, title, unit, color, thresholds = [] }) {
  return (
    <div className="card chart">
      <h3>
        {title} <span className="unit">({unit})</span>
      </h3>
      <ResponsiveContainer width="100%" height={150}>
        <LineChart data={history}>
          <CartesianGrid stroke="#1e293b" />
          <XAxis dataKey="time" hide />
          <YAxis domain={["auto", "auto"]} width={45} stroke="#64748b" fontSize={11} />
          <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155" }} />
          {thresholds.map((t, i) => (
            <ReferenceLine
              key={t.label}
              y={t.value}
              stroke={t.color}
              strokeDasharray="4 4"
              label={{ value: t.label, fill: t.color, fontSize: 10, position: i === 0 ? "insideTopRight" : "insideBottomLeft" }}
            />
          ))}
          <Line type="monotone" dataKey={dataKey} stroke={color} dot={false} isAnimationActive={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
