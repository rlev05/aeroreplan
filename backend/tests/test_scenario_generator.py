from datetime import date
from backend.app.services import MINIMUM_TURNAROUND_MINUTES, generate_short_haul_scenario


def test_generate_realistic_short_haul_scenario() -> None:
    scenario = generate_short_haul_scenario()

    assert len(scenario.airports) == 7
    assert len(scenario.aircraft) == 3
    assert len(scenario.flights) == 12


def test_scenario_generation_is_reproducible() -> None:
    first = generate_short_haul_scenario(
        seed=123
    )

    second = generate_short_haul_scenario(
        seed=123
    )

    first_passengers = [
        flight.passengers
        for flight in first.flights
    ]

    second_passengers = [
        flight.passengers
        for flight in second.flights
    ]

    assert first_passengers == second_passengers

def test_different_seed_changes_passenger_loads() -> None:
    first = generate_short_haul_scenario(
        seed=1
    )

    second = generate_short_haul_scenario(
        seed=2
    )

    assert [
        flight.passengers
        for flight in first.flights
    ] != [
        flight.passengers
        for flight in second.flights
    ]

def test_passenger_loads_remain_within_capacity() -> None:
    scenario = generate_short_haul_scenario()

    aircraft_by_id = {
        aircraft.aircraft_id: aircraft
        for aircraft in scenario.aircraft
    }

    for flight in scenario.flights:
        aircraft = aircraft_by_id[
            flight.aircraft_id
        ]

        assert flight.passengers <= aircraft.seat_capacity

        load_factor = (
            flight.passengers
            / aircraft.seat_capacity
        )

        assert 0.65 <= load_factor <= 0.95



def test_aircraft_rotations_are_geographically_continuous() -> None:
    scenario = generate_short_haul_scenario()

    for aircraft in scenario.aircraft:
        flights = sorted(
            [
                flight
                for flight in scenario.flights
                if flight.aircraft_id
                == aircraft.aircraft_id
            ],
            key=lambda flight:
            flight.scheduled_departure
        )

        assert flights[0].origin == aircraft.home_airport

        for previous, current in zip(
            flights,
            flights[1:]
        ):
            assert (
                previous.destination == current.origin
            )

            turnaround = (
                current.scheduled_departure - previous.scheduled_departure
            )

            turnaround_minutes = (
                turnaround.total_seconds() / 60
            )

            assert (
                turnaround_minutes >= MINIMUM_TURNAROUND_MINUTES
            )

def test_scenario_uses_requested_operating_date() -> None:
    operating_date = date(2026,10,15)

    scenario = generate_short_haul_scenario(
        operating_date=operating_date
    )

    assert all(
        flight.scheduled_departure.date() == operating_date
        for flight in scenario.flights
    )

