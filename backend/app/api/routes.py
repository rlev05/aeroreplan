from datetime import date
from fastapi import APIRouter
from backend.app.api.schemas import DecisionRequest, DisruptionRequest, OptimizationRequest, SimulationRequest, StrategyComparisonRequest
from backend.app.domain import DecisionAnalysis, DisruptionAssessment, MonteCarloResult, RecoveryPlan, ScheduleScenario, StrategyComparison
from backend.app.services.decision_engine import analyze_recovery_decisions
from backend.app.services.disruption_engine import assess_aircraft_unavailability
from backend.app.services.kpi_engine import compare_recovery_strategies
from backend.app.services.recovery_heuristic import generate_greedy_recovery
from backend.app.services.scenario_generator import generate_short_haul_scenario
from backend.app.simulation import simulate_disruption_uncertainty
from backend.app.optimization import optimize_recovery, MILPRecoveryResult

router = APIRouter(
    prefix="/api",
    tags=["AeroReplan"],
)

def _build_scenario(
        operating_date: date,
        seed: int
) -> ScheduleScenario:
    return generate_short_haul_scenario(
        operating_date=operating_date,
        seed=seed,
    )

@router.get(
    "/scenario",
    response_model=ScheduleScenario,
)
def get_scenario(
    operating_date: date = date(
        2026,
        9,
        1,
    ),
    seed: int = 42,
) -> ScheduleScenario:
    return _build_scenario(
        operating_date,
        seed,
    )


@router.post(
    "/disruption/assess",
    response_model=DisruptionAssessment,
)
def assess_disruption(
    request: DisruptionRequest,
) -> DisruptionAssessment:
    scenario = _build_scenario(
        request.operating_date,
        request.seed,
    )

    return assess_aircraft_unavailability(
        scenario=scenario,
        disruption=request.disruption,
    )


@router.post(
    "/recovery/greedy",
    response_model=RecoveryPlan,
)
def run_greedy_recovery(
    request: DisruptionRequest,
) -> RecoveryPlan:
    scenario = _build_scenario(
        request.operating_date,
        request.seed,
    )

    return generate_greedy_recovery(
        scenario=scenario,
        disruption=request.disruption,
    )


@router.post(
    "/recovery/optimize",
    response_model=MILPRecoveryResult,
)
def run_optimized_recovery(
    request: OptimizationRequest,
) -> MILPRecoveryResult:
    scenario = _build_scenario(
        request.operating_date,
        request.seed,
    )

    return optimize_recovery(
        scenario=scenario,
        disruption=request.disruption,
        weights=request.weights,
    )


@router.post(
    "/analytics/compare",
    response_model=StrategyComparison,
)
def compare_strategies(
    request: StrategyComparisonRequest,
) -> StrategyComparison:
    scenario = _build_scenario(
        request.operating_date,
        request.seed,
    )

    return compare_recovery_strategies(
        scenario=scenario,
        disruption=request.disruption,
        assumptions=request.assumptions,
    )


@router.post(
    "/simulation/monte-carlo",
    response_model=MonteCarloResult,
)
def run_monte_carlo(
    request: SimulationRequest,
) -> MonteCarloResult:
    scenario = _build_scenario(
        request.operating_date,
        request.seed,
    )

    return simulate_disruption_uncertainty(
        scenario=scenario,
        disruption=request.disruption,
        config=request.config,
        assumptions=request.assumptions,
    )


@router.post(
    "/decision/analyze",
    response_model=DecisionAnalysis,
)
def analyze_decisions(
    request: DecisionRequest,
) -> DecisionAnalysis:
    scenario = _build_scenario(
        request.operating_date,
        request.seed,
    )

    return analyze_recovery_decisions(
        scenario=scenario,
        disruption=request.disruption,
        config=request.config,
        assumptions=request.assumptions,
        weights=request.weights,
    )

