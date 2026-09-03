from datetime import date
from sqlalchemy.orm import Session
from backend.app.domain import AircraftUnavailability, AnalysisCaseDetail, AnalysisCaseList, AnalysisCaseSummary, DecisionAnalysis, StrategyComparison
from backend.app.persistence.models import AnalysisCaseORM
from backend.app.persistence.repository import create_analysis_case, get_analysis_case, list_analysis_cases


def _to_summary(
        record: AnalysisCaseORM
) -> AnalysisCaseSummary:
    return AnalysisCaseSummary(
        case_id=record.case_id,
        created_at=record.created_at,
        operating_date=record.operating_date,
        disruption_id=record.disruption_id,
        aircraft_id=record.aircraft_id,
        recommended_strategy=record.recommended_strategy,
    )



def _to_detail(
        record: AnalysisCaseORM
) -> AnalysisCaseDetail:
    return AnalysisCaseDetail(
        case_id=record.case_id,
        created_at=record.created_at,
        operating_date=record.operating_date,
        seed=record.seed,
        disruption=AircraftUnavailability.model_validate(
            record.disruption_payload
        ),
        comparison=StrategyComparison.model_validate(
            record.comparison_payload
        ),
        decision=DecisionAnalysis.model_validate(
            record.decision_payload
        ),
        recommended_strategy=record.recommended_strategy,
    )

def save_analysis_case(
        session: Session,
        operating_date: date,
        seed: int,
        disruption: AircraftUnavailability,
        comparison: StrategyComparison,
        decision: DecisionAnalysis,
) -> AnalysisCaseDetail:
    record = create_analysis_case(
        session=session,
        operating_date=operating_date,
        seed=seed,
        disruption=disruption,
        comparison=comparison,
        decision=decision,
    )

    return _to_detail(record)

def load_analysis_case(
        session: Session,
        case_id: str
) -> AnalysisCaseDetail | None:
    record = get_analysis_case(
        session,
        case_id
    )

    if record is None:
        return None

    return _to_detail(record)


def load_analysis_case_list(
        session: Session,
        limit: int = 50,
) -> AnalysisCaseList:
    records = list_analysis_cases(
        session=session,
        limit=limit
    )

    summaries = [
        _to_summary(record)
        for record in records
    ]

    return AnalysisCaseList(
        cases=summaries,
        count=len(summaries)
    )

