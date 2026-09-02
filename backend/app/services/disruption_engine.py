from datetime import timedelta

from backend.app.domain import (
    AircraftUnavailability,
    DisruptionAssessment,
    FlightImpact,
    ScheduleScenario,
)
from backend.app.services.scenario_generator import (
    MINIMUM_TURNAROUND_MINUTES,
)


def assess_aircraft_unavailability(
    scenario: ScheduleScenario,
    disruption: AircraftUnavailability,
    minimum_turnaround_minutes: int = MINIMUM_TURNAROUND_MINUTES,
) -> DisruptionAssessment:
    aircraft_ids = {
        aircraft.aircraft_id
        for aircraft in scenario.aircraft
    }

    if disruption.aircraft_id not in aircraft_ids:
        raise ValueError(
            (
                f"Disruption references unknown aircraft "
                f"{disruption.aircraft_id}."
            )
        )

    aircraft_flights = sorted(
        [
            flight
            for flight in scenario.flights
            if flight.aircraft_id
            == disruption.aircraft_id
        ],
        key=lambda flight:
        flight.scheduled_departure,
    )

    impacts: list[FlightImpact] = []

    previous_projected_arrival = None

    for flight in aircraft_flights:
        flight_duration = (
            flight.scheduled_arrival
            - flight.scheduled_departure
        )

        projected_departure = (
            flight.scheduled_departure
        )

        directly_affected = (
            disruption.start_time
            <= flight.scheduled_departure
            < disruption.end_time
        )

        if directly_affected:
            projected_departure = max(
                projected_departure,
                disruption.end_time,
            )

        if previous_projected_arrival is not None:
            earliest_turnaround_departure = (
                previous_projected_arrival
                + timedelta(
                    minutes=minimum_turnaround_minutes
                )
            )

            projected_departure = max(
                projected_departure,
                earliest_turnaround_departure,
            )

        if (
            disruption.start_time
            <= projected_departure
            < disruption.end_time
        ):
            projected_departure = (
                disruption.end_time
            )

        delay_minutes = int(
            (
                projected_departure
                - flight.scheduled_departure
            ).total_seconds()
            // 60
        )

        projected_arrival = (
            projected_departure
            + flight_duration
        )

        previous_projected_arrival = (
            projected_arrival
        )

        if delay_minutes > 0:
            impacts.append(
                FlightImpact(
                    flight_id=flight.flight_id,
                    flight_number=flight.flight_number,
                    aircraft_id=flight.aircraft_id,
                    scheduled_departure=(
                        flight.scheduled_departure
                    ),
                    scheduled_arrival=(
                        flight.scheduled_arrival
                    ),
                    projected_departure=(
                        projected_departure
                    ),
                    projected_arrival=(
                        projected_arrival
                    ),
                    delay_minutes=delay_minutes,
                    passengers=flight.passengers,
                    directly_affected=(
                        directly_affected
                    ),
                )
            )

    total_delay_minutes = sum(
        impact.delay_minutes
        for impact in impacts
    )

    passengers_affected = sum(
        impact.passengers
        for impact in impacts
    )

    directly_affected_flights = sum(
        impact.directly_affected
        for impact in impacts
    )

    maximum_delay_minutes = max(
        (
            impact.delay_minutes
            for impact in impacts
        ),
        default=0,
    )

    return DisruptionAssessment(
        disruption_id=(
            disruption.disruption_id
        ),
        aircraft_id=(
            disruption.aircraft_id
        ),
        impacts=impacts,
        impacted_flights=len(impacts),
        directly_affected_flights=(
            directly_affected_flights
        ),
        passengers_affected=(
            passengers_affected
        ),
        total_delay_minutes=(
            total_delay_minutes
        ),
        maximum_delay_minutes=(
            maximum_delay_minutes
        ),
    )