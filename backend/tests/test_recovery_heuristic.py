from datetime import datetime, timezone

from backend.app.domain import (
    AircraftUnavailability,
    RecoveryActionType,
)
from backend.app.services import (
    generate_greedy_recovery,
    generate_short_haul_scenario,
)


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


def test_greedy_recovery_reduces_total_delay() -> None:
    scenario = generate_short_haul_scenario()

    plan = generate_greedy_recovery(
        scenario,
        create_test_disruption(),
    )

    assert (
        plan.baseline_total_delay_minutes
        == 310
    )

    assert plan.total_delay_minutes == 115

    assert plan.delay_reduction_minutes == 195


def test_recovery_uses_reserve_aircraft() -> None:
    scenario = generate_short_haul_scenario()

    plan = generate_greedy_recovery(
        scenario,
        create_test_disruption(),
    )

    flights = {
        flight.flight_id: flight
        for flight in plan.flights
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


def test_reassigned_flights_operate_without_delay() -> None:
    scenario = generate_short_haul_scenario()

    plan = generate_greedy_recovery(
        scenario,
        create_test_disruption(),
    )

    flights = {
        flight.flight_id: flight
        for flight in plan.flights
    }

    assert flights["FL002"].delay_minutes == 115
    assert flights["FL003"].delay_minutes == 0
    assert flights["FL004"].delay_minutes == 0

    assert (
        flights["FL003"].action
        == RecoveryActionType.REASSIGN
    )

    assert (
        flights["FL004"].action
        == RecoveryActionType.REASSIGN
    )


def test_recovery_tracks_reassigned_flights() -> None:
    scenario = generate_short_haul_scenario()

    plan = generate_greedy_recovery(
        scenario,
        create_test_disruption(),
    )

    assert plan.reassigned_flights == 2


def test_recovery_reduces_passenger_disruption() -> None:
    scenario = generate_short_haul_scenario(
        seed=42
    )

    plan = generate_greedy_recovery(
        scenario,
        create_test_disruption(),
    )

    assert (
        plan.passengers_affected
        < plan.baseline_passengers_affected
    )

    assert plan.passengers_recovered > 0


def test_recovery_preserves_rotation_continuity() -> None:
    scenario = generate_short_haul_scenario()

    plan = generate_greedy_recovery(
        scenario,
        create_test_disruption(),
    )

    reserve_flights = [
        flight
        for flight in plan.flights
        if flight.assigned_aircraft_id
        == "AC004"
    ]

    reserve_flights = sorted(
        reserve_flights,
        key=lambda flight:
        flight.projected_departure,
    )

    for previous, current in zip(
        reserve_flights,
        reserve_flights[1:],
    ):
        assert (
            previous.destination
            == current.origin
        )