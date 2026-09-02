from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class AircraftUnavailability(BaseModel):
    disruption_id: str = Field(min_length=1)
    aircraft_id: str = Field(min_length=1)

    start_time: datetime
    end_time: datetime

    reason: str = Field(
        default="Operational disruption",
        min_length=1,
    )

    @model_validator(mode="after")
    def validate_window(self) -> "AircraftUnavailability":
        if self.end_time <= self.start_time:
            raise ValueError("Disruption end time must be after start time.")

        return self

class FlightImpact(BaseModel):
    flight_id: str
    flight_number: str
    aircraft_id: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    projected_departure: datetime
    projected_arrival: datetime
    delay_minutes: int = Field(ge=0)
    passengers: int = Field(ge=0)
    directly_affected: bool


class DisruptionAssessment(BaseModel):
    disruption_id: str
    aircraft_id: str

    impacts: list[FlightImpact]

    impacted_flights: int = Field(ge=0)
    directly_affected_flights: int = Field(ge=0)

    passengers_affected: int = Field(ge=0)
    total_delay_minutes: int = Field(ge=0)
    maximum_delay_minutes: int = Field(ge=0)


