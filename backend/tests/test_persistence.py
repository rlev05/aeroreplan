from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.domain import AircraftUnavailability, MonteCarloConfig
from backend.app.persistence import Base, create_database_engine, create_session_factory, load_analysis_case, load_analysis_case_list, save_analysis_case
from backend.app.services.decision_engine import analyze_recovery_decisions
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


def create_test_session(
    tmp_path,
) -> Session:
    database_path = (
        tmp_path
        / "test-aeroreplan.db"
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

    return session_factory()


def create_analysis_outputs():
    scenario = generate_short_haul_scenario()

    disruption = (
        create_test_disruption()
    )

    comparison = (
        compare_recovery_strategies(
            scenario,
            disruption,
        )
    )

    decision = (
        analyze_recovery_decisions(
            scenario,
            disruption,
            config=MonteCarloConfig(
                iterations=5,
                seed=42,
            ),
        )
    )

    return (
        disruption,
        comparison,
        decision,
    )


def test_saves_and_loads_analysis_case(
    tmp_path,
) -> None:
    session = create_test_session(
        tmp_path
    )

    try:
        (
            disruption,
            comparison,
            decision,
        ) = create_analysis_outputs()

        saved = save_analysis_case(
            session=session,
            operating_date=(
                disruption.start_time.date()
            ),
            seed=42,
            disruption=disruption,
            comparison=comparison,
            decision=decision,
        )

        loaded = load_analysis_case(
            session,
            saved.case_id,
        )

        assert loaded is not None

        assert (
            loaded.case_id
            == saved.case_id
        )

        assert (
            loaded.disruption.disruption_id
            == "DISRUPTION-001"
        )

        assert (
            loaded.comparison.baseline.total_delay_minutes
            == 310
        )
    finally:
        session.close()


def test_preserves_decision_analysis(
    tmp_path,
) -> None:
    session = create_test_session(
        tmp_path
    )

    try:
        (
            disruption,
            comparison,
            decision,
        ) = create_analysis_outputs()

        saved = save_analysis_case(
            session=session,
            operating_date=(
                disruption.start_time.date()
            ),
            seed=42,
            disruption=disruption,
            comparison=comparison,
            decision=decision,
        )

        loaded = load_analysis_case(
            session,
            saved.case_id,
        )

        assert loaded is not None

        assert (
            loaded.decision.recommended_strategy
            == decision.recommended_strategy
        )

        assert (
            loaded.decision.pareto_strategies
            == decision.pareto_strategies
        )
    finally:
        session.close()


def test_lists_saved_analysis_cases(
    tmp_path,
) -> None:
    session = create_test_session(
        tmp_path
    )

    try:
        (
            disruption,
            comparison,
            decision,
        ) = create_analysis_outputs()

        saved = save_analysis_case(
            session=session,
            operating_date=(
                disruption.start_time.date()
            ),
            seed=42,
            disruption=disruption,
            comparison=comparison,
            decision=decision,
        )

        result = load_analysis_case_list(
            session
        )

        assert result.count == 1

        assert (
            result.cases[0].case_id
            == saved.case_id
        )

        assert (
            result.cases[
                0
            ].recommended_strategy
            == decision.recommended_strategy
        )
    finally:
        session.close()


def test_missing_case_returns_none(
    tmp_path,
) -> None:
    session = create_test_session(
        tmp_path
    )

    try:
        result = load_analysis_case(
            session,
            "missing-case-id",
        )

        assert result is None
    finally:
        session.close()