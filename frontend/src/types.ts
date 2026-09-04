export type AircraftType =
  | "A319"
  | "A320"
  | "A321"
  | "E190";

export interface Airport {
  iata_code: string;
  name: string;
  city: string;
  country: string;
  latitude: number;
  longitude: number;
}

export interface Aircraft {
  aircraft_id: string;
  tail_number: string;
  aircraft_type: AircraftType;
  seat_capacity: number;
  home_airport: string;
}

export interface Flight {
  flight_id: string;
  flight_number: string;
  origin: string;
  destination: string;
  scheduled_departure: string;
  scheduled_arrival: string;
  aircraft_id: string;
  passengers: number;
  distance_km: number;
}

export interface ScheduleScenario {
  scenario_id: string;
  airports: Airport[];
  aircraft: Aircraft[];
  flights: Flight[];
}

export interface AircraftUnavailability {
  disruption_id: string;
  aircraft_id: string;
  start_time: string;
  end_time: string;
  reason: string;
}

export interface DisruptionRequest {
  operating_date: string;
  seed: number;
  disruption: AircraftUnavailability;
}

export interface FlightImpact {
  flight_id: string;
  flight_number: string;
  aircraft_id: string;
  scheduled_departure: string;
  scheduled_arrival: string;
  projected_departure: string;
  projected_arrival: string;
  delay_minutes: number;
  passengers: number;
  directly_affected: boolean;
}

export interface DisruptionAssessment {
  disruption_id: string;
  aircraft_id: string;
  impacts: FlightImpact[];
  impacted_flights: number;
  directly_affected_flights: number;
  passengers_affected: number;
  total_delay_minutes: number;
  maximum_delay_minutes: number;
}

export type RecoveryAction =
  | "delay"
  | "reassign";

export interface RecoveredFlight {
  flight_id: string;
  flight_number: string;
  origin: string;
  destination: string;
  original_aircraft_id: string;
  assigned_aircraft_id: string;
  scheduled_departure: string;
  scheduled_arrival: string;
  projected_departure: string;
  projected_arrival: string;
  passengers: number;
  delay_minutes: number;
  action: RecoveryAction;
}

export interface RecoveryPlan {
  strategy: string;
  disruption_id: string;
  flights: RecoveredFlight[];
  baseline_total_delay_minutes: number;
  total_delay_minutes: number;
  delay_reduction_minutes: number;
  baseline_passengers_affected: number;
  passengers_affected: number;
  passengers_recovered: number;
  reassigned_flights: number;
}

export interface MILPRecoveryResult {
  plan: RecoveryPlan;
  solver_status: string;
  objective_value: number;
  solve_time_ms: number;
  candidate_count: number;
  incremental_emissions_kg_co2e: number;
}

export interface StrategyKPIs {
  strategy: string;
  flights_considered: number;
  delayed_flights: number;
  on_time_flights: number;
  passengers_affected: number;
  passenger_delay_minutes: number;
  total_delay_minutes: number;
  average_delay_minutes: number;
  maximum_delay_minutes: number;
  reassigned_flights: number;
  delay_reduction_percent: number;
  passenger_recovery_percent: number;
  on_time_recovery_rate_percent: number;
  operational_delay_cost_gbp: number;
  passenger_delay_cost_gbp: number;
  reassignment_cost_gbp: number;
  total_estimated_cost_gbp: number;
}

export interface StrategyComparison {
  baseline: StrategyKPIs;
  greedy: StrategyKPIs;
  optimized: StrategyKPIs;
  recommended_strategy: string;
  estimated_savings_vs_baseline_gbp: number;
}