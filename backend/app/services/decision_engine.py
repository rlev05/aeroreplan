from backend.app.domain import AircraftUnavailability, DecisionAnalysis, DecisionWeights, MonteCarloConfig, RecoveryCostAssumptions, ScheduleScenario, StrategyDecisionPoint
from backend.app.services.emissions_engine import compare_recovery_emissions
from backend.app.simulation import simulate_disruption_uncertainty

def _dominates(
        first: StrategyDecisionPoint,
        second: StrategyDecisionPoint
) -> bool:
    first_values = (
        first.expected_cost_gbp,
        first.cvar_cost_gbp,
        first.expected_delay_minutes,
        first.emissions_kg_co2e
    )

    second_values = (
        second.expected_cost_gbp,
        second.cvar_cost_gbp,
        second.expected_delay_minutes,
        second.emissions_kg_co2e
    )

    no_worse = all(
        first_value <= second_value
        for first_value, second_value
        in zip(
            first_values, second_values
        )
    )

    strictly_better = any(
        first_value < second_value
        for first_value, second_value
        in zip(
            first_values, second_values
        )
    )

    return no_worse and strictly_better


def _mark_pareto_frontier(
    strategies: list[StrategyDecisionPoint],
) -> list[StrategyDecisionPoint]:
    result: list[StrategyDecisionPoint] = []

    for strategy in strategies:
        dominated = any(
            _dominates(
                other,
                strategy,
            )
            for other in strategies
            if other.strategy != strategy.strategy
        )

        result.append(
            strategy.model_copy(
                update={
                    "is_pareto_optimal": (
                        not dominated
                    )
                }
            )
        )

    return result

def _score_strategy(
        strategy: StrategyDecisionPoint,
        weights: DecisionWeights,
) -> float:
    return(
        weights.expected_cost_weight
        * strategy.expected_cost_gbp
        + weights.cvar_weight
        * strategy.cvar_cost_gbp
        + weights.delay_weight
        * strategy.expected_delay_minutes
        + weights.emissions_weight
        * strategy.emissions_kg_co2e
    )


def analyze_recovery_decisions(
        scenario: ScheduleScenario,
        disruption: AircraftUnavailability,
        config: MonteCarloConfig | None = None,
        assumptions: RecoveryCostAssumptions | None = None,
        weights: DecisionWeights | None = None,
) -> DecisionAnalysis:
    if config is None:
        config = MonteCarloConfig(iterations=100)

    if assumptions is None:
        assumptions = RecoveryCostAssumptions()

    if weights is None:
        weights = DecisionWeights()

    risk_result = (
        simulate_disruption_uncertainty(
            scenario = scenario,
            disruption = disruption,
            config = config,
            assumptions = assumptions,
        )
    )

    emissions_result = (
        compare_recovery_emissions(
            scenario = scenario,
            disruption = disruption,
        )
    )

    strategies = [
        StrategyDecisionPoint(
            strategy = "unrecovered_baseline",
            expected_cost_gbp = (
                risk_result.baseline.conditional_value_at_risk_gbp
            ),
            cvar_cost_gbp = (
                risk_result.baseline.conditional_value_at_risk_gbp
            ),
            expected_delay_minutes = (
                risk_result.baseline.mean_delay_minutes
            ),
            emissions_kg_co2e = (
                emissions_result.baseline.estimated_co2e_kg
            ),
        ),
        StrategyDecisionPoint(
            strategy = "greedy_tail_reassignment",
            expected_cost_gbp = (
                risk_result.greedy.mean_cost_gbp
            ),
            cvar_cost_gbp = (
                risk_result.greedy.conditional_value_at_risk_gbp
            ),
            expected_delay_minutes = (
                risk_result.greedy.mean_delay_minutes
            ),
            emissions_kg_co2e = (
                emissions_result.greedy.estimated_co2e_kg
            ),
        ),
        StrategyDecisionPoint(
            strategy = "milp_recovery",
            expected_cost_gbp=(
                risk_result.optimized.mean_cost_gbp
            ),
            cvar_cost_gbp=(
                risk_result.optimized.conditional_value_at_risk_gbp
            ),
            expected_delay_minutes=(
                risk_result.optimized.mean_delay_minutes
            ),
            emissions_kg_co2e=(
                emissions_result.optimized.estimated_co2e_kg
            ),
        ),
    ]

    strategies = _mark_pareto_frontier(strategies)

    recommended = min(
        strategies,
        key=lambda strategy: _score_strategy(strategy, weights),
    )

    pareto_strategies = [
        strategy.strategy
        for strategy in strategies
        if strategy.is_pareto_optimal
    ]

    return DecisionAnalysis(
        strategies=strategies,
        recommended_strategy=(
            recommended.strategy
        ),
        pareto_strategies=(
            pareto_strategies
        ),
    )





