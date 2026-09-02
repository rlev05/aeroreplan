from datetime import datetime, timedelta
from backend.app.domain import Aircraft, AircraftUnavailability, Flight, RecoveredFlight, RecoveryActionType, RecoveryPlan, ScheduleScenario
from backend.app.services.disruption_engine import assess_aircraft_unavailability
from backend.app.services.scenario_generator import MINIMUM_TURNAROUND_MINUTES


def _aircraft_can_operate_flights(
    aircraft: Aircraft,
    proposed_flights: list[Flight],
    scenario: ScheduleScenario,
    minimum_turnaround_minutes: int,
) -> bool:
    for flight in proposed_flights:
        if flight.passengers > aircraft.seat_capacity:
            return False

    existing_flights = [
        flight
        for flight in scenario.flights
        if flight.aircraft_id == aircraft.aircraft_id
    ]

    combined_schedule = sorted(
        [
            *existing_flights,
            *proposed_flights,
        ],
        key=lambda flight: flight.scheduled_departure,
    )

    if not combined_schedule:
        return True

    if combined_schedule[0].origin != aircraft.home_airport:
        return False

    turnaround = timedelta(
        minutes=minimum_turnaround_minutes
    )

    for previous, current in zip(
        combined_schedule,
        combined_schedule[1:],
    ):
        if previous.destination != current.origin:
            return False

        earliest_departure = (
            previous.scheduled_arrival
            + turnaround
        )

        if (
            current.scheduled_departure
            < earliest_departure
        ):
            return False

    return True


def _find_recovery_aircraft(
    scenario: ScheduleScenario,
    disrupted_aircraft_id: str,
    proposed_flights: list[Flight],
    minimum_turnaround_minutes: int,
) -> Aircraft | None:
    candidates = [
        aircraft
        for aircraft in scenario.aircraft
        if aircraft.aircraft_id
        != disrupted_aircraft_id
    ]

    feasible_candidates = [
        aircraft
        for aircraft in candidates
        if _aircraft_can_operate_flights(
            aircraft=aircraft,
            proposed_flights=proposed_flights,
            scenario=scenario,
            minimum_turnaround_minutes=(
                minimum_turnaround_minutes
            ),
        )
    ]

    if not feasible_candidates:
        return None

    return min(
        feasible_candidates,
        key=lambda aircraft:
        aircraft.seat_capacity,
    )


def generate_greedy_recovery(
    scenario: ScheduleScenario,
    disruption: AircraftUnavailability,
    minimum_turnaround_minutes: int = (
        MINIMUM_TURNAROUND_MINUTES
    ),
) -> RecoveryPlan:
    baseline = assess_aircraft_unavailability(
        scenario=scenario,
        disruption=disruption,
        minimum_turnaround_minutes=(
            minimum_turnaround_minutes
        ),
    )

    impacted_flight_ids = {
        impact.flight_id
        for impact in baseline.impacts
    }

    impacted_flights = sorted(
        [
            flight
            for flight in scenario.flights
            if flight.flight_id
            in impacted_flight_ids
        ],
        key=lambda flight:
        flight.scheduled_departure,
    )

    baseline_by_flight = {
        impact.flight_id: impact
        for impact in baseline.impacts
    }

    recovery_start_index: int | None = None
    recovery_aircraft: Aircraft | None = None

    for index in range(
        len(impacted_flights)
    ):
        proposed_tail = impacted_flights[
            index:
        ]

        candidate = _find_recovery_aircraft(
            scenario=scenario,
            disrupted_aircraft_id=(
                disruption.aircraft_id
            ),
            proposed_flights=proposed_tail,
            minimum_turnaround_minutes=(
                minimum_turnaround_minutes
            ),
        )

        if candidate is not None:
            recovery_start_index = index
            recovery_aircraft = candidate
            break

    recovered_flights: list[RecoveredFlight] = []

    for index, flight in enumerate(
        impacted_flights
    ):
        baseline_impact = baseline_by_flight[
            flight.flight_id
        ]

        should_reassign = (
            recovery_start_index is not None
            and recovery_aircraft is not None
            and index >= recovery_start_index
        )

        if should_reassign:
            recovered_flights.append(
                RecoveredFlight(
                    flight_id=flight.flight_id,
                    flight_number=(
                        flight.flight_number
                    ),
                    origin=flight.origin,
                    destination=flight.destination,
                    original_aircraft_id=(
                        flight.aircraft_id
                    ),
                    assigned_aircraft_id=(
                        recovery_aircraft.aircraft_id
                    ),
                    scheduled_departure=(
                        flight.scheduled_departure
                    ),
                    scheduled_arrival=(
                        flight.scheduled_arrival
                    ),
                    projected_departure=(
                        flight.scheduled_departure
                    ),
                    projected_arrival=(
                        flight.scheduled_arrival
                    ),
                    passengers=flight.passengers,
                    delay_minutes=0,
                    action=(
                        RecoveryActionType.REASSIGN
                    ),
                )
            )

        else:
            recovered_flights.append(
                RecoveredFlight(
                    flight_id=flight.flight_id,
                    flight_number=(
                        flight.flight_number
                    ),
                    origin=flight.origin,
                    destination=flight.destination,
                    original_aircraft_id=(
                        flight.aircraft_id
                    ),
                    assigned_aircraft_id=(
                        flight.aircraft_id
                    ),
                    scheduled_departure=(
                        flight.scheduled_departure
                    ),
                    scheduled_arrival=(
                        flight.scheduled_arrival
                    ),
                    projected_departure=(
                        baseline_impact.projected_departure
                    ),
                    projected_arrival=(
                        baseline_impact.projected_arrival
                    ),
                    passengers=flight.passengers,
                    delay_minutes=(
                        baseline_impact.delay_minutes
                    ),
                    action=(
                        RecoveryActionType.DELAY
                    ),
                )
            )

    total_delay_minutes = sum(
        flight.delay_minutes
        for flight in recovered_flights
    )

    passengers_affected = sum(
        flight.passengers
        for flight in recovered_flights
        if flight.delay_minutes > 0
    )

    reassigned_flights = sum(
        flight.action
        == RecoveryActionType.REASSIGN
        for flight in recovered_flights
    )

    delay_reduction_minutes = (
        baseline.total_delay_minutes
        - total_delay_minutes
    )

    passengers_recovered = max(
        0,
        baseline.passengers_affected
        - passengers_affected,
    )

    return RecoveryPlan(
        strategy="greedy_tail_reassignment",
        disruption_id=(
            disruption.disruption_id
        ),
        flights=recovered_flights,
        baseline_total_delay_minutes=(
            baseline.total_delay_minutes
        ),
        total_delay_minutes=(
            total_delay_minutes
        ),
        delay_reduction_minutes=(
            delay_reduction_minutes
        ),
        baseline_passengers_affected=(
            baseline.passengers_affected
        ),
        passengers_affected=(
            passengers_affected
        ),
        passengers_recovered=(
            passengers_recovered
        ),
        reassigned_flights=(
            reassigned_flights
        ),
    )