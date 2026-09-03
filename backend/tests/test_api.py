from fastapi.testclient import TestClient
from backend.app.main import app


client = TestClient(app)


def create_disruption_payload() -> dict:
    return {
        "operating_date": "2026-09-01",
        "seed": 42,
        "disruption": {
            "disruption_id": "DISRUPTION-001",
            "aircraft_id": "AC001",
            "start_time": (
                "2026-09-01T08:00:00Z"
            ),
            "end_time": (
                "2026-09-01T10:30:00Z"
            ),
            "reason": (
                "Aircraft technical issue"
            ),
        },
    }


def test_scenario_endpoint() -> None:
    response = client.get(
        "/api/scenario"
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["scenario_id"]
        == "SHORT-HAUL-2026-09-01"
    )

    assert len(
        payload["airports"]
    ) == 7

    assert len(
        payload["aircraft"]
    ) == 4

    assert len(
        payload["flights"]
    ) == 12


def test_disruption_assessment_endpoint() -> None:
    response = client.post(
        "/api/disruption/assess",
        json=create_disruption_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["total_delay_minutes"]
        == 310
    )

    assert (
        payload["impacted_flights"]
        == 3
    )


def test_greedy_recovery_endpoint() -> None:
    response = client.post(
        "/api/recovery/greedy",
        json=create_disruption_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload["strategy"]
        == "greedy_tail_reassignment"
    )

    assert (
        payload["total_delay_minutes"]
        == 115
    )

    assert (
        payload["reassigned_flights"]
        == 2
    )


def test_optimized_recovery_endpoint() -> None:
    payload = create_disruption_payload()

    payload["weights"] = {
        "delay_minute_cost": 1.0,
        "passenger_delay_minute_cost": 0.01,
        "reassignment_cost": 30.0,
        "emissions_cost_per_kg_co2e": 0.0,
    }

    response = client.post(
        "/api/recovery/optimize",
        json=payload,
    )

    assert response.status_code == 200

    result = response.json()

    assert (
        result["solver_status"]
        == "OPTIMAL"
    )

    assert (
        result["plan"][
            "total_delay_minutes"
        ]
        == 115
    )


def test_strategy_comparison_endpoint() -> None:
    response = client.post(
        "/api/analytics/compare",
        json=create_disruption_payload(),
    )

    assert response.status_code == 200

    payload = response.json()

    assert (
        payload[
            "baseline"
        ]["total_delay_minutes"]
        == 310
    )

    assert (
        payload[
            "optimized"
        ]["total_delay_minutes"]
        == 115
    )

    assert (
        payload[
            "estimated_savings_vs_baseline_gbp"
        ]
        > 0
    )


def test_monte_carlo_endpoint() -> None:
    payload = create_disruption_payload()

    payload["config"] = {
        "iterations": 10,
        "end_time_stddev_minutes": 30.0,
        "risk_confidence": 0.95,
        "severe_delay_threshold_minutes": 180,
        "seed": 42,
    }

    response = client.post(
        "/api/simulation/monte-carlo",
        json=payload,
    )

    assert response.status_code == 200

    result = response.json()

    assert result["iterations"] == 10

    assert len(
        result["samples"]
    ) == 10

    assert (
        result["baseline"][
            "conditional_value_at_risk_gbp"
        ]
        >= result["baseline"][
            "value_at_risk_gbp"
        ]
    )


def test_decision_analysis_endpoint() -> None:
    payload = create_disruption_payload()

    payload["config"] = {
        "iterations": 10,
        "end_time_stddev_minutes": 30.0,
        "risk_confidence": 0.95,
        "severe_delay_threshold_minutes": 180,
        "seed": 42,
    }

    payload["weights"] = {
        "expected_cost_weight": 1.0,
        "cvar_weight": 0.25,
        "delay_weight": 0.0,
        "emissions_weight": 0.0,
    }

    response = client.post(
        "/api/decision/analyze",
        json=payload,
    )

    assert response.status_code == 200

    result = response.json()

    assert len(
        result["strategies"]
    ) == 3

    assert (
        result["recommended_strategy"]
        in {
            "unrecovered_baseline",
            "greedy_tail_reassignment",
            "milp_recovery",
        }
    )

    assert len(
        result["pareto_strategies"]
    ) >= 1