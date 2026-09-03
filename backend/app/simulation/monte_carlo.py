from datetime import timedelta
from math import ceil
from random import Random
from statistics import mean, pstdev
from backend.app.domain import AircraftUnavailability, MonteCarloConfig, MonteCarloResult, RecoveryCostAssumptions, ScheduleScenario, SimulationSample, StrategyRiskMetrics
from backend.app.services.kpi_engine import compare_recovery_strategies

def _percentile(
    values: list[float],
    probability: float,
) -> float:
    if not values:
        return 0.0

    ordered = sorted(values)

    index = ceil(
        probability * len(ordered)
    ) - 1

    index = max(
        0,
        min(
            index,
            len(ordered) - 1,
        ),
    )

    return float(
        ordered[index]
    )


def _conditional_value_at_risk(
    values: list[float],
    confidence: float,
) -> float:
    if not values:
        return 0.0

    value_at_risk = _percentile(
        values,
        confidence,
    )

    tail = [
        value
        for value in values
        if value >= value_at_risk
    ]

    if not tail:
        return value_at_risk

    return float(
        mean(tail)
    )


def _build_risk_metrics(
    strategy: str,
    delays: list[int],
    costs: list[float],
    confidence: float,
    severe_delay_threshold_minutes: int,
) -> StrategyRiskMetrics:
    severe_outcomes = sum(
        delay
        >= severe_delay_threshold_minutes
        for delay in delays
    )

    severe_probability = (
        100
        * severe_outcomes
        / len(delays)
        if delays
        else 0.0
    )

    cost_stddev = (
        pstdev(costs)
        if len(costs) > 1
        else 0.0
    )

    return StrategyRiskMetrics(
        strategy=strategy,
        mean_delay_minutes=round(
            mean(delays)
            if delays
            else 0.0,
            2,
        ),
        p90_delay_minutes=round(
            _percentile(
                [
                    float(delay)
                    for delay in delays
                ],
                0.90,
            ),
            2,
        ),
        p95_delay_minutes=round(
            _percentile(
                [
                    float(delay)
                    for delay in delays
                ],
                0.95,
            ),
            2,
        ),
        worst_case_delay_minutes=max(
            delays,
            default=0,
        ),
        severe_delay_probability_percent=round(
            severe_probability,
            2,
        ),
        mean_cost_gbp=round(
            mean(costs)
            if costs
            else 0.0,
            2,
        ),
        cost_stddev_gbp=round(
            cost_stddev,
            2,
        ),
        value_at_risk_gbp=round(
            _percentile(
                costs,
                confidence,
            ),
            2,
        ),
        conditional_value_at_risk_gbp=round(
            _conditional_value_at_risk(
                costs,
                confidence,
            ),
            2,
        ),
        worst_case_cost_gbp=round(
            max(
                costs,
                default=0.0,
            ),
            2,
        ),
    )


def simulate_disruption_uncertainty(
    scenario: ScheduleScenario,
    disruption: AircraftUnavailability,
    config: MonteCarloConfig | None = None,
    assumptions: RecoveryCostAssumptions | None = None,
) -> MonteCarloResult:
    if config is None:
        config = MonteCarloConfig()

    if assumptions is None:
        assumptions = RecoveryCostAssumptions()

    random_generator = Random(
        config.seed
    )

    minimum_end_time = (
        disruption.start_time
        + timedelta(minutes=1)
    )

    samples: list[SimulationSample] = []

    baseline_delays: list[int] = []
    greedy_delays: list[int] = []
    optimized_delays: list[int] = []

    baseline_costs: list[float] = []
    greedy_costs: list[float] = []
    optimized_costs: list[float] = []

    for sample_index in range(
        config.iterations
    ):
        uncertainty_minutes = (
            random_generator.gauss(
                0.0,
                config.end_time_stddev_minutes,
            )
        )

        sampled_end_time = (
            disruption.end_time
            + timedelta(
                minutes=uncertainty_minutes
            )
        )

        sampled_end_time = max(
            sampled_end_time,
            minimum_end_time,
        )

        sampled_disruption = (
            disruption.model_copy(
                update={
                    "disruption_id": (
                        f"{disruption.disruption_id}"
                        f"-MC-{sample_index + 1:05d}"
                    ),
                    "end_time": sampled_end_time,
                }
            )
        )

        comparison = (
            compare_recovery_strategies(
                scenario=scenario,
                disruption=sampled_disruption,
                assumptions=assumptions,
            )
        )

        baseline_delay = (
            comparison
            .baseline
            .total_delay_minutes
        )

        greedy_delay = (
            comparison
            .greedy
            .total_delay_minutes
        )

        optimized_delay = (
            comparison
            .optimized
            .total_delay_minutes
        )

        baseline_cost = (
            comparison
            .baseline
            .total_estimated_cost_gbp
        )

        greedy_cost = (
            comparison
            .greedy
            .total_estimated_cost_gbp
        )

        optimized_cost = (
            comparison
            .optimized
            .total_estimated_cost_gbp
        )

        baseline_delays.append(
            baseline_delay
        )

        greedy_delays.append(
            greedy_delay
        )

        optimized_delays.append(
            optimized_delay
        )

        baseline_costs.append(
            baseline_cost
        )

        greedy_costs.append(
            greedy_cost
        )

        optimized_costs.append(
            optimized_cost
        )

        samples.append(
            SimulationSample(
                sample_id=(
                    sample_index + 1
                ),
                disruption_end_time=(
                    sampled_end_time
                ),
                baseline_delay_minutes=(
                    baseline_delay
                ),
                greedy_delay_minutes=(
                    greedy_delay
                ),
                optimized_delay_minutes=(
                    optimized_delay
                ),
                baseline_cost_gbp=(
                    baseline_cost
                ),
                greedy_cost_gbp=(
                    greedy_cost
                ),
                optimized_cost_gbp=(
                    optimized_cost
                ),
            )
        )

    baseline_metrics = _build_risk_metrics(
        strategy="unrecovered_baseline",
        delays=baseline_delays,
        costs=baseline_costs,
        confidence=config.risk_confidence,
        severe_delay_threshold_minutes=(
            config.severe_delay_threshold_minutes
        ),
    )

    greedy_metrics = _build_risk_metrics(
        strategy="greedy_tail_reassignment",
        delays=greedy_delays,
        costs=greedy_costs,
        confidence=config.risk_confidence,
        severe_delay_threshold_minutes=(
            config.severe_delay_threshold_minutes
        ),
    )

    optimized_metrics = _build_risk_metrics(
        strategy="milp_recovery",
        delays=optimized_delays,
        costs=optimized_costs,
        confidence=config.risk_confidence,
        severe_delay_threshold_minutes=(
            config.severe_delay_threshold_minutes
        ),
    )

    return MonteCarloResult(
        iterations=config.iterations,
        seed=config.seed,
        end_time_stddev_minutes=(
            config.end_time_stddev_minutes
        ),
        risk_confidence=(
            config.risk_confidence
        ),
        severe_delay_threshold_minutes=(
            config.severe_delay_threshold_minutes
        ),
        baseline=baseline_metrics,
        greedy=greedy_metrics,
        optimized=optimized_metrics,
        samples=samples,
    )



