from fastapi.testclient import TestClient
from backend.app.main import app

def _standard_disruption_request(
    client: TestClient,
) -> dict:
    scenario_response = client.get(
        "/api/scenario",
    )

    assert scenario_response.status_code == 200

    scenario = scenario_response.json()

    operating_date = (
        scenario["flights"][0]["scheduled_departure"][:10]
    )

    return {
        "operating_date": operating_date,
        "seed": 42,
        "disruption": {
            "disruption_id": "INTEGRATION-DISRUPTION",
            "aircraft_id": "AC001",
            "start_time": (
                f"{operating_date}T08:00:00Z"
            ),
            "end_time": (
                f"{operating_date}T10:30:00Z"
            ),
            "reason": "Integration test disruption",
        },
    }


def test_end_to_end_recovery_pipeline() -> None:
    with TestClient(app) as client:
        request = _standard_disruption_request(
            client,
        )

        assessment_response = client.post(
            "/api/disruption/assess",
            json=request,
        )

        greedy_response = client.post(
            "/api/recovery/greedy",
            json=request,
        )

        optimized_response = client.post(
            "/api/recovery/optimize",
            json=request,
        )

        comparison_response = client.post(
            "/api/analytics/compare",
            json=request,
        )

        decision_response = client.post(
            "/api/decision/analyze",
            json={
                **request,
                "config": {
                    "iterations": 20,
                    "end_time_stddev_minutes": 45,
                    "risk_confidence": 0.95,
                    "severe_delay_threshold_minutes": 180,
                    "seed": 42,
                },
                "weights": {
                    "expected_cost_weight": 1.0,
                    "cvar_weight": 0.25,
                    "delay_weight": 0.0,
                    "emissions_weight": 0.0,
                },
            },
        )

        assert assessment_response.status_code == 200
        assert greedy_response.status_code == 200
        assert optimized_response.status_code == 200
        assert comparison_response.status_code == 200
        assert decision_response.status_code == 200

        assessment = assessment_response.json()
        greedy = greedy_response.json()
        optimized = optimized_response.json()
        comparison = comparison_response.json()
        decision = decision_response.json()

        assert assessment["impacted_flights"] == 3
        assert assessment["total_delay_minutes"] == 310

        assert (
            greedy["total_delay_minutes"]
            <= assessment["total_delay_minutes"]
        )

        optimized_plan = optimized["plan"]

        assert (
            optimized_plan["total_delay_minutes"]
            <= assessment["total_delay_minutes"]
        )

        assert (
            optimized_plan["delay_reduction_minutes"]
            == assessment["total_delay_minutes"]
            - optimized_plan["total_delay_minutes"]
        )

        assert optimized["candidate_count"] >= 1

        assert optimized["solver_status"]

        assert (
            comparison["baseline"]["total_delay_minutes"]
            == assessment["total_delay_minutes"]
        )

        assert (
            comparison["optimized"]["total_delay_minutes"]
            == optimized_plan["total_delay_minutes"]
        )

        valid_strategies = {
            "unrecovered_baseline",
            "greedy_tail_reassignment",
            "milp_recovery",
        }

        assert (
            comparison["recommended_strategy"]
            in valid_strategies
        )

        assert (
            decision["recommended_strategy"]
            in valid_strategies
        )

        assert len(decision["strategies"]) == 3

        assert len(
            decision["pareto_strategies"],
        ) >= 1

        for strategy in decision["strategies"]:
            assert strategy["strategy"] in valid_strategies

            assert (
                strategy["expected_cost_gbp"]
                >= 0
            )

            assert (
                strategy["cvar_cost_gbp"]
                >= strategy["expected_cost_gbp"]
            )

            assert (
                strategy["expected_delay_minutes"]
                >= 0
            )


def test_recovery_pipeline_is_deterministic() -> None:
    with TestClient(app) as client:
        request = _standard_disruption_request(
            client,
        )

        first_response = client.post(
            "/api/recovery/optimize",
            json=request,
        )

        second_response = client.post(
            "/api/recovery/optimize",
            json=request,
        )

        assert first_response.status_code == 200
        assert second_response.status_code == 200

        first = first_response.json()
        second = second_response.json()

        assert (
            first["plan"]["total_delay_minutes"]
            == second["plan"]["total_delay_minutes"]
        )

        assert (
            first["plan"]["reassigned_flights"]
            == second["plan"]["reassigned_flights"]
        )

        assert (
            first["plan"]["flights"]
            == second["plan"]["flights"]
        )

