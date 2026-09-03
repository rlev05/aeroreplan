from pydantic import BaseModel, Field

class StrategyEmissions(BaseModel):
    strategy: str

    flights_considered: int = Field(ge=0)
    estimated_co2e_kg: float = Field(ge=0)
    change_vs_baseline_kg: float

class EmissionsComparison(BaseModel):
    baseline: StrategyEmissions
    greedy: StrategyEmissions
    optimized: StrategyEmissions

    emissions_weight: float = Field(ge=0)

