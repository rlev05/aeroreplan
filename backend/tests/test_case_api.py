from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.persistence import Base, create_database_engine, create_session_factory, get_database_session

def create_case_payload() -> dict:
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
        "config": {
            "iterations": 5,
            "end_time_stddev_minutes": 30.0,
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
    }


def create_test_client(
    tmp_path,
) -> TestClient:
    database_path = (
        tmp_path
        / "case-api.db"
    )

    engine = create_database_engine(
        f"sqlite:///{database_path}"
    )

    Base.metadata.create_all(
        engine
    )

    session_factory = (
        create_session_factory(
            engine
        )
    )

    def override_database_session():
        session: Session = (
            session_factory()
        )

        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[
        get_database_session
    ] = override_database_session

    return TestClient(
        app
    )


def test_analyzes_and_saves_case(
    tmp_path,
) -> None:
    client = create_test_client(
        tmp_path
    )

    try:
        response = client.post(
            "/api/cases/analyze",
            json=create_case_payload(),
        )

        assert response.status_code == 201

        payload = response.json()

        assert payload["case_id"]

        assert (
            payload["disruption"][
                "disruption_id"
            ]
            == "DISRUPTION-001"
        )

        assert (
            payload["comparison"][
                "baseline"
            ]["total_delay_minutes"]
            == 310
        )

        assert (
            payload["recommended_strategy"]
            == payload["decision"][
                "recommended_strategy"
            ]
        )

    finally:
        app.dependency_overrides.clear()


def test_lists_saved_cases(
    tmp_path,
) -> None:
    client = create_test_client(
        tmp_path
    )

    try:
        create_response = client.post(
            "/api/cases/analyze",
            json=create_case_payload(),
        )

        assert (
            create_response.status_code
            == 201
        )

        response = client.get(
            "/api/cases"
        )

        assert response.status_code == 200

        payload = response.json()

        assert payload["count"] == 1

        assert len(
            payload["cases"]
        ) == 1

        assert (
            payload["cases"][0][
                "disruption_id"
            ]
            == "DISRUPTION-001"
        )

    finally:
        app.dependency_overrides.clear()


def test_retrieves_saved_case(
    tmp_path,
) -> None:
    client = create_test_client(
        tmp_path
    )

    try:
        create_response = client.post(
            "/api/cases/analyze",
            json=create_case_payload(),
        )

        created = (
            create_response.json()
        )

        case_id = created[
            "case_id"
        ]

        response = client.get(
            f"/api/cases/{case_id}"
        )

        assert response.status_code == 200

        payload = response.json()

        assert (
            payload["case_id"]
            == case_id
        )

        assert (
            payload["seed"]
            == 42
        )

    finally:
        app.dependency_overrides.clear()


def test_missing_case_returns_404(
    tmp_path,
) -> None:
    client = create_test_client(
        tmp_path
    )

    try:
        response = client.get(
            "/api/cases/missing-case"
        )

        assert response.status_code == 404

        assert response.json() == {
            "detail": (
                "Analysis case not found."
            )
        }

    finally:
        app.dependency_overrides.clear()


