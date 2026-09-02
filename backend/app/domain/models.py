from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class AircraftType(StrEnum):
    AIRBUS_A319 = "A319"
    AIRBUS_A320 = "A320"
    AIRBUS_A321 = "A321"
    EMBRAER_E190 = "E190"


class Airport(BaseModel):
    iata_code: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )
    name: str = Field(min_length=1)
    city: str = Field(min_length=1)
    country: str = Field(min_length=1)

    latitude: float = Field(
        ge=-90,
        le=90,
    )
    longitude: float = Field(
        ge=-180,
        le=180,
    )


class Aircraft(BaseModel):
    aircraft_id: str = Field(min_length=1)
    tail_number: str = Field(min_length=1)
    aircraft_type: AircraftType

    seat_capacity: int = Field(
        ge=1,
        le=250,
    )

    home_airport: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )


class Flight(BaseModel):
    flight_id: str = Field(min_length=1)

    flight_number: str = Field(
        min_length=2,
        max_length=10,
    )

    origin: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    destination: str = Field(
        min_length=3,
        max_length=3,
        pattern=r"^[A-Z]{3}$",
    )

    scheduled_departure: datetime
    scheduled_arrival: datetime

    aircraft_id: str = Field(min_length=1)

    passengers: int = Field(
        ge=0,
    )

    distance_km: float = Field(
        gt=0,
    )

    @model_validator(mode="after")
    def validate_flight(self) -> "Flight":
        if self.origin == self.destination:
            raise ValueError(
                "Flight origin and destination must be different."
            )

        if self.scheduled_arrival <= self.scheduled_departure:
            raise ValueError(
                "Scheduled arrival must be after scheduled departure."
            )

        return self


class ScheduleScenario(BaseModel):
    scenario_id: str = Field(min_length=1)

    airports: list[Airport]
    aircraft: list[Aircraft]
    flights: list[Flight]

    @model_validator(mode="after")
    def validate_scenario(self) -> "ScheduleScenario":
        self._validate_unique_ids()
        self._validate_references()
        self._validate_passenger_capacity()
        self._validate_aircraft_assignments()

        return self

    def _validate_unique_ids(self) -> None:
        airport_codes = [
            airport.iata_code
            for airport in self.airports
        ]

        aircraft_ids = [
            aircraft.aircraft_id
            for aircraft in self.aircraft
        ]

        flight_ids = [
            flight.flight_id
            for flight in self.flights
        ]

        if len(airport_codes) != len(set(airport_codes)):
            raise ValueError(
                "Airport IATA codes must be unique."
            )

        if len(aircraft_ids) != len(set(aircraft_ids)):
            raise ValueError(
                "Aircraft IDs must be unique."
            )

        if len(flight_ids) != len(set(flight_ids)):
            raise ValueError(
                "Flight IDs must be unique."
            )

    def _validate_references(self) -> None:
        airport_codes = {
            airport.iata_code
            for airport in self.airports
        }

        aircraft_ids = {
            aircraft.aircraft_id
            for aircraft in self.aircraft
        }

        for aircraft in self.aircraft:
            if aircraft.home_airport not in airport_codes:
                raise ValueError(
                    (
                        f"Aircraft {aircraft.aircraft_id} references "
                        f"unknown home airport "
                        f"{aircraft.home_airport}."
                    )
                )

        for flight in self.flights:
            if flight.origin not in airport_codes:
                raise ValueError(
                    (
                        f"Flight {flight.flight_id} references "
                        f"unknown origin {flight.origin}."
                    )
                )

            if flight.destination not in airport_codes:
                raise ValueError(
                    (
                        f"Flight {flight.flight_id} references "
                        f"unknown destination "
                        f"{flight.destination}."
                    )
                )

            if flight.aircraft_id not in aircraft_ids:
                raise ValueError(
                    (
                        f"Flight {flight.flight_id} references "
                        f"unknown aircraft "
                        f"{flight.aircraft_id}."
                    )
                )

    def _validate_passenger_capacity(self) -> None:
        aircraft_by_id = {
            aircraft.aircraft_id: aircraft
            for aircraft in self.aircraft
        }

        for flight in self.flights:
            aircraft = aircraft_by_id[
                flight.aircraft_id
            ]

            if flight.passengers > aircraft.seat_capacity:
                raise ValueError(
                    (
                        f"Flight {flight.flight_id} has "
                        f"{flight.passengers} passengers but "
                        f"aircraft {aircraft.aircraft_id} has "
                        f"capacity {aircraft.seat_capacity}."
                    )
                )

    def _validate_aircraft_assignments(self) -> None:
        flights_by_aircraft: dict[str, list[Flight]] = {}

        for flight in self.flights:
            flights_by_aircraft.setdefault(
                flight.aircraft_id,
                [],
            ).append(flight)

        for aircraft_id, flights in flights_by_aircraft.items():
            ordered_flights = sorted(
                flights,
                key=lambda flight: flight.scheduled_departure,
            )

            for previous, current in zip(
                ordered_flights,
                ordered_flights[1:],
            ):
                if (
                    current.scheduled_departure
                    < previous.scheduled_arrival
                ):
                    raise ValueError(
                        (
                            f"Aircraft {aircraft_id} has "
                            f"overlapping flights "
                            f"{previous.flight_id} and "
                            f"{current.flight_id}."
                        )
                    )