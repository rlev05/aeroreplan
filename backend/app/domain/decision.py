from pydantic import BaseModel, Field

class StrategyDecisionPoint(BaseModel):
    strategy: str
    expected_cost_gbp: float = Field(ge=0)
    cvar_cost_gbp: float = Field(ge=0)
    expected_delay_minutes: float = Field(ge=0)
    emissions_kg_co2e: float = Field(ge=0)
    is_pareto_optimal: bool = False


class DecisionWeights(BaseModel):
    expected_cost_weight: float = Field(
        default=1.0,
        ge=0)

    cvar_weight: float = Field(
        default=0.25,
        ge=0
    )

    delay_weight: float = Field(
        default=0.0,
        ge=0
    )

    emissions_weight: float = Field(
        default=0.0,
        ge=0
    )

class DecisionAnalysis(BaseModel):
    strategies: list[StrategyDecisionPoint]
    recommended_strategy: str
    pareto_strategies: list[str]

