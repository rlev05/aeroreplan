from backend.app.domain import AircraftUnavailability, DisruptionAssessment, RecoveryCostAssumptions, RecoveryPlan, ScheduleScenario, StrategyComparison, StrategyKPIs
from backend.app.optimization.milp_recovery import OptimizationWeights, optimize_recovery
from backend.app.services.disruption_engine import assess_aircraft_unavailability
from backend.app.services.recovery_heuristic import generate_greedy_recovery

def _percentage(
        numerator: float,
        denominator: float
) -> float:
    if denominator <= 0:
        return 0.0

    return round(
        100 * numerator / denominator,
        2
    )

def _calculate_costs(
        total_delay_minutes: int,
        passenger_delay_minutes: int,
        reassigned_flights: int,
        assumptions: RecoveryCostAssumptions
) -> tuple[float, float, float, float]:
    operational_delay_cost = (
        total_delay_minutes * assumptions.passenger_delay_cost_per_minute_gbp
    )

    passenger_delay_cost = (
        passenger_delay_minutes * assumptions.passenger_delay_cost_per_minute_gbp
    )
    reassignment_cost = (
        reassigned_flights * assumptions.aircraft_reassignment_cost_gbp
    )

    total_cost = operational_delay_cost + reassignment_cost + passenger_delay_cost


    return (
        round(operational_delay_cost, 2),
        round(passenger_delay_cost, 2),
        round(reassignment_cost, 2),
        round(total_cost, 2)
    )

def _baseline_kpis(
    assessment: DisruptionAssessment,
    assumptions: RecoveryCostAssumptions,
) -> StrategyKPIs:
    passenger_delay_minutes = sum(
        impact.passengers
        * impact.delay_minutes
        for impact in assessment.impacts
    )

    delayed_flights = len(
        assessment.impacts
    )

    average_delay_minutes = (
        assessment.total_delay_minutes
        / delayed_flights
        if delayed_flights > 0
        else 0.0
    )

    (
        operational_delay_cost,
        passenger_delay_cost,
        reassignment_cost,
        total_cost,
    ) = _calculate_costs(
        total_delay_minutes=(
            assessment.total_delay_minutes
        ),
        passenger_delay_minutes=(
            passenger_delay_minutes
        ),
        reassigned_flights=0,
        assumptions=assumptions,
    )

    return StrategyKPIs(
        strategy="unrecovered_baseline",
        flights_considered=delayed_flights,
        delayed_flights=delayed_flights,
        on_time_flights=0,
        passengers_affected=(
            assessment.passengers_affected
        ),
        passenger_delay_minutes=(
            passenger_delay_minutes
        ),
        total_delay_minutes=(
            assessment.total_delay_minutes
        ),
        average_delay_minutes=round(
            average_delay_minutes,
            2,
        ),
        maximum_delay_minutes=(
            assessment.maximum_delay_minutes
        ),
        reassigned_flights=0,
        delay_reduction_percent=0.0,
        passenger_recovery_percent=0.0,
        on_time_recovery_rate_percent=0.0,
        operational_delay_cost_gbp=(
            operational_delay_cost
        ),
        passenger_delay_cost_gbp=(
            passenger_delay_cost
        ),
        reassignment_cost_gbp=(
            reassignment_cost
        ),
        total_estimated_cost_gbp=(
            total_cost
        ),
    )


def _recovery_kpis(
        plan: RecoveryPlan,
        assumptions: RecoveryCostAssumptions
) -> StrategyKPIs:
    flights_considered = len(plan.flights)
    delayed_flights = sum(
        flight.delay_minutes > 0
        for flight in plan.flights
    )

    on_time_flights = (flights_considered - delayed_flights)

    passenger_delay_minutes = sum(
        flight.passengers * flight.delay_minutes
        for flight in plan.flights
    )

    maximum_delay_minutes = max(
        (
            flight.delay_minutes
            for flight in plan.flights
        ),
        default=0
    )

    average_delay_minutes = (
        plan.total_delay_minutes / flights_considered
        if flights_considered > 0
        else 0.0
    )

    delay_reduction_percent = _percentage(
        plan.baseline_total_delay_minutes - plan.total_delay_minutes,
        plan.baseline_total_delay_minutes
    )

    passenger_recovery_percent = _percentage(
        plan.baseline_passengers_affected - plan.passengers_affected,
        plan.baseline_passengers_affected
    )

    on_time_recovery_rate = _percentage(
        on_time_flights,
        flights_considered
    )

    (
        operational_delay_cost,
        passenger_delay_cost,
        reassignment_cost,
        total_cost
    ) = _calculate_costs(
        total_delay_minutes=plan.total_delay_minutes,
        passenger_delay_minutes=passenger_delay_minutes,
        reassigned_flights=plan.reassigned_flights,
        assumptions=assumptions,
    )

    return StrategyKPIs(
        strategy=plan.strategy,
        flights_considered=flights_considered,
        delayed_flights=delayed_flights,
        on_time_flights=on_time_flights,
        passengers_affected=plan.passengers_affected,
        passenger_delay_minutes=passenger_delay_minutes,
        total_delay_minutes=plan.total_delay_minutes,
        average_delay_minutes=round(average_delay_minutes, 2),
        maximum_delay_minutes=maximum_delay_minutes,
        reassigned_flights=plan.reassigned_flights,
        delay_reduction_percent=delay_reduction_percent,
        passenger_recovery_percent=passenger_recovery_percent,
        on_time_recovery_rate_percent=on_time_recovery_rate,
        operational_delay_cost_gbp=operational_delay_cost,
        passenger_delay_cost_gbp=passenger_delay_cost,
        reassignment_cost_gbp=reassignment_cost,
        total_estimated_cost_gbp=total_cost,
    )


def compare_recovery_strategies(
    scenario: ScheduleScenario,
    disruption: AircraftUnavailability,
    assumptions: RecoveryCostAssumptions | None = None,
) -> StrategyComparison:
    if assumptions is None:
        assumptions = RecoveryCostAssumptions()

    baseline_assessment = (
        assess_aircraft_unavailability(
            scenario,
            disruption,
        )
    )

    greedy_plan = generate_greedy_recovery(
        scenario,
        disruption,
    )

    optimization_weights = OptimizationWeights(
        delay_minute_cost=(
            assumptions
            .operational_delay_cost_per_minute_gbp
        ),
        passenger_delay_minute_cost=(
            assumptions
            .passenger_delay_cost_per_minute_gbp
        ),
        reassignment_cost=(
            assumptions
            .aircraft_reassignment_cost_gbp
        ),
    )

    optimized_result = optimize_recovery(
        scenario=scenario,
        disruption=disruption,
        weights=optimization_weights,
    )

    baseline = _baseline_kpis(
        baseline_assessment,
        assumptions,
    )

    greedy = _recovery_kpis(
        greedy_plan,
        assumptions,
    )

    optimized = _recovery_kpis(
        optimized_result.plan,
        assumptions,
    )

    strategies = [
        baseline,
        greedy,
        optimized,
    ]

    strategy_priority = {
        "milp_recovery": 0,
        "greedy_tail_reassignment": 1,
        "unrecovered_baseline": 2,
    }

    recommended = min(
        strategies,
        key=lambda strategy: (
            strategy.total_estimated_cost_gbp,
            strategy_priority.get(
                strategy.strategy,
                99,
            ),
        ),
    )

    savings = max(
        0.0,
        baseline.total_estimated_cost_gbp
        - recommended.total_estimated_cost_gbp,
    )

    return StrategyComparison(
        baseline=baseline,
        greedy=greedy,
        optimized=optimized,
        recommended_strategy=(
            recommended.strategy
        ),
        estimated_savings_vs_baseline_gbp=round(
            savings,
            2,
        ),
    )




