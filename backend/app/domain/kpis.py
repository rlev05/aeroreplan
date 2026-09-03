from pydantic import BaseModel, Field


class RecoveryCostAssumptions(BaseModel):
    operational_delay_cost_per_minute_gbp: float = Field(
        default=75.0,
        ge=0
    )

    passenger_delay_cost_per_minute_gbp: float = Field(
        default=0.20,
        ge=0
    )

    aircraft_reassignment_cost_gbp: float = Field(
        default=400.0,
        ge=0
    )

class StrategyKPIs(BaseModel):
    strategy: str
    flights_considered: int = Field(ge=0)
    delayed_flights: int = Field(ge=0)
    on_time_flights: int = Field(ge=0)
    passengers_affected: int = Field(ge=0)
    passenger_delay_minutes: int = Field(ge=0)
    total_delay_minutes: int = Field(ge=0)
    average_delay_minutes: float = Field(ge=0)
    maximum_delay_minutes: int = Field(ge=0)
    reassigned_flights: int = Field(ge=0)
    delay_reduction_percent: float = Field(ge=0,
                                           le=100)
    passenger_recovery_percent: float = Field(ge=0,
                                              le=100)
    on_time_recovery_rate_percent: float = Field(ge=0,
                                                 le=100)
    operational_delay_cost_gbp: float = Field(ge=0)
    passenger_delay_cost_gbp: float = Field(ge=0)
    reassignment_cost_gbp: float = Field(ge=0)
    total_estimated_cost_gbp: float = Field(ge=0)

class StrategyComparison(BaseModel):
    baseline: StrategyKPIs
    greedy: StrategyKPIs
    optimized: StrategyKPIs

    recommended_strategy: str
    estimated_savings_vs_baseline_gbp: float = Field(ge=0)

