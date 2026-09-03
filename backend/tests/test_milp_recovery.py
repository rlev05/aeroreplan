from datetime import datetime, timezone
from backend.app.domain import AircraftUnavailability, RecoveryActionType
from backend.app.optimization import OptimizationWeights, optimize_recovery
from backend.app.services import generate_greedy_recovery, generate_short_haul_scenario

def create_test_disruption() -> AircraftUnavailability:
    return AircraftUnavailability(
        disruption_id="DISRUPTION-001",
        aircraft_id="AC001",
        start_time=datetime(
            2026,
            9,
            1,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        end_time=datetime(
            2026,
            9,
            1,
            10,
            30,
            tzinfo=timezone.utc,
        ),
        reason="Aircraft technical issue",
    )


def test_milp_finds_optimal_recovery() -> None:
    scenario = generate_short_haul_scenario()

    result = optimize_recovery(
        scenario,
        create_test_disruption(),
    )

    assert result.solver_status == "OPTIMAL"

    assert (
        result.plan.baseline_total_delay_minutes
        == 310
    )

    assert (
        result.plan.total_delay_minutes
        == 115
    )

    assert (
        result.plan.delay_reduction_minutes
        == 195
    )


def test_milp_assigns_feasible_reserve_aircraft() -> None:
    scenario = generate_short_haul_scenario()

    result = optimize_recovery(
        scenario,
        create_test_disruption(),
    )

    flights = {
        flight.flight_id: flight
        for flight in result.plan.flights
    }

    assert (
        flights["FL002"].assigned_aircraft_id
        == "AC001"
    )

    assert (
        flights["FL003"].assigned_aircraft_id
        == "AC004"
    )

    assert (
        flights["FL004"].assigned_aircraft_id
        == "AC004"
    )

    assert (
        flights["FL003"].action
        == RecoveryActionType.REASSIGN
    )

    assert (
        flights["FL004"].action
        == RecoveryActionType.REASSIGN
    )


def test_milp_is_never_worse_than_greedy_for_test_scenario() -> None:
    scenario = generate_short_haul_scenario()

    disruption = create_test_disruption()

    greedy = generate_greedy_recovery(
        scenario,
        disruption,
    )

    optimized = optimize_recovery(
        scenario,
        disruption,
    )

    assert (
        optimized.plan.total_delay_minutes
        <= greedy.total_delay_minutes
    )


def test_high_reassignment_cost_can_prefer_delay() -> None:
    scenario = generate_short_haul_scenario()

    weights = OptimizationWeights(
        delay_minute_cost=1.0,
        passenger_delay_minute_cost=0.01,
        reassignment_cost=1000.0,
    )

    result = optimize_recovery(
        scenario,
        create_test_disruption(),
        weights=weights,
    )

    assert result.plan.reassigned_flights == 0

    assert (
        result.plan.total_delay_minutes
        == 310
    )


def test_milp_exposes_solver_metrics() -> None:
    scenario = generate_short_haul_scenario()

    result = optimize_recovery(
        scenario,
        create_test_disruption(),
    )

    assert result.objective_value >= 0
    assert result.solve_time_ms >= 0

    assert result.candidate_count >= 2


def test_no_impact_disruption_requires_no_recovery() -> None:
    scenario = generate_short_haul_scenario()

    disruption = AircraftUnavailability(
        disruption_id="DISRUPTION-LATE",
        aircraft_id="AC001",
        start_time=datetime(
            2026,
            9,
            1,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        end_time=datetime(
            2026,
            9,
            1,
            20,
            0,
            tzinfo=timezone.utc,
        ),
    )

    result = optimize_recovery(
        scenario,
        disruption,
    )

    assert result.plan.total_delay_minutes == 0
    assert result.plan.reassigned_flights == 0
    assert result.plan.flights == []