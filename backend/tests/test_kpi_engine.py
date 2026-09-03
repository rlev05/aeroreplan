from datetime import datetime, timezone
import pytest
from backend.app.domain import AircraftUnavailability, RecoveryCostAssumptions
from backend.app.services.kpi_engine import compare_recovery_strategies
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


def test_comparison_contains_all_strategies() -> None:
    scenario = generate_short_haul_scenario()

    comparison = compare_recovery_strategies(
        scenario,
        create_test_disruption(),
    )

    assert (
        comparison.baseline.strategy
        == "unrecovered_baseline"
    )

    assert (
        comparison.greedy.strategy
        == "greedy_tail_reassignment"
    )

    assert (
        comparison.optimized.strategy
        == "milp_recovery"
    )


def test_recovery_strategies_reduce_delay() -> None:
    scenario = generate_short_haul_scenario()

    comparison = compare_recovery_strategies(
        scenario,
        create_test_disruption(),
    )

    assert (
        comparison.baseline.total_delay_minutes
        == 310
    )

    assert (
        comparison.greedy.total_delay_minutes
        == 115
    )

    assert (
        comparison.optimized.total_delay_minutes
        == 115
    )

    assert (
        comparison.optimized.delay_reduction_percent
        == pytest.approx(
            62.9,
            abs=0.01,
        )
    )


def test_recovery_reduces_passenger_delay() -> None:
    scenario = generate_short_haul_scenario()

    comparison = compare_recovery_strategies(
        scenario,
        create_test_disruption(),
    )

    assert (
        comparison.greedy.passenger_delay_minutes
        < comparison.baseline.passenger_delay_minutes
    )

    assert (
        comparison.optimized.passenger_delay_minutes
        < comparison.baseline.passenger_delay_minutes
    )

    assert (
        comparison.optimized.passenger_recovery_percent
        > 0
    )


def test_cost_components_sum_to_total() -> None:
    scenario = generate_short_haul_scenario()

    comparison = compare_recovery_strategies(
        scenario,
        create_test_disruption(),
    )

    optimized = comparison.optimized

    expected_total = (
        optimized.operational_delay_cost_gbp
        + optimized.passenger_delay_cost_gbp
        + optimized.reassignment_cost_gbp
    )

    assert (
        optimized.total_estimated_cost_gbp
        == pytest.approx(
            expected_total
        )
    )


def test_default_recommendation_is_optimized_recovery() -> None:
    scenario = generate_short_haul_scenario()

    comparison = compare_recovery_strategies(
        scenario,
        create_test_disruption(),
    )

    assert (
        comparison.recommended_strategy
        == "milp_recovery"
    )

    assert (
        comparison.estimated_savings_vs_baseline_gbp
        > 0
    )


def test_high_reassignment_cost_changes_optimizer_decision() -> None:
    scenario = generate_short_haul_scenario()

    assumptions = RecoveryCostAssumptions(
        operational_delay_cost_per_minute_gbp=75.0,
        passenger_delay_cost_per_minute_gbp=0.20,
        aircraft_reassignment_cost_gbp=100_000.0,
    )

    comparison = compare_recovery_strategies(
        scenario,
        create_test_disruption(),
        assumptions=assumptions,
    )

    assert (
        comparison.optimized.reassigned_flights
        == 0
    )

    assert (
        comparison.optimized.total_delay_minutes
        == 310
    )


def test_zero_impact_disruption_has_zero_cost() -> None:
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

    comparison = compare_recovery_strategies(
        scenario,
        disruption,
    )

    assert (
        comparison.baseline.total_estimated_cost_gbp
        == 0
    )

    assert (
        comparison.greedy.total_estimated_cost_gbp
        == 0
    )

    assert (
        comparison.optimized.total_estimated_cost_gbp
        == 0
    )

    assert (
        comparison.estimated_savings_vs_baseline_gbp
        == 0
    )