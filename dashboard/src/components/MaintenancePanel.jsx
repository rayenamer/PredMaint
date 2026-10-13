// Maintenance actions and the log of every tool change

export default function MaintenancePanel({ status, log, onReplaceTool, onToggleAuto }) {
  const running = status.machine.state === "running";

  return (
    <div className="card">
      <h2>Maintenance</h2>
      <div className="maintenance-actions">
        <button className="primary" disabled={!running} onClick={onReplaceTool}>
          Replace tool now
        </button>
        <label>
          <input type="checkbox" checked={status.settings.auto_replace} onChange={(e) => onToggleAuto(e.target.checked)} />
          Auto-replace on critical alarm
        </label>
      </div>

      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Tool</th>
            <th>Type</th>
            <th>Life</th>
            <th>Wear at removal</th>
          </tr>
        </thead>
        <tbody>
          {log.slice(0, 6).map((entry) => (
            <tr key={entry.id} className={entry.kind === "failure" ? "bad-row" : ""}>
              <td>{entry.time}</td>
              <td>#{entry.tool_id}</td>
              <td>{entry.kind}</td>
              <td>{entry.tool_life_min} min</td>
              <td>{entry.measured_wear_mm} mm</td>
            </tr>
          ))}
        </tbody>
      </table>
      {log.length === 0 && <p className="muted">No tool change yet.</p>}
    </div>
  );
}
