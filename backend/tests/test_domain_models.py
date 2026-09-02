from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from backend.app.domain import (
    Aircraft,
    AircraftType,
    Airport,
    Flight,
    ScheduleScenario,
)


BASE_TIME = datetime(
    2026,
    9,
    1,
    8,
    0,
    tzinfo=timezone.utc,
)


def create_airports() -> list[Airport]:
    return [
        Airport(
            iata_code="LHR",
            name="London Heathrow Airport",
            city="London",
            country="United Kingdom",
            latitude=51.4700,
            longitude=-0.4543,
        ),
        Airport(
            iata_code="AMS",
            name="Amsterdam Airport Schiphol",
            city="Amsterdam",
            country="Netherlands",
            latitude=52.3105,
            longitude=4.7683,
        ),
        Airport(
            iata_code="CDG",
            name="Charles de Gaulle Airport",
            city="Paris",
            country="France",
            latitude=49.0097,
            longitude=2.5479,
        ),
    ]


def create_aircraft() -> list[Aircraft]:
    return [
        Aircraft(
            aircraft_id="AC001",
            tail_number="G-ARPA",
            aircraft_type=AircraftType.AIRBUS_A320,
            seat_capacity=180,
            home_airport="LHR",
        )
    ]


def create_flight(
    flight_id: str = "FL001",
    origin: str = "LHR",
    destination: str = "AMS",
    departure_offset_hours: int = 0,
    duration_minutes: int = 75,
    aircraft_id: str = "AC001",
    passengers: int = 150,
) -> Flight:
    departure = BASE_TIME + timedelta(
        hours=departure_offset_hours
    )

    return Flight(
        flight_id=flight_id,
        flight_number="AR101",
        origin=origin,
        destination=destination,
        scheduled_departure=departure,
        scheduled_arrival=departure
        + timedelta(minutes=duration_minutes),
        aircraft_id=aircraft_id,
        passengers=passengers,
        distance_km=370,
    )


def test_valid_schedule_scenario() -> None:
    scenario = ScheduleScenario(
        scenario_id="SCENARIO-001",
        airports=create_airports(),
        aircraft=create_aircraft(),
        flights=[
            create_flight(),
            create_flight(
                flight_id="FL002",
                origin="AMS",
                destination="LHR",
                departure_offset_hours=2,
            ),
        ],
    )

    assert len(scenario.flights) == 2
    assert scenario.aircraft[0].seat_capacity == 180


def test_rejects_same_origin_and_destination() -> None:
    with pytest.raises(
        ValidationError,
        match="origin and destination must be different",
    ):
        create_flight(
            origin="LHR",
            destination="LHR",
        )


def test_rejects_passenger_load_above_capacity() -> None:
    with pytest.raises(
        ValidationError,
        match="capacity 180",
    ):
        ScheduleScenario(
            scenario_id="SCENARIO-002",
            airports=create_airports(),
            aircraft=create_aircraft(),
            flights=[
                create_flight(
                    passengers=181,
                )
            ],
        )


def test_rejects_unknown_aircraft() -> None:
    with pytest.raises(
        ValidationError,
        match="unknown aircraft AC999",
    ):
        ScheduleScenario(
            scenario_id="SCENARIO-003",
            airports=create_airports(),
            aircraft=create_aircraft(),
            flights=[
                create_flight(
                    aircraft_id="AC999",
                )
            ],
        )


def test_rejects_overlapping_aircraft_assignments() -> None:
    with pytest.raises(
        ValidationError,
        match="overlapping flights",
    ):
        ScheduleScenario(
            scenario_id="SCENARIO-004",
            airports=create_airports(),
            aircraft=create_aircraft(),
            flights=[
                create_flight(
                    flight_id="FL001",
                    departure_offset_hours=0,
                    duration_minutes=90,
                ),
                create_flight(
                    flight_id="FL002",
                    origin="AMS",
                    destination="CDG",
                    departure_offset_hours=1,
                    duration_minutes=75,
                ),
            ],
        )