import type { ScheduleScenario } from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";

export async function fetchScenario(): Promise<ScheduleScenario> {
  const response = await fetch(
    `${API_BASE_URL}/api/scenario`,
  );

  if (!response.ok) {
    throw new Error(
      `Scenario request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<ScheduleScenario>;
}