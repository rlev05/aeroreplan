from datetime import date
from pydantic import BaseModel, Field
from backend.app.domain import AircraftUnavailability, DecisionWeights, MonteCarloConfig, RecoveryCostAssumptions
from backend.app.optimization import OptimizationWeights

class ScenarioParameters(BaseModel):
    operating_date: date = date(
        2026,
        9,
        1
    )

    seed: int = 42

class DisruptionRequest(ScenarioParameters):
    disruption: AircraftUnavailability

class OptimizationRequest(DisruptionRequest):
    weights: OptimizationWeights | None = None

class StrategyComparisonRequest(DisruptionRequest):
    assumptions: RecoveryCostAssumptions | None = None

class SimulationRequest(DisruptionRequest):
    config: MonteCarloConfig = Field(
        default_factory=MonteCarloConfig,
    )

    assumptions: RecoveryCostAssumptions | None = None

class DecisionRequest(DisruptionRequest):
    config: MonteCarloConfig = Field(
        default_factory=lambda: MonteCarloConfig(
            iterations=100
        )
    )

    assumptions: RecoveryCostAssumptions | None = None

    weights: DecisionWeights = Field(
        default_factory=DecisionWeights
    )


class SaveAnalysisCaseRequest(DecisionRequest):
    pass
