from backend.app.domain import AircraftUnavailability, EmissionsComparison, RecoveryPlan, ScheduleScenario, StrategyEmissions
from backend.app.optimization import OptimizationWeights, optimize_recovery
from backend.app.services.disruption_engine import assess_aircraft_unavailability
from backend.app.services.emissions import estimate_flight_emissions_kg
from backend.app.services.recovery_heuristic import generate_greedy_recovery


def _baseline_emissions(
        scenario: ScheduleScenario,
        flight_ids: set[str]
) -> float:
    aircraft_by_id = {
        aircraft.aircraft_id: aircraft
        for aircraft in scenario.aircraft
    }

    total = 0.0

    for flight in scenario.flights:
        if flight.flight_id not in flight_ids:
            continue

        aircraft = aircraft_by_id[flight.aircraft_id]
        total += estimate_flight_emissions_kg(
            distance_km=flight.distance_km,
            aircraft_type=aircraft.aircraft_type,
        )

    return round(
        total,
        2
    )

def _recovery_emissions(
    scenario: ScheduleScenario,
    plan: RecoveryPlan,
) -> float:
    aircraft_by_id = {
        aircraft.aircraft_id: aircraft
        for aircraft in scenario.aircraft
    }

    original_flights = {
        flight.flight_id: flight
        for flight in scenario.flights
    }

    total = 0.0

    for recovered_flight in plan.flights:
        original_flight = original_flights[
            recovered_flight.flight_id
        ]

        assigned_aircraft = aircraft_by_id[
            recovered_flight.assigned_aircraft_id
        ]

        total += estimate_flight_emissions_kg(
            distance_km=original_flight.distance_km,
            aircraft_type=(
                assigned_aircraft.aircraft_type
            ),
        )

    return round(
        total,
        2,
    )


def compare_recovery_emissions(
    scenario: ScheduleScenario,
    disruption: AircraftUnavailability,
    emissions_weight: float = 0.0,
) -> EmissionsComparison:
    baseline_assessment = (
        assess_aircraft_unavailability(
            scenario,
            disruption,
        )
    )

    impacted_ids = {
        impact.flight_id
        for impact in baseline_assessment.impacts
    }

    baseline_total = _baseline_emissions(
        scenario,
        impacted_ids,
    )

    greedy_plan = generate_greedy_recovery(
        scenario,
        disruption,
    )

    optimized_result = optimize_recovery(
        scenario=scenario,
        disruption=disruption,
        weights=OptimizationWeights(
            emissions_cost_per_kg_co2e=(
                emissions_weight
            ),
        ),
    )

    greedy_total = _recovery_emissions(
        scenario,
        greedy_plan,
    )

    optimized_total = _recovery_emissions(
        scenario,
        optimized_result.plan,
    )

    return EmissionsComparison(
        baseline=StrategyEmissions(
            strategy="unrecovered_baseline",
            flights_considered=len(
                impacted_ids
            ),
            estimated_co2e_kg=(
                baseline_total
            ),
            change_vs_baseline_kg=0.0,
        ),
        greedy=StrategyEmissions(
            strategy=greedy_plan.strategy,
            flights_considered=len(
                greedy_plan.flights
            ),
            estimated_co2e_kg=(
                greedy_total
            ),
            change_vs_baseline_kg=round(
                greedy_total
                - baseline_total,
                2,
            ),
        ),
        optimized=StrategyEmissions(
            strategy=(
                optimized_result.plan.strategy
            ),
            flights_considered=len(
                optimized_result.plan.flights
            ),
            estimated_co2e_kg=(
                optimized_total
            ),
            change_vs_baseline_kg=round(
                optimized_total
                - baseline_total,
                2,
            ),
        ),
        emissions_weight=(
            emissions_weight
        ),
    )


