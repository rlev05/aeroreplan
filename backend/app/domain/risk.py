from datetime import datetime
from pydantic import BaseModel, Field

class MonteCarloConfig(BaseModel):
    iterations: int = Field(
        default=250,
        ge=1,
        le=10_000,
    )

    end_time_stddev_minutes: float = Field(
        default=45.0,
        ge=0,
        le=240
    )

    risk_confidence: float = Field(
        default=0.95,
        gt=0.5,
        lt=1.0
    )

    severe_delay_threshold_minutes: int = Field(
        default=180,
        ge=0,
    )

    seed: int = 42


class SimulationSample(BaseModel):
    sample_id: int = Field(ge=1)
    disruption_end_time: datetime

    baseline_delay_minutes: int = Field(ge=0)
    greedy_delay_minutes: int = Field(ge=0)
    optimized_delay_minutes: int = Field(ge=0)
    baseline_cost_gbp: float = Field(ge=0)
    greedy_cost_gbp: float = Field(ge=0)
    optimized_cost_gbp: float = Field(ge=0)


class StrategyRiskMetrics(BaseModel):
    strategy: str

    mean_delay_minutes: float = Field(ge=0)
    p90_delay_minutes: float = Field(ge=0)
    p95_delay_minutes: float = Field(ge=0)
    worst_case_delay_minutes: int = Field(ge=0)

    severe_delay_probability_percent: float = Field(ge=0,
                                                    le=100)
    mean_cost_gbp: float = Field(ge=0)
    cost_stddev_gbp: float = Field(ge=0)
    value_at_risk_gbp: float = Field(ge=0)
    conditional_value_at_risk_gbp: float = Field(ge=0)
    worst_case_cost_gbp: float = Field(ge=0)

class MonteCarloResult(BaseModel):
    iterations: int = Field(ge=1)
    seed: int
    end_time_stddev_minutes: float = Field(ge=0)
    risk_confidence: float = Field(gt=0.5, lt=1.0)
    severe_delay_threshold_minutes: int = Field(ge=0)
    baseline: StrategyRiskMetrics
    greedy: StrategyRiskMetrics
    optimized: StrategyRiskMetrics
    samples: list[SimulationSample]
