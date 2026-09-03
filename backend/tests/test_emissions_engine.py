from datetime import datetime, timezone
import pytest
from backend.app.domain import AircraftType, AircraftUnavailability
from backend.app.optimization import OptimizationWeights, optimize_recovery
from backend.app.services.emissions import estimate_flight_emissions_kg
from backend.app.services.emissions_engine import compare_recovery_emissions
from backend.app.services.scenario_generator import generate_short_haul_scenario


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


def test_a321_emits_more_than_a320_in_model() -> None:
    a320 = estimate_flight_emissions_kg(
        500,
        AircraftType.AIRBUS_A320,
    )

    a321 = estimate_flight_emissions_kg(
        500,
        AircraftType.AIRBUS_A321,
    )

    assert a321 > a320


def test_reserve_aircraft_is_a321() -> None:
    scenario = generate_short_haul_scenario()

    reserve = next(
        aircraft
        for aircraft in scenario.aircraft
        if aircraft.aircraft_id == "AC004"
    )

    assert (
        reserve.aircraft_type
        == AircraftType.AIRBUS_A321
    )


def test_greedy_recovery_has_incremental_emissions() -> None:
    scenario = generate_short_haul_scenario()

    comparison = compare_recovery_emissions(
        scenario,
        create_test_disruption(),
    )

    assert (
        comparison.greedy.change_vs_baseline_kg
        > 0
    )


def test_default_optimizer_matches_recovery_emissions() -> None:
    scenario = generate_short_haul_scenario()

    comparison = compare_recovery_emissions(
        scenario,
        create_test_disruption(),
    )

    assert (
        comparison.optimized.change_vs_baseline_kg
        == pytest.approx(
            comparison.greedy.change_vs_baseline_kg
        )
    )


def test_high_emissions_weight_can_avoid_reassignment() -> None:
    scenario = generate_short_haul_scenario()

    result = optimize_recovery(
        scenario,
        create_test_disruption(),
        weights=OptimizationWeights(
            emissions_cost_per_kg_co2e=10.0,
        ),
    )

    assert result.plan.reassigned_flights == 0

    assert (
        result.incremental_emissions_kg_co2e
        == pytest.approx(0.0)
    )


