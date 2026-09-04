import type {
  AnalysisCaseDetail,
  AnalysisCaseList,
  DecisionAnalysis,
  DecisionRequest,
  DisruptionAssessment,
  DisruptionRequest,
  MILPRecoveryResult,
  MonteCarloResult,
  SaveAnalysisCaseRequest,
  ScheduleScenario,
  SimulationRequest,
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


function postJson<T>(
  url: string,
  payload: unknown,
): Promise<T> {
  return requestJson<T>(
    url,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify(
        payload,
      ),
    },
  );
}


export async function fetchScenario(): Promise<ScheduleScenario> {
  return requestJson<ScheduleScenario>(
    "/api/scenario",
  );
}


export async function assessDisruption(
  request: DisruptionRequest,
): Promise<DisruptionAssessment> {
  return postJson<DisruptionAssessment>(
    "/api/disruption/assess",
    request,
  );
}


export async function optimizeRecovery(
  request: DisruptionRequest,
): Promise<MILPRecoveryResult> {
  return postJson<MILPRecoveryResult>(
    "/api/recovery/optimize",
    request,
  );
}


export async function compareStrategies(
  request: DisruptionRequest,
): Promise<StrategyComparison> {
  return postJson<StrategyComparison>(
    "/api/analytics/compare",
    request,
  );
}


export async function analyzeDecisions(
  request: DecisionRequest,
): Promise<DecisionAnalysis> {
  return postJson<DecisionAnalysis>(
    "/api/decision/analyze",
    request,
  );
}


export async function runMonteCarlo(
  request: SimulationRequest,
): Promise<MonteCarloResult> {
  return postJson<MonteCarloResult>(
    "/api/simulation/monte-carlo",
    request,
  );
}


export async function saveAnalysisCase(
  request: SaveAnalysisCaseRequest,
): Promise<AnalysisCaseDetail> {
  return postJson<AnalysisCaseDetail>(
    "/api/cases/analyze",
    request,
  );
}


export async function fetchAnalysisCases(
  limit = 50,
): Promise<AnalysisCaseList> {
  return requestJson<AnalysisCaseList>(
    `/api/cases?limit=${limit}`,
  );
}


export async function fetchAnalysisCase(
  caseId: string,
): Promise<AnalysisCaseDetail> {
  return requestJson<AnalysisCaseDetail>(
    `/api/cases/${caseId}`,
  );
}