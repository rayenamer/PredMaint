// Alarm list: active alarms first. The operator acknowledges, the system clears.

function alarmState(alarm) {
  if (alarm.cleared_at) return "cleared";
  if (alarm.acknowledged_at) return "acknowledged";
  return "active";
}

export default function AlarmPanel({ alarms, onAcknowledge }) {
  const sorted = [...alarms].sort((a, b) => Boolean(a.cleared_at) - Boolean(b.cleared_at));

  return (
    <div className="card">
      <h2>Alarms</h2>
      {alarms.length === 0 && <p className="muted">No alarm.</p>}
      <ul className="alarms">
        {sorted.slice(0, 5).map((alarm) => {
          const state = alarmState(alarm);
          return (
            <li key={alarm.id} className={`alarm ${alarm.severity} ${state}`}>
              <div className="alarm-top">
                <strong>{alarm.message}</strong>
                {state === "active" && <button onClick={() => onAcknowledge(alarm.id)}>Acknowledge</button>}
              </div>
              <div className="alarm-action">→ {alarm.action}</div>
              <div className="muted">
                tool #{alarm.tool_id} · raised {alarm.raised_at} · {state}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
