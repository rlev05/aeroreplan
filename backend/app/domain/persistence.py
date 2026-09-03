from datetime import date, datetime
from pydantic import BaseModel, Field
from backend.app.domain.decision import DecisionAnalysis
from backend.app.domain.disruptions import AircraftUnavailability
from backend.app.domain.kpis import StrategyComparison

class AnalysisCaseSummary(BaseModel):
    case_id: str
    created_at: datetime
    operating_date: date
    disruption_id: str
    aircraft_id: str
    recommended_strategy: str


class AnalysisCaseDetail(BaseModel):
    case_id: str
    created_at: datetime
    operating_date: date
    seed: int
    disruption: AircraftUnavailability
    comparison: StrategyComparison
    decision: DecisionAnalysis
    recommended_strategy: str

class AnalysisCaseList(BaseModel):
    cases: list[AnalysisCaseSummary]
    count: int = Field(
        ge=0,
    )
