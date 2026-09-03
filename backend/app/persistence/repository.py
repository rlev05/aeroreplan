from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.domain import AircraftUnavailability, DecisionAnalysis, StrategyComparison
from backend.app.persistence.models import AnalysisCaseORM

def create_analysis_case(
        session: Session,
        operating_date: date,
        seed: int,
        disruption: AircraftUnavailability,
        comparison: StrategyComparison,
        decision: DecisionAnalysis,
) -> AnalysisCaseORM:
    record = AnalysisCaseORM(
        operating_date=operating_date,
        seed=seed,
        disruption_id=(
            disruption.disruption_id
        ),
        aircraft_id=(
            disruption.aircraft_id
        ),
        recommended_strategy=(
            decision.recommended_strategy
        ),
        disruption_payload=(
            disruption.model_dump(
                mode="json"
            )
        ),
        comparison_payload=(
            comparison.model_dump(
                mode="json"
            )
        ),
        decision_payload=(
            decision.model_dump(
                mode="json"
            )
        ),
    )

    session.add(
        record
    )

    session.commit()

    session.refresh(
        record
    )

    return record


def get_analysis_case(
        session: Session,
        case_id: str,
) -> AnalysisCaseORM | None:
    return session.get(
        AnalysisCaseORM,
        case_id,
    )


def list_analysis_cases(
        session: Session,
        limit: int = 50,
) -> list[AnalysisCaseORM]:
    statement = (
        select(
            AnalysisCaseORM
        )
        .order_by(
            AnalysisCaseORM.created_at.desc()
        )
        .limit(
            limit
        )
    )

    return list(
        session.scalars(
            statement
        )
    )


