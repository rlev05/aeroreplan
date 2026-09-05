import {
  useEffect,
  useState,
} from "react";

import {
  fetchAnalysisCase,
  fetchAnalysisCases,
} from "./api";

import type {
  AnalysisCaseDetail,
  AnalysisCaseSummary,
  StrategyKPIs,
} from "./types";

import "./case-history.css";


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


function formatDate(
  value: string,
): string {
  const parsed =
    new Date(value);

  if (
    Number.isNaN(
      parsed.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-GB",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(parsed);
}


function CaseHistory() {
  const [
    cases,
    setCases,
  ] = useState<
    AnalysisCaseSummary[]
  >([]);

  const [
    selected,
    setSelected,
  ] = useState<
    AnalysisCaseDetail | null
  >(null);

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    detailLoading,
    setDetailLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  useEffect(() => {
    let cancelled = false;

    function refreshCases() {
      void fetchAnalysisCases()
        .then(
          (result) => {
            if (cancelled) {
              return;
            }

            setCases(
              result.cases,
            );

            setError(
              null,
            );
          },
        )
        .catch(
          (loadError) => {
            console.error(
              loadError,
            );

            if (cancelled) {
              return;
            }

            setError(
              "Saved cases could not be loaded.",
            );
          },
        )
        .finally(
          () => {
            if (cancelled) {
              return;
            }

            setLoading(
              false,
            );
          },
        );
    }

    function handleCaseSaved() {
      refreshCases();
    }

    refreshCases();

    window.addEventListener(
      "aeroreplan-case-saved",
      handleCaseSaved,
    );

    return () => {
      cancelled = true;

      window.removeEventListener(
        "aeroreplan-case-saved",
        handleCaseSaved,
      );
    };
  }, []);


  async function openCase(
    caseId: string,
  ) {
    setDetailLoading(
      true,
    );

    setError(
      null,
    );

    try {
      const result =
        await fetchAnalysisCase(
          caseId,
        );

      setSelected(
        result,
      );
    } catch (
      detailError
    ) {
      console.error(
        detailError,
      );

      setError(
        "The selected case could not be loaded.",
      );
    } finally {
      setDetailLoading(
        false,
      );
    }
  }


  return (
    <section
      id="case-history"
      className="case-history"
    >
      <div className="case-history-heading">
        <div>
          <p className="eyebrow">
            Decision audit trail
          </p>

          <h2>
            Case History
          </h2>

          <p>
            Persisted disruption
            analyses and historical
            recovery recommendations.
          </p>
        </div>

        <span className="case-count">
          {
            cases.length
          } saved cases
        </span>
      </div>


      <div className="case-history-layout">
        <div className="case-list">
          {
            loading ? (
              <div className="case-empty">
                Loading cases…
              </div>
            ) : cases.length === 0 ? (
              <div className="case-empty">
                <strong>
                  No saved analyses
                </strong>

                <span>
                  Run the Decision Lab
                  and save a case to
                  build the audit trail.
                </span>
              </div>
            ) : (
              cases.map(
                (item) => (
                  <button
                    key={
                      item.case_id
                    }
                    className={
                      selected?.case_id
                      === item.case_id
                        ? "case-list-item selected"
                        : "case-list-item"
                    }
                    onClick={
                      () =>
                        void openCase(
                          item.case_id,
                        )
                    }
                  >
                    <div className="case-list-top">
                      <strong>
                        {
                          item.aircraft_id
                        }
                      </strong>

                      <span>
                        {
                          strategyLabel(
                            item.recommended_strategy,
                          )
                        }
                      </span>
                    </div>

                    <p>
                      {
                        item.disruption_id
                      }
                    </p>

                    <small>
                      {
                        formatDate(
                          item.created_at,
                        )
                      }
                    </small>
                  </button>
                ),
              )
            )
          }

          {
            error && (
              <p className="case-error">
                {error}
              </p>
            )
          }
        </div>


        <div className="case-detail">
          {
            detailLoading ? (
              <div className="case-detail-empty">
                Loading analysis…
              </div>
            ) : !selected ? (
              <div className="case-detail-empty">
                <div className="case-detail-icon">
                  ↗
                </div>

                <strong>
                  Select a saved case
                </strong>

                <span>
                  Historical disruption
                  assumptions and
                  recommendations will
                  appear here.
                </span>
              </div>
            ) : (
              <CaseDetail
                detail={
                  selected
                }
              />
            )
          }
        </div>
      </div>
    </section>
  );
}


function CaseDetail({
  detail,
}: {
  detail: AnalysisCaseDetail;
}) {
  const comparison =
    detail.comparison;

  const recommended =
    detail.decision
      .strategies
      .find(
        (strategy) =>
          strategy.strategy
          === detail.decision
            .recommended_strategy,
      );

  const strategies:
    StrategyKPIs[] = [
    comparison.baseline,
    comparison.greedy,
    comparison.optimized,
  ];

  return (
    <>
      <div className="case-detail-header">
        <div>
          <span className="case-id-label">
            CASE
          </span>

          <h3>
            {
              detail.case_id
                .slice(0, 8)
            }
          </h3>

          <p>
            {
              formatDate(
                detail.created_at,
              )
            }
          </p>
        </div>

        <span className="audit-badge">
          PERSISTED
        </span>
      </div>


      <div className="case-detail-metrics">
        <CaseMetric
          label="Aircraft"
          value={
            detail.disruption
              .aircraft_id
          }
        />

        <CaseMetric
          label="Window"
          value={
            `${
              detail.disruption
                .start_time
                .slice(11, 16)
            }–${
              detail.disruption
                .end_time
                .slice(11, 16)
            }`
          }
        />

        <CaseMetric
          label="Recommended"
          value={
            strategyLabel(
              detail.decision
                .recommended_strategy,
            )
          }
        />

        <CaseMetric
          label="Expected cost"
          value={
            recommended
              ? formatCurrency(
                  recommended
                    .expected_cost_gbp,
                )
              : "—"
          }
        />

        <CaseMetric
          label="CVaR"
          value={
            recommended
              ? formatCurrency(
                  recommended
                    .cvar_cost_gbp,
                )
              : "—"
          }
        />

        <CaseMetric
          label="Expected delay"
          value={
            recommended
              ? `${recommended
                  .expected_delay_minutes
                  .toFixed(1)}m`
              : "—"
          }
        />
      </div>


      <div className="case-disruption-box">
        <span>
          Disruption reason
        </span>

        <strong>
          {
            detail.disruption
              .reason
          }
        </strong>
      </div>


      <div className="case-strategy-table">
        <div className="case-section-heading">
          <div>
            <p className="eyebrow">
              Recorded comparison
            </p>

            <h4>
              Recovery strategies
            </h4>
          </div>
        </div>

        <div className="table-wrapper">
          <table>
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
                  Reassignments
                </th>

                <th>
                  Estimated cost
                </th>
              </tr>
            </thead>

            <tbody>
              {
                strategies.map(
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
                          strategy
                            .total_delay_minutes
                        }m
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
                  ),
                )
              }
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}


function CaseMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="case-metric">
      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>
    </div>
  );
}


export default CaseHistory;