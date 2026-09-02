from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, Field



class RecoveryActionType(StrEnum):
    DELAY = "delay"
    REASSIGN = "reassign"

class RecoveredFlight(BaseModel):
    flight_id: str
    flight_id: str
    flight_number: str
    origin: str
    destination: str
    original_aircraft_id: str
    assigned_aircraft_id: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    projected_departure: datetime
    projected_arrival: datetime
    passengers: int = Field(ge=0)
    delay_minutes: int = Field(ge=0)

    action: RecoveryActionType

class RecoveryPlan(BaseModel):
    strategy: str
    disruption_id: str

    flights: list[RecoveredFlight]
    baseline_total_delay_minutes: int = Field(ge=0)
    total_delay_minutes: int = Field(ge=0)
    delay_reduction_minutes: int = Field(ge=0)
    baseline_passengers_affected: int = Field(ge=0)
    passengers_affected: int = Field(ge=0)
    passengers_recovered: int = Field(ge=0)
    reassigned_flights: int = Field(ge=0)


