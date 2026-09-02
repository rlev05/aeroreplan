from datetime import date, datetime, time, timezone
from random import Random

from backend.app.domain import (
    Aircraft,
    AircraftType,
    Airport,
    Flight,
    ScheduleScenario,
)


MINIMUM_TURNAROUND_MINUTES = 45


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
            iata_code="NCL",
            name="Newcastle International Airport",
            city="Newcastle",
            country="United Kingdom",
            latitude=55.0375,
            longitude=-1.6917,
        ),
        Airport(
            iata_code="MAN",
            name="Manchester Airport",
            city="Manchester",
            country="United Kingdom",
            latitude=53.3537,
            longitude=-2.2750,
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
        Airport(
            iata_code="FRA",
            name="Frankfurt Airport",
            city="Frankfurt",
            country="Germany",
            latitude=50.0379,
            longitude=8.5622,
        ),
        Airport(
            iata_code="DUB",
            name="Dublin Airport",
            city="Dublin",
            country="Ireland",
            latitude=53.4264,
            longitude=-6.2499,
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
        ),
        Aircraft(
            aircraft_id="AC002",
            tail_number="G-ARPB",
            aircraft_type=AircraftType.AIRBUS_A319,
            seat_capacity=156,
            home_airport="NCL",
        ),
        Aircraft(
            aircraft_id="AC003",
            tail_number="G-ARPC",
            aircraft_type=AircraftType.EMBRAER_E190,
            seat_capacity=100,
            home_airport="MAN",
        ),
    ]


def _utc_datetime(
    operating_date: date,
    hour: int,
    minute: int,
) -> datetime:
    return datetime.combine(
        operating_date,
        time(
            hour=hour,
            minute=minute,
            tzinfo=timezone.utc,
        ),
    )


def _passenger_load(
    seat_capacity: int,
    random_generator: Random,
) -> int:
    load_factor = random_generator.uniform(
        0.68,
        0.94,
    )

    return round(
        seat_capacity * load_factor
    )


def generate_short_haul_scenario(
    operating_date: date = date(2026, 9, 1),
    seed: int = 42,
) -> ScheduleScenario:
    aircraft = create_aircraft()

    capacity_by_aircraft = {
        item.aircraft_id: item.seat_capacity
        for item in aircraft
    }

    random_generator = Random(seed)

    flight_templates = [
        {
            "flight_id": "FL001",
            "flight_number": "AR101",
            "origin": "LHR",
            "destination": "AMS",
            "departure": (6, 30),
            "arrival": (7, 45),
            "aircraft_id": "AC001",
            "distance_km": 370,
        },
        {
            "flight_id": "FL002",
            "flight_number": "AR102",
            "origin": "AMS",
            "destination": "LHR",
            "departure": (8, 35),
            "arrival": (9, 50),
            "aircraft_id": "AC001",
            "distance_km": 370,
        },
        {
            "flight_id": "FL003",
            "flight_number": "AR103",
            "origin": "LHR",
            "destination": "CDG",
            "departure": (10, 50),
            "arrival": (12, 10),
            "aircraft_id": "AC001",
            "distance_km": 347,
        },
        {
            "flight_id": "FL004",
            "flight_number": "AR104",
            "origin": "CDG",
            "destination": "LHR",
            "departure": (13, 0),
            "arrival": (14, 15),
            "aircraft_id": "AC001",
            "distance_km": 347,
        },
        {
            "flight_id": "FL005",
            "flight_number": "AR201",
            "origin": "NCL",
            "destination": "DUB",
            "departure": (7, 0),
            "arrival": (8, 0),
            "aircraft_id": "AC002",
            "distance_km": 346,
        },
        {
            "flight_id": "FL006",
            "flight_number": "AR202",
            "origin": "DUB",
            "destination": "NCL",
            "departure": (8, 50),
            "arrival": (9, 50),
            "aircraft_id": "AC002",
            "distance_km": 346,
        },
        {
            "flight_id": "FL007",
            "flight_number": "AR203",
            "origin": "NCL",
            "destination": "AMS",
            "departure": (10, 45),
            "arrival": (12, 10),
            "aircraft_id": "AC002",
            "distance_km": 516,
        },
        {
            "flight_id": "FL008",
            "flight_number": "AR204",
            "origin": "AMS",
            "destination": "NCL",
            "departure": (13, 0),
            "arrival": (14, 25),
            "aircraft_id": "AC002",
            "distance_km": 516,
        },
        {
            "flight_id": "FL009",
            "flight_number": "AR301",
            "origin": "MAN",
            "destination": "FRA",
            "departure": (6, 45),
            "arrival": (8, 25),
            "aircraft_id": "AC003",
            "distance_km": 834,
        },
        {
            "flight_id": "FL010",
            "flight_number": "AR302",
            "origin": "FRA",
            "destination": "MAN",
            "departure": (9, 20),
            "arrival": (11, 0),
            "aircraft_id": "AC003",
            "distance_km": 834,
        },
        {
            "flight_id": "FL011",
            "flight_number": "AR303",
            "origin": "MAN",
            "destination": "CDG",
            "departure": (12, 0),
            "arrival": (13, 30),
            "aircraft_id": "AC003",
            "distance_km": 588,
        },
        {
            "flight_id": "FL012",
            "flight_number": "AR304",
            "origin": "CDG",
            "destination": "MAN",
            "departure": (14, 20),
            "arrival": (15, 50),
            "aircraft_id": "AC003",
            "distance_km": 588,
        },
    ]

    flights: list[Flight] = []

    for template in flight_templates:
        aircraft_id = template["aircraft_id"]

        departure_hour, departure_minute = template[
            "departure"
        ]

        arrival_hour, arrival_minute = template[
            "arrival"
        ]

        flights.append(
            Flight(
                flight_id=template["flight_id"],
                flight_number=template["flight_number"],
                origin=template["origin"],
                destination=template["destination"],
                scheduled_departure=_utc_datetime(
                    operating_date,
                    departure_hour,
                    departure_minute,
                ),
                scheduled_arrival=_utc_datetime(
                    operating_date,
                    arrival_hour,
                    arrival_minute,
                ),
                aircraft_id=aircraft_id,
                passengers=_passenger_load(
                    capacity_by_aircraft[aircraft_id],
                    random_generator,
                ),
                distance_km=template["distance_km"],
            )
        )

    return ScheduleScenario(
        scenario_id=(
            f"SHORT-HAUL-{operating_date.isoformat()}"
        ),
        airports=create_airports(),
        aircraft=aircraft,
        flights=flights,
    )