from datetime import datetime, timezone
from backend.app.domain import AircraftUnavailability, DecisionWeights, MonteCarloConfig
from backend.app.services.decision_engine import analyze_recovery_decisions
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


def test_decision_analysis_contains_three_strategies() -> None:
    scenario = generate_short_haul_scenario()

    result = analyze_recovery_decisions(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=20,
            seed=42,
        ),
    )

    assert len(result.strategies) == 3

    assert {
        strategy.strategy
        for strategy in result.strategies
    } == {
        "unrecovered_baseline",
        "greedy_tail_reassignment",
        "milp_recovery",
    }


def test_pareto_frontier_is_not_empty() -> None:
    scenario = generate_short_haul_scenario()

    result = analyze_recovery_decisions(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=20,
            seed=42,
        ),
    )

    assert len(
        result.pareto_strategies
    ) >= 1


def test_recommended_strategy_is_valid() -> None:
    scenario = generate_short_haul_scenario()

    result = analyze_recovery_decisions(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=20,
            seed=42,
        ),
    )

    assert (
        result.recommended_strategy
        in {
            strategy.strategy
            for strategy in result.strategies
        }
    )


def test_risk_averse_weighting_returns_recovery_strategy() -> None:
    scenario = generate_short_haul_scenario()

    result = analyze_recovery_decisions(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=40,
            seed=42,
        ),
        weights=DecisionWeights(
            expected_cost_weight=0.5,
            cvar_weight=1.0,
            delay_weight=0.0,
            emissions_weight=0.0,
        ),
    )

    assert (
        result.recommended_strategy
        in {
            "greedy_tail_reassignment",
            "milp_recovery",
        }
    )


def test_emissions_weight_can_change_decision() -> None:
    scenario = generate_short_haul_scenario()

    result = analyze_recovery_decisions(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=20,
            seed=42,
        ),
        weights=DecisionWeights(
            expected_cost_weight=0.0,
            cvar_weight=0.0,
            delay_weight=0.0,
            emissions_weight=1.0,
        ),
    )

    assert (
        result.recommended_strategy
        == "unrecovered_baseline"
    )


def test_pareto_flags_match_strategy_list() -> None:
    scenario = generate_short_haul_scenario()

    result = analyze_recovery_decisions(
        scenario,
        create_test_disruption(),
        config=MonteCarloConfig(
            iterations=20,
            seed=42,
        ),
    )

    flagged = {
        strategy.strategy
        for strategy in result.strategies
        if strategy.is_pareto_optimal
    }

    assert flagged == set(
        result.pareto_strategies
    )