from datetime import datetime, timezone
import pytest
from backend.app.domain import AircraftUnavailability, MonteCarloConfig
from backend.app.services.scenario_generator import generate_short_haul_scenario
from backend.app.simulation import simulate_disruption_uncertainty


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


def test_monte_carlo_is_reproducible() -> None:
    scenario = generate_short_haul_scenario()

    config = MonteCarloConfig(
        iterations=30,
        seed=123,
    )

    first = simulate_disruption_uncertainty(
        scenario,
        create_test_disruption(),
        config=config,
    )

    second = simulate_disruption_uncertainty(
        scenario,
        create_test_disruption(),
        config=config,
    )

    first_times = [
        sample.disruption_end_time
        for sample in first.samples
    ]

    second_times = [
        sample.disruption_end_time
        for sample in second.samples
    ]

    assert first_times == second_times


def test_different_seed_changes_simulated_outcomes() -> None:
    scenario = generate_short_haul_scenario()

    first = simulate_disruption_uncertainty(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=20,
            seed=1,
        ),
    )

    second = simulate_disruption_uncertainty(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=20,
            seed=2,
        ),
    )

    assert [
        sample.disruption_end_time
        for sample in first.samples
    ] != [
        sample.disruption_end_time
        for sample in second.samples
    ]


def test_zero_uncertainty_matches_deterministic_case() -> None:
    scenario = generate_short_haul_scenario()

    result = simulate_disruption_uncertainty(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=20,
            end_time_stddev_minutes=0.0,
        ),
    )

    assert (
        result.baseline.mean_delay_minutes
        == pytest.approx(310.0)
    )

    assert (
        result.greedy.mean_delay_minutes
        == pytest.approx(115.0)
    )

    assert (
        result.optimized.mean_delay_minutes
        == pytest.approx(115.0)
    )


def test_cvar_is_at_least_value_at_risk() -> None:
    scenario = generate_short_haul_scenario()

    result = simulate_disruption_uncertainty(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=50,
            seed=42,
        ),
    )

    for strategy in [
        result.baseline,
        result.greedy,
        result.optimized,
    ]:
        assert (
            strategy.conditional_value_at_risk_gbp
            >= strategy.value_at_risk_gbp
        )


def test_p95_delay_is_at_least_p90_delay() -> None:
    scenario = generate_short_haul_scenario()

    result = simulate_disruption_uncertainty(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=50,
            seed=42,
        ),
    )

    for strategy in [
        result.baseline,
        result.greedy,
        result.optimized,
    ]:
        assert (
            strategy.p95_delay_minutes
            >= strategy.p90_delay_minutes
        )


def test_sampled_end_times_remain_after_disruption_start() -> None:
    scenario = generate_short_haul_scenario()

    disruption = create_test_disruption()

    result = simulate_disruption_uncertainty(
        scenario,
        disruption,
        config=MonteCarloConfig(
            iterations=50,
            end_time_stddev_minutes=120.0,
            seed=7,
        ),
    )

    assert all(
        sample.disruption_end_time
        > disruption.start_time
        for sample in result.samples
    )


def test_simulation_exposes_requested_number_of_samples() -> None:
    scenario = generate_short_haul_scenario()

    result = simulate_disruption_uncertainty(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=40,
        ),
    )

    assert result.iterations == 40
    assert len(result.samples) == 40


