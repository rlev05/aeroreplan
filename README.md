# AeroReplan

AerorReplan is a short haul airline disruption recovery project I built to explore optimisation under uncertainty.

The basic problem is simple if an aircraft suddenyl becomes unavailable, what should an airline do with flights that depend on it 

The system models how the disruption spreads through the schedule and then compares several recovery approaches

- leaving the schedule unrecovered
- a greedy aircraft reassignment heuristic 
- a mathematical recovery model using OR-tools 
- a risk aware recommendation using Monte Carlo simulation

There is also a React frontend which acts as a small airline Operations Control Centre. It lets the user creates disruptions, compare recovery plans and save previous analyses

## Example

The main scenario I used while testing takes aircract 'AC001' out of service from 8:00 to 10:30

Without any recovery action: 

- 3 flights are affected
- total propagated delay is 310 mins 
- later flights inherit delay from original disruption 

The recovery model keep the first affected flight delayed but moves the following two flights onto the reserve aicraft

This reduces total delay from 310 to 115 mins recovering 195 mins of delay

I intentionally made the reserve aircraft a less efficient model from A321 to an A320 

This means moving flight to the reserve can improve the schedule but also increases the emissions. That gives the optimiser an actual tradeoff instead of making one strategy automatically better than anything else

## What is in the project

The backend is written in Python with FastAPI

It generates a synthetic short haul schedule using real UK and European airports and models:

- aircraft rotations
- passenger demand
- aircraft capacity
- minimum turnaround time
- aircraft location
- cascading delays
- aircraft unavailability

The recovery side currently contains two main approaches

## Greedy recovery

The heuristic works throught the affected rotation and looks for the earliest point where the remaining flights can frasibly be moved onto another aircraft.

It is deliberately simple and gives me a useful baseline to compare against more mathematical models

## MILP recovery

The second approach uses OR-Tools 

For feasible recovery candidates, the optimisation objective combines:

w_dD + w_pPD + w_rR + w_eE

where:

- `D` = total delay
- `PD` = passenger-delay minutes
- `R` = reassignment penalty
- `E` = additional estimated emissions

The weights can be changed depending on what the user wants to prioritise

The model also checks:

- aircraft capacity
- aircraft availability
- aircraft location
- turnaround feasibility

For the standard example, the greedy heuristic and MILP currently find the same 115 min solution.

I kept this behaviour rather than trying to force the optimiser to produce a different answer, because on a small scenario the heuristic can legitimately find the optimum.

## Uncertainty

One thing I wanted to avoid was assuming that an aircraft will definitely return to service at exactly the expected time.

The Monte Carlo model samples the disruption end time around its nominal value:

T_{return} = T_{nominal} + \epsilon


The error term is sampled from a normal distribution.

Each recovery strategy is then evaluated repeatedly under different disruption durations.

From those simulations AeroReplan calculates:

- mean cost
- mean delay
- P90 delay
- P95 delay
- severe-delay probability
- Value at Risk
- Conditional Value at Risk

CVaR was useful here because two strategies can have similar average outcomes but very different behaviour in the worst disruption cases.

## Decision Lab

The frontend includes a Decision Lab where the relative importance of the following can be changed:

- expected cost
- CVaR
- delay
- emissions

For each strategy I store a point representing:

(E[C], CVaR(C), E[D], E)


The system also calculates which strategies are Pareto optimal.

I kept the Pareto calculation separate from the weighted recommendation.

The Pareto frontier shows which strategies are non-dominated, while the management weights determine which trade-off the user actually prefers.

## Screenshots

### Operations Control Centre

![Operations Control Centre](docs/images/operations-control.png)

### Recovery result

![Recovery result](docs/images/recovery-result.png)

### Decision Lab

![Decision Lab](docs/images/decision-lab.png)

## Frontend

The frontend is built with React and TypeScript.

The Operations Control Centre shows:

- daily flights
- aircraft status
- passenger demand
- reserve aircraft
- disruption controls
- affected flights and passengers
- baseline delay
- recommended recovery
- individual delay and reassignment actions

There are also views for the Decision Lab and saved case history.

## Saving analysis cases

Completed analyses can be saved through the API.

I used SQLAlchemy so I could use SQLite during local development and switch the production configuration to PostgreSQL without changing the rest of the persistence layer.

Saved cases contain:

- disruption details
- strategy comparisons
- decision analysis

This gives the project a basic decision audit trail.

## Stack

### Backend

- Python 3.12
- FastAPI
- Pydantic
- OR-Tools
- SQLAlchemy
- PostgreSQL
- SQLite
- pytest

### Frontend

- React
- TypeScript
- Vite
- ESLint
- CSS

### Infrastructure

- Docker
- Docker Compose
- Nginx
- GitHub Actions

## Running locally

Create and activate the Python environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Install the frontend dependencies:

```powershell
cd frontend
npm install
cd ..
```

Start the API:

```powershell
uvicorn backend.app.main:app --reload
```

In another terminal:

```powershell
cd frontend
npm run dev
```

Frontend:

`http://localhost:5173`

FastAPI documentation:

`http://localhost:8000/docs`

## Docker

The production Docker setup contains:

- React
- Nginx
- FastAPI
- PostgreSQL

Start the stack with:

```powershell
docker compose up --build
```

Application:

`http://localhost:8080`

Backend health endpoint:

`http://localhost:8000/health`

PostgreSQL uses a Docker volume, so saved cases survive normal container restarts.

To stop the stack:

```powershell
docker compose down
```

## Tests

Run the backend suite with:

```powershell
python -m pytest
```

Current result:

**75 passed**

The tests cover:

- domain models
- schedule generation
- disruption propagation
- greedy recovery
- MILP optimisation
- emissions
- risk metrics
- persistence
- API behaviour
- end-to-end recovery behaviour

For the frontend:

```powershell
cd frontend
npm run lint
npm run build
```

Backend and frontend checks also run through GitHub Actions when changes are pushed to `main`.

## Benchmark

There is a small benchmark for comparing the heuristic and MILP recovery implementations.

Run it with:

```powershell
python -m backend.benchmarks.benchmark_recovery
```

It runs moderate, standard and severe disruption cases and reports:

- heuristic runtime
- MILP runtime
- recovered delay
- reassignment count
- optimiser candidate count

The exact timings depend on the machine, so I have not hard-coded benchmark results into the README.

## Project structure

- `backend/app/` - application code
- `backend/tests/` - automated tests
- `backend/benchmarks/` - recovery benchmark
- `frontend/src/` - React application
- `.github/workflows/` - CI configuration
- `compose.yaml` - Docker Compose stack
- `requirements.txt` - Python dependencies

## Scope

I kept the project focused on aircraft recovery rather than trying to simulate every part of an airline operation.

It currently does not solve:

- crew rostering
- individual passenger rebooking
- airport gate allocation
- detailed maintenance planning
- long-haul recovery
- full airline-scale network optimisation

Those would all be logical extensions, but they would also turn this into a much larger optimisation problem.

The main aim of this version was to build the aircraft recovery problem properly and then add uncertainty, risk and business trade-offs around it.

