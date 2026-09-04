from statistics import median
from time import perf_counter
from fastapi.testclient import TestClient
from backend.app.main import app

REPEATS = 5


BENCHMARK_CASES = [
    {
        "name": "Moderate",
        "start_time": "08:00",
        "end_time": "09:30",
    },
    {
        "name": "Standard",
        "start_time": "08:00",
        "end_time": "10:30",
    },
    {
        "name": "Severe",
        "start_time": "08:00",
        "end_time": "11:30",
    },
]


def timed_post(
    client: TestClient,
    endpoint: str,
    payload: dict,
) -> tuple[float, dict]:
    timings = []
    final_result = {}

    for _ in range(REPEATS):
        start = perf_counter()

        response = client.post(
            endpoint,
            json=payload,
        )

        elapsed_ms = (
            perf_counter() - start
        ) * 1000

        if response.status_code != 200:
            raise RuntimeError(
                f"{endpoint} returned "
                f"{response.status_code}: "
                f"{response.text}"
            )

        timings.append(
            elapsed_ms,
        )

        final_result = response.json()

    return (
        median(timings),
        final_result,
    )


def main() -> None:
    with TestClient(app) as client:
        scenario_response = client.get(
            "/api/scenario",
        )

        scenario_response.raise_for_status()

        scenario = scenario_response.json()

        operating_date = (
            scenario["flights"][0][
                "scheduled_departure"
            ][:10]
        )

        print()
        print(
            "AeroReplan Recovery Benchmark"
        )
        print(
            "=" * 86
        )

        header = (
            f"{'Case':<12}"
            f"{'Greedy ms':>12}"
            f"{'MILP ms':>12}"
            f"{'Delay':>10}"
            f"{'Recovered':>12}"
            f"{'Swaps':>8}"
            f"{'Candidates':>12}"
        )

        print(header)
        print("-" * 86)

        for index, benchmark in enumerate(
            BENCHMARK_CASES,
            start=1,
        ):
            payload = {
                "operating_date": operating_date,
                "seed": 42,
                "disruption": {
                    "disruption_id": (
                        f"BENCHMARK-{index}"
                    ),
                    "aircraft_id": "AC001",
                    "start_time": (
                        f"{operating_date}T"
                        f"{benchmark['start_time']}:00Z"
                    ),
                    "end_time": (
                        f"{operating_date}T"
                        f"{benchmark['end_time']}:00Z"
                    ),
                    "reason": (
                        "Recovery benchmark"
                    ),
                },
            }

            greedy_ms, _ = timed_post(
                client,
                "/api/recovery/greedy",
                payload,
            )

            milp_ms, optimized = timed_post(
                client,
                "/api/recovery/optimize",
                payload,
            )

            plan = optimized["plan"]

            print(
                f"{benchmark['name']:<12}"
                f"{greedy_ms:>12.2f}"
                f"{milp_ms:>12.2f}"
                f"{plan['total_delay_minutes']:>10}"
                f"{plan['delay_reduction_minutes']:>12}"
                f"{plan['reassigned_flights']:>8}"
                f"{optimized['candidate_count']:>12}"
            )

        print("-" * 86)

        print(
            f"Each strategy measured using "
            f"the median of {REPEATS} runs."
        )

        print(
            "Timing includes local FastAPI "
            "request/response overhead."
        )

        print()


if __name__ == "__main__":
    main()