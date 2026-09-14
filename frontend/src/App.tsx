import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  assessDisruption,
  compareStrategies,
  fetchScenario,
  optimizeRecovery,
} from "./api";

import CaseHistory from "./CaseHistory";
import DecisionLab from "./DecisionLab";

import type {
  Aircraft,
  DisruptionAssessment,
  DisruptionRequest,
  Flight,
  MILPRecoveryResult,
  ScheduleScenario,
  StrategyComparison,
  StrategyKPIs,
} from "./types";

import "./disruption.css";


type LoadState =
  | "loading"
  | "ready"
  | "error";


function formatTime(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    "en-GB",
    {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "UTC",
    },
  ).format(
    new Date(value),
  );
}


function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    "en-GB",
  ).format(value);
}


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


function App() {
  const [
    scenario,
    setScenario,
  ] = useState<
    ScheduleScenario | null
  >(null);

  const [
    loadState,
    setLoadState,
  ] = useState<LoadState>(
    "loading",
  );

  const [
    selectedAircraft,
    setSelectedAircraft,
  ] = useState(
    "AC001",
  );

  const [
    startTime,
    setStartTime,
  ] = useState(
    "08:00",
  );

  const [
    endTime,
    setEndTime,
  ] = useState(
    "10:30",
  );

  const [
    reason,
    setReason,
  ] = useState(
    "Aircraft technical issue",
  );

  const [
    analysing,
    setAnalysing,
  ] = useState(false);

  const [
    analysisError,
    setAnalysisError,
  ] = useState<
    string | null
  >(null);

  const [
    assessment,
    setAssessment,
  ] = useState<
    DisruptionAssessment | null
  >(null);

  const [
    optimization,
    setOptimization,
  ] = useState<
    MILPRecoveryResult | null
  >(null);

  const [
    comparison,
    setComparison,
  ] = useState<
    StrategyComparison | null
  >(null);

  const [
    lastRequest,
    setLastRequest,
  ] = useState<
    DisruptionRequest | null
  >(null);


  useEffect(() => {
    async function loadScenario() {
      try {
        const result =
          await fetchScenario();

        setScenario(
          result,
        );

        setLoadState(
          "ready",
        );
      } catch (error) {
        console.error(
          error,
        );

        setLoadState(
          "error",
        );
      }
    }

    void loadScenario();
  }, []);


  const metrics = useMemo(() => {
    if (!scenario) {
      return null;
    }

    const aircraftById =
      new Map<
        string,
        Aircraft
      >(
        scenario.aircraft.map(
          (aircraft) => [
            aircraft.aircraft_id,
            aircraft,
          ],
        ),
      );

    const assignedAircraft =
      new Set(
        scenario.flights.map(
          (flight) =>
            flight.aircraft_id,
        ),
      );

    const totalPassengers =
      scenario.flights.reduce(
        (
          total,
          flight,
        ) =>
          total
          + flight.passengers,
        0,
      );

    const availableSeats =
      scenario.flights.reduce(
        (
          total,
          flight,
        ) => {
          const aircraft =
            aircraftById.get(
              flight.aircraft_id,
            );

          return (
            total
            + (
              aircraft
                ?.seat_capacity
              ?? 0
            )
          );
        },
        0,
      );

    const loadFactor =
      availableSeats > 0
        ? (
            100
            * totalPassengers
            / availableSeats
          )
        : 0;

    return {
      flights:
        scenario.flights.length,

      passengers:
        totalPassengers,

      activeAircraft:
        assignedAircraft.size,

      reserveAircraft:
        scenario.aircraft.length
        - assignedAircraft.size,

      loadFactor,
    };
  }, [scenario]);


  async function handleAnalysis() {
    if (!scenario) {
      return;
    }

    const operatingDate =
      scenario.flights[0]
        ?.scheduled_departure
        .slice(
          0,
          10,
        );

    if (!operatingDate) {
      return;
    }

    const request:
      DisruptionRequest = {
      operating_date:
        operatingDate,

      seed: 42,

      disruption: {
        disruption_id:
          `DISRUPTION-${Date.now()}`,

        aircraft_id:
          selectedAircraft,

        start_time:
          `${operatingDate}T${startTime}:00Z`,

        end_time:
          `${operatingDate}T${endTime}:00Z`,

        reason,
      },
    };

    setLastRequest(
      request,
    );

    setAnalysing(
      true,
    );

    setAnalysisError(
      null,
    );

    try {
      const [
        disruptionResult,
        optimizationResult,
        comparisonResult,
      ] = await Promise.all([
        assessDisruption(
          request,
        ),

        optimizeRecovery(
          request,
        ),

        compareStrategies(
          request,
        ),
      ]);

      setAssessment(
        disruptionResult,
      );

      setOptimization(
        optimizationResult,
      );

      setComparison(
        comparisonResult,
      );
    } catch (error) {
      console.error(
        error,
      );

      setAnalysisError(
        "Analysis failed. Check the disruption window and backend connection.",
      );
    } finally {
      setAnalysing(
        false,
      );
    }
  }


  function scrollToDecisionLab() {
    document
      .getElementById(
        "decision-lab",
      )
      ?.scrollIntoView({
        behavior: "smooth",
      });
  }


  function scrollToCaseHistory() {
    document
      .getElementById(
        "case-history",
      )
      ?.scrollIntoView({
        behavior: "smooth",
      });
  }


  if (
    loadState === "loading"
  ) {
    return (
      <main className="state-screen">
        <div className="state-panel">
          <div className="brand-mark">
            AR
          </div>

          <h1>
            AeroReplan
          </h1>

          <p>
            Connecting to operations
            data…
          </p>
        </div>
      </main>
    );
  }


  if (
    loadState === "error"
    || !scenario
    || !metrics
  ) {
    return (
      <main className="state-screen">
        <div className="state-panel">
          <div className="brand-mark">
            AR
          </div>

          <h1>
            Backend unavailable
          </h1>

          <p>
            Start the AeroReplan
            FastAPI service on port
            8000 and refresh.
          </p>
        </div>
      </main>
    );
  }


  const orderedFlights =
    [...scenario.flights].sort(
      (
        first,
        second,
      ) =>
        new Date(
          first
            .scheduled_departure,
        ).getTime()
        - new Date(
          second
            .scheduled_departure,
        ).getTime(),
    );


  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div>
          <div className="brand">
            <div className="brand-mark">
              AR
            </div>

            <div>
              <strong>
                AeroReplan
              </strong>

              <span>
                Decision Intelligence
              </span>
            </div>
          </div>

          <nav className="navigation">
            <button
              className="nav-item active"
            >
              <span>
                01
              </span>

              Operations
            </button>

            <button className="nav-item">
              <span>
                02
              </span>

              Recovery
            </button>

            <button
              className="nav-item"
              onClick={
                scrollToDecisionLab
              }
            >
              <span>
                03
              </span>

              Decision Lab
            </button>

            <button
              className="nav-item"
              onClick={
                scrollToCaseHistory
              }
            >
              <span>
                04
              </span>

              Case History
            </button>
          </nav>
        </div>

        <div className="sidebar-footer">
          <div className="system-status">
            <span className="status-dot" />

            <div>
              <strong>
                Systems nominal
              </strong>

              <span>
                API connected
              </span>
            </div>
          </div>
        </div>
      </aside>


      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">
              Operations Control
              Centre
            </p>

            <h1>
              Network overview
            </h1>
          </div>

          <div className="topbar-meta">
            <span>
              Scenario
            </span>

            <strong>
              {
                scenario
                  .scenario_id
              }
            </strong>
          </div>
        </header>


        <section
          className={
            assessment
              ? "alert-banner disruption-active"
              : "alert-banner"
          }
        >
          <div>
            <span className="alert-label">
              {
                assessment
                  ? "DISRUPTION ACTIVE"
                  : "NETWORK STATUS"
              }
            </span>

            <h2>
              {
                assessment
                  ? `${selectedAircraft} operational disruption`
                  : "Normal operations"
              }
            </h2>

            <p>
              {
                assessment
                  ? (
                    `${assessment.impacted_flights} flights and `
                    + `${assessment.passengers_affected} passengers are exposed. `
                    + "AeroReplan has evaluated recovery alternatives."
                  )
                  : (
                    "All scheduled rotations are currently feasible. "
                    + "Configure an aircraft disruption below to evaluate recovery options."
                  )
              }
            </p>

            <div className="disruption-controls">
              <div className="control-group">
                <label>
                  Aircraft
                </label>

                <select
                  value={
                    selectedAircraft
                  }
                  onChange={
                    (event) =>
                      setSelectedAircraft(
                        event.target.value,
                      )
                  }
                >
                  {
                    scenario.aircraft.map(
                      (
                        aircraft,
                      ) => (
                        <option
                          key={
                            aircraft.aircraft_id
                          }
                          value={
                            aircraft.aircraft_id
                          }
                        >
                          {
                            aircraft.aircraft_id
                          }
                          {" · "}
                          {
                            aircraft.tail_number
                          }
                        </option>
                      ),
                    )
                  }
                </select>
              </div>


              <div className="control-group">
                <label>
                  Unavailable from
                </label>

                <input
                  type="time"
                  value={
                    startTime
                  }
                  onChange={
                    (event) =>
                      setStartTime(
                        event.target.value,
                      )
                  }
                />
              </div>


              <div className="control-group">
                <label>
                  Available from
                </label>

                <input
                  type="time"
                  value={
                    endTime
                  }
                  onChange={
                    (event) =>
                      setEndTime(
                        event.target.value,
                      )
                  }
                />
              </div>


              <div className="control-group">
                <label>
                  Reason
                </label>

                <select
                  value={
                    reason
                  }
                  onChange={
                    (event) =>
                      setReason(
                        event.target.value,
                      )
                  }
                >
                  <option>
                    Aircraft technical issue
                  </option>

                  <option>
                    Unscheduled maintenance
                  </option>

                  <option>
                    Operational inspection
                  </option>

                  <option>
                    Ground handling delay
                  </option>
                </select>
              </div>


              <button
                className="analyse-button"
                disabled={
                  analysing
                }
                onClick={
                  () =>
                    void handleAnalysis()
                }
              >
                {
                  analysing
                    ? "ANALYSING…"
                    : "ANALYSE DISRUPTION"
                }
              </button>
            </div>

            {
              analysisError && (
                <p className="analysis-error">
                  {
                    analysisError
                  }
                </p>
              )
            }
          </div>

          <div className="readiness">
            <span>
              Recovery engine
            </span>

            <strong>
              {
                analysing
                  ? "RUNNING"
                  : assessment
                    ? "COMPLETE"
                    : "READY"
              }
            </strong>
          </div>
        </section>


        {
          assessment && (
            <section className="analysis-grid">
              <ImpactCard
                label="Impacted flights"
                value={
                  `${assessment.impacted_flights}`
                }
                detail={
                  `${assessment.directly_affected_flights} directly affected`
                }
              />

              <ImpactCard
                label="Passengers exposed"
                value={
                  formatNumber(
                    assessment.passengers_affected,
                  )
                }
                detail="Across impacted flights"
              />

              <ImpactCard
                label="Baseline delay"
                value={
                  `${assessment.total_delay_minutes}m`
                }
                detail="Without intervention"
              />

              <ImpactCard
                label="Maximum delay"
                value={
                  `${assessment.maximum_delay_minutes}m`
                }
                detail="Worst affected flight"
              />
            </section>
          )
        }


        {
          optimization
          && comparison
          && (
            <section className="panel recovery-panel">
              <div className="panel-header">
                <div>
                  <p className="eyebrow">
                    Recovery intelligence
                  </p>

                  <h2>
                    Recommended action
                  </h2>
                </div>

                <span className="panel-badge">
                  {
                    optimization
                      .solver_status
                  }
                </span>
              </div>

              <div className="recovery-layout">
                <div className="recommendation-card">
                  <span className="recommendation-label">
                    RECOMMENDED STRATEGY
                  </span>

                  <h3>
                    {
                      strategyLabel(
                        comparison
                          .recommended_strategy,
                      )
                    }
                  </h3>

                  <p>
                    Mathematical recovery
                    plan selected from
                    feasible fleet actions.
                  </p>

                  <div className="recommendation-metrics">
                    <div>
                      <span>
                        Recovery delay
                      </span>

                      <strong>
                        {
                          optimization
                            .plan
                            .total_delay_minutes
                        } min
                      </strong>
                    </div>

                    <div>
                      <span>
                        Delay recovered
                      </span>

                      <strong>
                        {
                          optimization
                            .plan
                            .delay_reduction_minutes
                        } min
                      </strong>
                    </div>

                    <div>
                      <span>
                        Reassignments
                      </span>

                      <strong>
                        {
                          optimization
                            .plan
                            .reassigned_flights
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Estimated saving
                      </span>

                      <strong>
                        {
                          formatCurrency(
                            comparison
                              .estimated_savings_vs_baseline_gbp,
                          )
                        }
                      </strong>
                    </div>
                  </div>
                </div>

                <StrategyTable
                  comparison={
                    comparison
                  }
                />
              </div>
            </section>
          )
        }


        {
          !assessment && (
            <section className="metric-grid">
              <MetricCard
                label="Scheduled flights"
                value={
                  formatNumber(
                    metrics.flights,
                  )
                }
                detail="Current operating day"
              />

              <MetricCard
                label="Passengers"
                value={
                  formatNumber(
                    metrics.passengers,
                  )
                }
                detail="Scheduled demand"
              />

              <MetricCard
                label="Active aircraft"
                value={
                  `${metrics.activeAircraft}`
                }
                detail={
                  `${metrics.reserveAircraft} reserve`
                }
              />

              <MetricCard
                label="Network load factor"
                value={
                  `${metrics.loadFactor.toFixed(1)}%`
                }
                detail="Synthetic passenger demand"
              />
            </section>
          )
        }


        <section className="operations-grid">
          <div className="panel schedule-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">
                  Flight programme
                </p>

                <h2>
                  Today's schedule
                </h2>
              </div>

              <span className="panel-badge">
                {
                  scenario.flights
                    .length
                } flights
              </span>
            </div>

            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>
                      Flight
                    </th>

                    <th>
                      Route
                    </th>

                    <th>
                      Departure
                    </th>

                    <th>
                      Arrival
                    </th>

                    <th>
                      Aircraft
                    </th>

                    <th>
                      Pax
                    </th>

                    <th>
                      Status
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {
                    orderedFlights.map(
                      (
                        flight,
                      ) => (
                        <FlightRow
                          key={
                            flight.flight_id
                          }
                          flight={
                            flight
                          }
                          assessment={
                            assessment
                          }
                          optimization={
                            optimization
                          }
                        />
                      ),
                    )
                  }
                </tbody>
              </table>
            </div>
          </div>


          <div className="panel fleet-panel">
            <div className="panel-header">
              <div>
                <p className="eyebrow">
                  Fleet
                </p>

                <h2>
                  Aircraft status
                </h2>
              </div>
            </div>

            <div className="fleet-list">
              {
                scenario.aircraft.map(
                  (
                    aircraft,
                  ) => {
                    const rotations =
                      scenario.flights.filter(
                        (
                          flight,
                        ) =>
                          flight.aircraft_id
                          === aircraft.aircraft_id,
                      );

                    return (
                      <AircraftCard
                        key={
                          aircraft.aircraft_id
                        }
                        aircraft={
                          aircraft
                        }
                        rotations={
                          rotations
                        }
                        disrupted={
                          assessment
                            ?.aircraft_id
                          === aircraft.aircraft_id
                        }
                      />
                    );
                  },
                )
              }
            </div>
          </div>
        </section>


        {
          lastRequest && (
            <DecisionLab
              request={
                lastRequest
              }
            />
          )
        }


        <CaseHistory />
      </main>
    </div>
  );
}


function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="metric-card">
      <p>
        {label}
      </p>

      <strong>
        {value}
      </strong>

      <span>
        {detail}
      </span>
    </article>
  );
}


function ImpactCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string;
  detail: string;
}) {
  return (
    <article className="impact-card">
      <p>
        {label}
      </p>

      <strong>
        {value}
      </strong>

      <span>
        {detail}
      </span>
    </article>
  );
}


function StrategyTable({
  comparison,
}: {
  comparison:
    StrategyComparison;
}) {
  const strategies:
    StrategyKPIs[] = [
    comparison.baseline,
    comparison.greedy,
    comparison.optimized,
  ];

  return (
    <div className="table-wrapper">
      <table className="strategy-table">
        <thead>
          <tr>
            <th>
              Strategy
            </th>

            <th>
              Delay
            </th>

            <th>
              Pax affected
            </th>

            <th>
              Swaps
            </th>

            <th>
              Cost
            </th>
          </tr>
        </thead>

        <tbody>
          {
            strategies.map(
              (
                strategy,
              ) => {
                const recommended =
                  strategy.strategy
                  === comparison
                    .recommended_strategy;

                return (
                  <tr
                    key={
                      strategy.strategy
                    }
                    className={
                      recommended
                        ? "recommended-row"
                        : ""
                    }
                  >
                    <td className="strategy-name">
                      {
                        strategyLabel(
                          strategy.strategy,
                        )
                      }

                      {
                        recommended && (
                          <span className="recommended-tag">
                            RECOMMENDED
                          </span>
                        )
                      }
                    </td>

                    <td>
                      {
                        strategy
                          .total_delay_minutes
                      } min
                    </td>

                    <td>
                      {
                        strategy
                          .passengers_affected
                      }
                    </td>

                    <td>
                      {
                        strategy
                          .reassigned_flights
                      }
                    </td>

                    <td>
                      {
                        formatCurrency(
                          strategy
                            .total_estimated_cost_gbp,
                        )
                      }
                    </td>
                  </tr>
                );
              },
            )
          }
        </tbody>
      </table>
    </div>
  );
}


function FlightRow({
  flight,
  assessment,
  optimization,
}: {
  flight: Flight;
  assessment:
    DisruptionAssessment | null;
  optimization:
    MILPRecoveryResult | null;
}) {
  const impact =
    assessment?.impacts.find(
      (
        item,
      ) =>
        item.flight_id
        === flight.flight_id,
    );

  const recoveredFlight =
    optimization
      ?.plan
      .flights
      .find(
        (
          item,
        ) =>
          item.flight_id
          === flight.flight_id,
      );

  let status =
    "ON TIME";

  let statusClass =
    "on-time";

  if (
    recoveredFlight
      ?.action
    === "reassign"
  ) {
    status =
      `REASSIGN → ${recoveredFlight.assigned_aircraft_id}`;

    statusClass =
      "reassign";
  } else if (
    recoveredFlight
    && recoveredFlight
      .delay_minutes > 0
  ) {
    status =
      `DELAY +${recoveredFlight.delay_minutes}m`;

    statusClass =
      "delay";
  } else if (
    impact
  ) {
    status =
      `DELAY +${impact.delay_minutes}m`;

    statusClass =
      "delay";
  }

  return (
    <tr>
      <td>
        <strong
          className={
            impact
              ?.directly_affected
              ? "direct-impact"
              : ""
          }
        >
          {
            flight
              .flight_number
          }
        </strong>

        <span className="cell-subtext">
          {
            flight
              .flight_id
          }
        </span>
      </td>

      <td>
        <div className="route-cell">
          <strong>
            {flight.origin}
          </strong>

          <span>
            →
          </span>

          <strong>
            {
              flight
                .destination
            }
          </strong>
        </div>
      </td>

      <td>
        {
          formatTime(
            flight
              .scheduled_departure,
          )
        }
      </td>

      <td>
        {
          formatTime(
            flight
              .scheduled_arrival,
          )
        }
      </td>

      <td>
        {
          recoveredFlight
            ?.assigned_aircraft_id
          ?? flight.aircraft_id
        }
      </td>

      <td>
        {
          flight.passengers
        }
      </td>

      <td>
        <span
          className={
            `flight-status ${statusClass}`
          }
        >
          {status}
        </span>
      </td>
    </tr>
  );
}


function AircraftCard({
  aircraft,
  rotations,
  disrupted,
}: {
  aircraft: Aircraft;
  rotations: Flight[];
  disrupted: boolean;
}) {
  const isReserve =
    rotations.length === 0;

  return (
    <article className="aircraft-card">
      <div className="aircraft-heading">
        <div>
          <strong>
            {
              aircraft
                .tail_number
            }
          </strong>

          <span>
            {
              aircraft
                .aircraft_id
            }
          </span>
        </div>

        <span
          className={
            disrupted
              ? "aircraft-state reserve"
              : isReserve
                ? "aircraft-state reserve"
                : "aircraft-state active"
          }
        >
          {
            disrupted
              ? "DISRUPTED"
              : isReserve
                ? "RESERVE"
                : "ACTIVE"
          }
        </span>
      </div>

      <div className="aircraft-specs">
        <div>
          <span>
            Type
          </span>

          <strong>
            {
              aircraft
                .aircraft_type
            }
          </strong>
        </div>

        <div>
          <span>
            Base
          </span>

          <strong>
            {
              aircraft
                .home_airport
            }
          </strong>
        </div>

        <div>
          <span>
            Seats
          </span>

          <strong>
            {
              aircraft
                .seat_capacity
            }
          </strong>
        </div>

        <div>
          <span>
            Legs
          </span>

          <strong>
            {
              rotations.length
            }
          </strong>
        </div>
      </div>
    </article>
  );
}


export default App;