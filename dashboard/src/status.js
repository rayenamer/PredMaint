// Overall machine status shown by the beacon and the header badge

export const COLORS = {
  ok: "#22c55e",
  warning: "#f59e0b",
  critical: "#ef4444",
  stopped: "#64748b",
};

export function overallStatus(machine, alarms) {
  const open = alarms.filter((alarm) => !alarm.cleared_at);
  if (open.some((alarm) => alarm.severity === "critical")) return { level: "critical", label: "CRITICAL" };
  if (machine.state === "stopped") return { level: "stopped", label: `STOPPED - ${machine.stop_reason}` };
  if (open.length > 0) return { level: "warning", label: "WARNING" };
  return { level: "ok", label: "RUNNING" };
}
