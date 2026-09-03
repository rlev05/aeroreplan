from dataclasses import dataclass
from datetime import timedelta
from time import perf_counter
from ortools.linear_solver import pywraplp
from pydantic import BaseModel, Field

from backend.app.domain import Aircraft, AircraftUnavailability, Flight, RecoveredFlight, RecoveryActionType, RecoveryPlan, ScheduleScenario
from backend.app.services.disruption_engine import assess_aircraft_unavailability
from backend.app.services import MINIMUM_TURNAROUND_MINUTES

class OptimizationWeights(BaseModel):
    delay_minute_cost: float = Field(
        default=1.0,
        ge=0,
    )

    passenger_delay_minute_cost: float = Field(
        default=0.01,
        ge=0,
    )

    reassignment_cost: float = Field(
        default=30.0,
        ge=0,
    )


class MILPRecoveryResult(BaseModel):
    plan: RecoveryPlan

    solver_status: str
    objective_value: float = Field(ge=0)

    solve_time_ms: float = Field(ge=0)
    candidate_count: int = Field(ge=1)


@dataclass(frozen=True)
class _RecoveryCandidate:
    recovery_aircraft_id: str | None
    recovery_start_index: int | None

    total_delay_minutes: int
    passenger_delay_minutes: int
    reassigned_flights: int


def _aircraft_can_operate_tail(
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
        key=lambda flight:
        flight.scheduled_departure,
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


def _create_candidates(
    scenario: ScheduleScenario,
    disruption: AircraftUnavailability,
    minimum_turnaround_minutes: int,
) -> tuple[
    list[_RecoveryCandidate],
    list[Flight],
    dict,
]:
    baseline = assess_aircraft_unavailability(
        scenario=scenario,
        disruption=disruption,
        minimum_turnaround_minutes=(
            minimum_turnaround_minutes
        ),
    )

    baseline_by_flight = {
        impact.flight_id: impact
        for impact in baseline.impacts
    }

    impacted_flight_ids = set(
        baseline_by_flight
    )

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

    baseline_passenger_delay = sum(
        impact.passengers
        * impact.delay_minutes
        for impact in baseline.impacts
    )

    candidates = [
        _RecoveryCandidate(
            recovery_aircraft_id=None,
            recovery_start_index=None,
            total_delay_minutes=(
                baseline.total_delay_minutes
            ),
            passenger_delay_minutes=(
                baseline_passenger_delay
            ),
            reassigned_flights=0,
        )
    ]

    recovery_aircraft = [
        aircraft
        for aircraft in scenario.aircraft
        if aircraft.aircraft_id
        != disruption.aircraft_id
    ]

    for start_index in range(
        len(impacted_flights)
    ):
        proposed_tail = impacted_flights[
            start_index:
        ]

        preceding_flights = impacted_flights[
            :start_index
        ]

        preceding_impacts = [
            baseline_by_flight[
                flight.flight_id
            ]
            for flight in preceding_flights
        ]

        retained_delay = sum(
            impact.delay_minutes
            for impact in preceding_impacts
        )

        retained_passenger_delay = sum(
            impact.passengers
            * impact.delay_minutes
            for impact in preceding_impacts
        )

        for aircraft in recovery_aircraft:
            feasible = (
                _aircraft_can_operate_tail(
                    aircraft=aircraft,
                    proposed_flights=proposed_tail,
                    scenario=scenario,
                    minimum_turnaround_minutes=(
                        minimum_turnaround_minutes
                    ),
                )
            )

            if not feasible:
                continue

            candidates.append(
                _RecoveryCandidate(
                    recovery_aircraft_id=(
                        aircraft.aircraft_id
                    ),
                    recovery_start_index=(
                        start_index
                    ),
                    total_delay_minutes=(
                        retained_delay
                    ),
                    passenger_delay_minutes=(
                        retained_passenger_delay
                    ),
                    reassigned_flights=len(
                        proposed_tail
                    ),
                )
            )

    return (
        candidates,
        impacted_flights,
        baseline_by_flight,
    )


def _create_solver() -> pywraplp.Solver:
    solver = pywraplp.Solver.CreateSolver(
        "SCIP"
    )

    if solver is None:
        solver = pywraplp.Solver.CreateSolver(
            "CBC_MIXED_INTEGER_PROGRAMMING"
        )

    if solver is None:
        raise RuntimeError(
            "No compatible OR-Tools MILP solver is available."
        )

    return solver


def _solver_status_name(
    status: int,
) -> str:
    status_names = {
        pywraplp.Solver.OPTIMAL: "OPTIMAL",
        pywraplp.Solver.FEASIBLE: "FEASIBLE",
        pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
        pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
        pywraplp.Solver.ABNORMAL: "ABNORMAL",
        pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED",
    }

    return status_names.get(
        status,
        "UNKNOWN",
    )


def optimize_recovery(
    scenario: ScheduleScenario,
    disruption: AircraftUnavailability,
    weights: OptimizationWeights | None = None,
    minimum_turnaround_minutes: int = (
        MINIMUM_TURNAROUND_MINUTES
    ),
) -> MILPRecoveryResult:
    if weights is None:
        weights = OptimizationWeights()

    baseline = assess_aircraft_unavailability(
        scenario=scenario,
        disruption=disruption,
        minimum_turnaround_minutes=(
            minimum_turnaround_minutes
        ),
    )

    (
        candidates,
        impacted_flights,
        baseline_by_flight,
    ) = _create_candidates(
        scenario=scenario,
        disruption=disruption,
        minimum_turnaround_minutes=(
            minimum_turnaround_minutes
        ),
    )

    solver = _create_solver()

    candidate_selected = [
        solver.BoolVar(
            f"candidate_{index}"
        )
        for index in range(
            len(candidates)
        )
    ]

    solver.Add(
        sum(candidate_selected) == 1
    )

    total_delay = solver.NumVar(
        0,
        solver.infinity(),
        "total_delay_minutes",
    )

    passenger_delay = solver.NumVar(
        0,
        solver.infinity(),
        "passenger_delay_minutes",
    )

    reassignment_count = solver.NumVar(
        0,
        solver.infinity(),
        "reassignment_count",
    )

    solver.Add(
        total_delay
        == sum(
            candidate.total_delay_minutes
            * candidate_selected[index]
            for index, candidate
            in enumerate(candidates)
        )
    )

    solver.Add(
        passenger_delay
        == sum(
            candidate.passenger_delay_minutes
            * candidate_selected[index]
            for index, candidate
            in enumerate(candidates)
        )
    )

    solver.Add(
        reassignment_count
        == sum(
            candidate.reassigned_flights
            * candidate_selected[index]
            for index, candidate
            in enumerate(candidates)
        )
    )

    objective = (
        weights.delay_minute_cost
        * total_delay
        + weights.passenger_delay_minute_cost
        * passenger_delay
        + weights.reassignment_cost
        * reassignment_count
    )

    solver.Minimize(objective)

    start_time = perf_counter()

    status = solver.Solve()

    solve_time_ms = (
        perf_counter() - start_time
    ) * 1000

    if status not in {
        pywraplp.Solver.OPTIMAL,
        pywraplp.Solver.FEASIBLE,
    }:
        raise RuntimeError(
            (
                "Recovery optimisation failed with "
                f"status {_solver_status_name(status)}."
            )
        )

    selected_index = max(
        range(len(candidates)),
        key=lambda index:
        candidate_selected[
            index
        ].solution_value(),
    )

    selected = candidates[
        selected_index
    ]

    recovered_flights: list[
        RecoveredFlight
    ] = []

    for index, flight in enumerate(
        impacted_flights
    ):
        baseline_impact = baseline_by_flight[
            flight.flight_id
        ]

        is_reassigned = (
            selected.recovery_start_index
            is not None
            and selected.recovery_aircraft_id
            is not None
            and index
            >= selected.recovery_start_index
        )

        if is_reassigned:
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
                        selected.recovery_aircraft_id
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
                    passengers=(
                        flight.passengers
                    ),
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
                    passengers=(
                        flight.passengers
                    ),
                    delay_minutes=(
                        baseline_impact.delay_minutes
                    ),
                    action=(
                        RecoveryActionType.DELAY
                    ),
                )
            )

    passengers_affected = sum(
        flight.passengers
        for flight in recovered_flights
        if flight.delay_minutes > 0
    )

    passengers_recovered = max(
        0,
        baseline.passengers_affected
        - passengers_affected,
    )

    plan = RecoveryPlan(
        strategy="milp_recovery",
        disruption_id=(
            disruption.disruption_id
        ),
        flights=recovered_flights,
        baseline_total_delay_minutes=(
            baseline.total_delay_minutes
        ),
        total_delay_minutes=(
            selected.total_delay_minutes
        ),
        delay_reduction_minutes=(
            baseline.total_delay_minutes
            - selected.total_delay_minutes
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
            selected.reassigned_flights
        ),
    )

    return MILPRecoveryResult(
        plan=plan,
        solver_status=(
            _solver_status_name(status)
        ),
        objective_value=(
            solver.Objective().Value()
        ),
        solve_time_ms=(
            solve_time_ms
        ),
        candidate_count=len(
            candidates
        ),
    )