import {
  useMemo,
  useState,
} from "react";

import {
  analyzeDecisions,
  runMonteCarlo,
} from "./api";

import type {
  DecisionAnalysis,
  DecisionWeights,
  DisruptionRequest,
  MonteCarloConfig,
  MonteCarloResult,
  StrategyDecisionPoint,
  StrategyRiskMetrics,
} from "./types";

import "./decision-lab.css";


function formatCurrency(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-GB",
    {
      style: "currency",
      currency: "GBP",
      maximumFractionDigits: 0,
    },
  ).format(value);
}


function formatNumber(
  value: number,
  digits = 1,
): string {
  return value.toFixed(
    digits,
  );
}


function strategyLabel(
  strategy: string,
): string {
  const labels: Record<
    string,
    string
  > = {
    unrecovered_baseline:
      "Unrecovered",
    greedy_tail_reassignment:
      "Greedy heuristic",
    milp_recovery:
      "MILP recovery",
  };

  return (
    labels[strategy]
    ?? strategy
  );
}


interface DecisionLabProps {
  request: DisruptionRequest;
}


function DecisionLab({
  request,
}: DecisionLabProps) {
  const [
    weights,
    setWeights,
  ] = useState<DecisionWeights>({
    expected_cost_weight: 1.0,
    cvar_weight: 0.25,
    delay_weight: 0.0,
    emissions_weight: 0.0,
  });

  const [
    iterations,
    setIterations,
  ] = useState(40);

  const [
    uncertainty,
    setUncertainty,
  ] = useState(45);

  const [
    confidence,
    setConfidence,
  ] = useState(0.95);

  const [
    result,
    setResult,
  ] = useState<
    DecisionAnalysis | null
  >(null);

  const [
    simulation,
    setSimulation,
  ] = useState<
    MonteCarloResult | null
  >(null);

  const [
    running,
    setRunning,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  const config =
    useMemo<MonteCarloConfig>(
      () => ({
        iterations,
        end_time_stddev_minutes:
          uncertainty,
        risk_confidence:
          confidence,
        severe_delay_threshold_minutes:
          180,
        seed: 42,
      }),
      [
        confidence,
        iterations,
        uncertainty,
      ],
    );


  function updateWeight(
    key: keyof DecisionWeights,
    value: number,
  ) {
    setWeights(
      (
        current,
      ) => ({
        ...current,
        [key]: value,
      }),
    );
  }


  async function runAnalysis() {
    setRunning(true);
    setError(null);

    try {
      const [
        decisionResult,
        simulationResult,
      ] = await Promise.all([
        analyzeDecisions({
          ...request,
          config,
          weights,
        }),

        runMonteCarlo({
          ...request,
          config,
        }),
      ]);

      setResult(
        decisionResult,
      );

      setSimulation(
        simulationResult,
      );
    } catch (analysisError) {
      console.error(
        analysisError,
      );

      setError(
        "Decision analysis failed. Check that the backend is running and try again.",
      );
    } finally {
      setRunning(false);
    }
  }


  const recommended =
    result?.strategies.find(
      (strategy) =>
        strategy.strategy
        === result.recommended_strategy,
    );


  return (
    <section
      id="decision-lab"
      className="decision-lab"
    >
      <div className="decision-heading">
        <div>
          <p className="eyebrow">
            Advanced analytics
          </p>

          <h2>
            Decision Lab
          </h2>

          <p>
            Explore cost, tail risk,
            operational delay and
            emissions trade-offs under
            uncertain disruption duration.
          </p>
        </div>

        <div className="decision-context">
          <span>
            Active case
          </span>

          <strong>
            {
              request
                .disruption
                .aircraft_id
            }
          </strong>

          <small>
            {
              request
                .disruption
                .start_time
                .slice(11, 16)
            }
            {" → "}
            {
              request
                .disruption
                .end_time
                .slice(11, 16)
            }
            {" UTC"}
          </small>
        </div>
      </div>


      <div className="decision-layout">
        <aside className="decision-controls">
          <div className="control-section">
            <p className="control-title">
              Management preferences
            </p>

            <WeightControl
              label="Expected cost"
              value={
                weights.expected_cost_weight
              }
              onChange={
                (value) =>
                  updateWeight(
                    "expected_cost_weight",
                    value,
                  )
              }
            />

            <WeightControl
              label="Tail risk / CVaR"
              value={
                weights.cvar_weight
              }
              onChange={
                (value) =>
                  updateWeight(
                    "cvar_weight",
                    value,
                  )
              }
            />

            <WeightControl
              label="Delay"
              value={
                weights.delay_weight
              }
              onChange={
                (value) =>
                  updateWeight(
                    "delay_weight",
                    value,
                  )
              }
            />

            <WeightControl
              label="Emissions"
              value={
                weights.emissions_weight
              }
              onChange={
                (value) =>
                  updateWeight(
                    "emissions_weight",
                    value,
                  )
              }
            />
          </div>


          <div className="control-section">
            <p className="control-title">
              Uncertainty model
            </p>

            <label className="lab-slider">
              <div>
                <span>
                  Monte Carlo runs
                </span>

                <strong>
                  {iterations}
                </strong>
              </div>

              <input
                type="range"
                min="20"
                max="150"
                step="10"
                value={
                  iterations
                }
                onChange={
                  (event) =>
                    setIterations(
                      Number(
                        event.target.value,
                      ),
                    )
                }
              />
            </label>

            <label className="lab-slider">
              <div>
                <span>
                  Repair uncertainty
                </span>

                <strong>
                  ±{uncertainty} min
                </strong>
              </div>

              <input
                type="range"
                min="0"
                max="120"
                step="5"
                value={
                  uncertainty
                }
                onChange={
                  (event) =>
                    setUncertainty(
                      Number(
                        event.target.value,
                      ),
                    )
                }
              />
            </label>

            <label className="lab-slider">
              <div>
                <span>
                  Risk confidence
                </span>

                <strong>
                  {
                    (
                      confidence * 100
                    ).toFixed(0)
                  }%
                </strong>
              </div>

              <input
                type="range"
                min="0.80"
                max="0.99"
                step="0.01"
                value={
                  confidence
                }
                onChange={
                  (event) =>
                    setConfidence(
                      Number(
                        event.target.value,
                      ),
                    )
                }
              />
            </label>
          </div>


          <button
            className="decision-run-button"
            disabled={
              running
            }
            onClick={
              () =>
                void runAnalysis()
            }
          >
            {
              running
                ? "SIMULATING…"
                : "RUN DECISION ANALYSIS"
            }
          </button>

          {
            error && (
              <p className="decision-error">
                {error}
              </p>
            )
          }
        </aside>


        <div className="decision-results">
          {
            !result
            || !simulation
            || !recommended
              ? (
                <div className="decision-empty">
                  <div className="decision-empty-icon">
                    ∑
                  </div>

                  <h3>
                    Configure the model
                  </h3>

                  <p>
                    Set management
                    preferences and
                    uncertainty assumptions,
                    then run the analysis to
                    generate the Pareto and
                    risk view.
                  </p>
                </div>
              )
              : (
                <>
                  <div className="decision-summary-grid">
                    <DecisionMetric
                      label="Recommended"
                      value={
                        strategyLabel(
                          result
                            .recommended_strategy,
                        )
                      }
                      detail={
                        result
                          .pareto_strategies
                          .includes(
                            result
                              .recommended_strategy,
                          )
                          ? "Pareto optimal"
                          : "Weighted preference"
                      }
                    />

                    <DecisionMetric
                      label="Expected cost"
                      value={
                        formatCurrency(
                          recommended
                            .expected_cost_gbp,
                        )
                      }
                      detail="Mean simulated cost"
                    />

                    <DecisionMetric
                      label="CVaR"
                      value={
                        formatCurrency(
                          recommended
                            .cvar_cost_gbp,
                        )
                      }
                      detail={
                        `${(
                          confidence * 100
                        ).toFixed(0)}% tail-risk cost`
                      }
                    />

                    <DecisionMetric
                      label="Expected delay"
                      value={
                        `${formatNumber(
                          recommended
                            .expected_delay_minutes,
                        )} min`
                      }
                      detail="Across simulated outcomes"
                    />

                    <DecisionMetric
                      label="CO₂e"
                      value={
                        `${formatNumber(
                          recommended
                            .emissions_kg_co2e,
                          0,
                        )} kg`
                      }
                      detail="Affected-flight estimate"
                    />
                  </div>


                  <StrategyFrontier
                    strategies={
                      result.strategies
                    }
                  />


                  <RiskTable
                    simulation={
                      simulation
                    }
                  />
                </>
              )
          }
        </div>
      </div>
    </section>
  );
}


function WeightControl({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number;
  onChange: (
    value: number,
  ) => void;
}) {
  return (
    <label className="lab-slider">
      <div>
        <span>
          {label}
        </span>

        <strong>
          {
            value.toFixed(2)
          }
        </strong>
      </div>

      <input
        type="range"
        min="0"
        max="2"
        step="0.05"
        value={
          value
        }
        onChange={
          (event) =>
            onChange(
              Number(
                event.target.value,
              ),
            )
        }
      />
    </label>
  );
}


function DecisionMetric({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="decision-metric">
      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      <small>
        {detail}
      </small>
    </article>
  );
}


function StrategyFrontier({
  strategies,
}: {
  strategies:
    StrategyDecisionPoint[];
}) {
  const maxCost = Math.max(
    ...strategies.map(
      (strategy) =>
        strategy.expected_cost_gbp,
    ),
    1,
  );

  return (
    <div className="lab-panel">
      <div className="lab-panel-heading">
        <div>
          <p className="eyebrow">
            Multi-objective analysis
          </p>

          <h3>
            Strategy frontier
          </h3>
        </div>

        <span>
          Pareto-efficient strategies
          highlighted
        </span>
      </div>

      <div className="frontier-list">
        {
          strategies.map(
            (strategy) => (
              <div
                key={
                  strategy.strategy
                }
                className={
                  strategy
                    .is_pareto_optimal
                    ? "frontier-row pareto"
                    : "frontier-row"
                }
              >
                <div className="frontier-name">
                  <strong>
                    {
                      strategyLabel(
                        strategy.strategy,
                      )
                    }
                  </strong>

                  {
                    strategy
                      .is_pareto_optimal
                      && (
                        <span>
                          PARETO
                        </span>
                      )
                  }
                </div>

                <div className="frontier-cost">
                  <div className="frontier-bar-track">
                    <div
                      className="frontier-bar"
                      style={{
                        width:
                          `${
                            Math.max(
                              4,
                              (
                                strategy
                                  .expected_cost_gbp
                                / maxCost
                              ) * 100,
                            )
                          }%`,
                      }}
                    />
                  </div>

                  <strong>
                    {
                      formatCurrency(
                        strategy
                          .expected_cost_gbp,
                      )
                    }
                  </strong>
                </div>

                <div className="frontier-stat">
                  <span>
                    CVaR
                  </span>

                  <strong>
                    {
                      formatCurrency(
                        strategy
                          .cvar_cost_gbp,
                      )
                    }
                  </strong>
                </div>

                <div className="frontier-stat">
                  <span>
                    Delay
                  </span>

                  <strong>
                    {
                      formatNumber(
                        strategy
                          .expected_delay_minutes,
                      )
                    }m
                  </strong>
                </div>

                <div className="frontier-stat">
                  <span>
                    CO₂e
                  </span>

                  <strong>
                    {
                      formatNumber(
                        strategy
                          .emissions_kg_co2e,
                        0,
                      )
                    }kg
                  </strong>
                </div>
              </div>
            ),
          )
        }
      </div>
    </div>
  );
}


function RiskTable({
  simulation,
}: {
  simulation: MonteCarloResult;
}) {
  const rows:
    StrategyRiskMetrics[] = [
    simulation.baseline,
    simulation.greedy,
    simulation.optimized,
  ];

  return (
    <div className="lab-panel">
      <div className="lab-panel-heading">
        <div>
          <p className="eyebrow">
            Monte Carlo risk
          </p>

          <h3>
            Tail-risk comparison
          </h3>
        </div>

        <span>
          {
            simulation.iterations
          } simulated outcomes
        </span>
      </div>

      <div className="table-wrapper">
        <table className="risk-table">
          <thead>
            <tr>
              <th>
                Strategy
              </th>

              <th>
                Mean delay
              </th>

              <th>
                P95 delay
              </th>

              <th>
                Severe risk
              </th>

              <th>
                Mean cost
              </th>

              <th>
                VaR
              </th>

              <th>
                CVaR
              </th>
            </tr>
          </thead>

          <tbody>
            {
              rows.map(
                (strategy) => (
                  <tr
                    key={
                      strategy.strategy
                    }
                  >
                    <td>
                      <strong>
                        {
                          strategyLabel(
                            strategy.strategy,
                          )
                        }
                      </strong>
                    </td>

                    <td>
                      {
                        formatNumber(
                          strategy
                            .mean_delay_minutes,
                        )
                      }m
                    </td>

                    <td>
                      {
                        formatNumber(
                          strategy
                            .p95_delay_minutes,
                        )
                      }m
                    </td>

                    <td>
                      {
                        formatNumber(
                          strategy
                            .severe_delay_probability_percent,
                        )
                      }%
                    </td>

                    <td>
                      {
                        formatCurrency(
                          strategy
                            .mean_cost_gbp,
                        )
                      }
                    </td>

                    <td>
                      {
                        formatCurrency(
                          strategy
                            .value_at_risk_gbp,
                        )
                      }
                    </td>

                    <td>
                      {
                        formatCurrency(
                          strategy
                            .conditional_value_at_risk_gbp,
                        )
                      }
                    </td>
                  </tr>
                ),
              )
            }
          </tbody>
        </table>
      </div>
    </div>
  );
}


export default DecisionLab;