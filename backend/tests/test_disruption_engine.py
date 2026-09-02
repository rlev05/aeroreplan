from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.app.domain import (
    AircraftUnavailability,
)
from backend.app.services import (
    assess_aircraft_unavailability,
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


def test_rejects_invalid_disruption_window() -> None:
    with pytest.raises(
        ValidationError,
        match="end time must be after start time",
    ):
        AircraftUnavailability(
            disruption_id="INVALID",
            aircraft_id="AC001",
            start_time=datetime(
                2026,
                9,
                1,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            end_time=datetime(
                2026,
                9,
                1,
                9,
                0,
                tzinfo=timezone.utc,
            ),
        )


def test_identifies_direct_and_downstream_impacts() -> None:
    scenario = generate_short_haul_scenario()

    assessment = assess_aircraft_unavailability(
        scenario,
        create_test_disruption(),
    )

    impacted_ids = [
        impact.flight_id
        for impact in assessment.impacts
    ]

    assert impacted_ids == [
        "FL002",
        "FL003",
        "FL004",
    ]

    assert assessment.impacted_flights == 3
    assert assessment.directly_affected_flights == 1


def test_propagates_delay_through_aircraft_rotation() -> None:
    scenario = generate_short_haul_scenario()

    assessment = assess_aircraft_unavailability(
        scenario,
        create_test_disruption(),
    )

    impacts = {
        impact.flight_id: impact
        for impact in assessment.impacts
    }

    assert impacts["FL002"].delay_minutes == 115
    assert impacts["FL003"].delay_minutes == 100
    assert impacts["FL004"].delay_minutes == 95

    assert assessment.total_delay_minutes == 310
    assert assessment.maximum_delay_minutes == 115


def test_counts_passengers_exposed_to_disruption() -> None:
    scenario = generate_short_haul_scenario(
        seed=42
    )

    assessment = assess_aircraft_unavailability(
        scenario,
        create_test_disruption(),
    )

    expected_passengers = sum(
        flight.passengers
        for flight in scenario.flights
        if flight.flight_id
        in {
            "FL002",
            "FL003",
            "FL004",
        }
    )

    assert (
        assessment.passengers_affected
        == expected_passengers
    )


def test_does_not_affect_other_aircraft() -> None:
    scenario = generate_short_haul_scenario()

    assessment = assess_aircraft_unavailability(
        scenario,
        create_test_disruption(),
    )

    assert all(
        impact.aircraft_id == "AC001"
        for impact in assessment.impacts
    )


def test_rejects_unknown_aircraft() -> None:
    scenario = generate_short_haul_scenario()

    disruption = AircraftUnavailability(
        disruption_id="DISRUPTION-UNKNOWN",
        aircraft_id="AC999",
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
            0,
            tzinfo=timezone.utc,
        ),
    )

    with pytest.raises(
        ValueError,
        match="unknown aircraft AC999",
    ):
        assess_aircraft_unavailability(
            scenario,
            disruption,
        )


def test_disruption_after_rotation_has_no_impact() -> None:
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

    assessment = assess_aircraft_unavailability(
        scenario,
        disruption,
    )

    assert assessment.impacted_flights == 0
    assert assessment.passengers_affected == 0
    assert assessment.total_delay_minutes == 0