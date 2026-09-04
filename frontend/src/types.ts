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