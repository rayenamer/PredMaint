// Small wrapper around the FastAPI endpoints (proxied by Vite under /api)

async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) throw new Error(`${path} -> HTTP ${response.status}`);
  return response.json();
}

export const fetchStatus = () => request("/status");
export const fetchHistory = (limit) => request(`/history?limit=${limit}`);
export const fetchAlarms = () => request("/alarms");
export const fetchMaintenance = () => request("/maintenance");
export const fetchModels = () => request("/models");

export const acknowledgeAlarm = (id) => request(`/alarms/${id}/acknowledge`, { method: "POST" });
export const replaceTool = () => request("/maintenance/replace-tool", { method: "POST" });
export const saveSettings = (settings) => request("/settings", { method: "PUT", body: JSON.stringify(settings) });
