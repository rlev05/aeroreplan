import type {
  DisruptionAssessment,
  DisruptionRequest,
  MILPRecoveryResult,
  ScheduleScenario,
  StrategyComparison,
} from "./types";


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";


async function requestJson<T>(
  url: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${url}`,
    options,
  );

  if (!response.ok) {
    throw new Error(
      `API request failed with status ${response.status}`,
    );
  }

  return response.json() as Promise<T>;
}


export async function fetchScenario(): Promise<ScheduleScenario> {
  return requestJson<ScheduleScenario>(
    "/api/scenario",
  );
}


export async function assessDisruption(
  request: DisruptionRequest,
): Promise<DisruptionAssessment> {
  return requestJson<DisruptionAssessment>(
    "/api/disruption/assess",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
  );
}


export async function optimizeRecovery(
  request: DisruptionRequest,
): Promise<MILPRecoveryResult> {
  return requestJson<MILPRecoveryResult>(
    "/api/recovery/optimize",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
  );
}


export async function compareStrategies(
  request: DisruptionRequest,
): Promise<StrategyComparison> {
  return requestJson<StrategyComparison>(
    "/api/analytics/compare",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    },
  );
}