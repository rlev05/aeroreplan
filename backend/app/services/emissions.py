from backend.app.domain import AircraftType


AIRCRAFT_EMISSIONS_KG_CO2E_PER_KM = {
    AircraftType.AIRBUS_A319: 2.70,
    AircraftType.AIRBUS_A320: 3.00,
    AircraftType.AIRBUS_A321: 3.50,
    AircraftType.EMBRAER_E190: 2.25,
}


def estimate_flight_emissions_kg(
        distance_km: float,
        aircraft_type: AircraftType
) -> float:
    factor = (
        AIRCRAFT_EMISSIONS_KG_CO2E_PER_KM[aircraft_type]
    )

    return round(distance_km * factor, 2)


