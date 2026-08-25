# Customer Complaint Management System

 simplified customer complaint and escalation POC using FastAPI, SQLAlchemy, JWT authentication, background jobs, TTL caching, an optional LLM, and Streamlit.

## Run

From the Application root:

if its 1st time dont forget to run 
python -m pip install -r requirements.txt

.\venv\Scripts\Activate.ps1
python -m app.scripts.seed_demo
python -m fastapi dev app/main.py


In a 2nd terminal, from `streamlit_app`:
run
python -m streamlit run app.py


For all demo user designations use password `Password123!`:

- `admin@example.com`
- `manager@example.com`
- `agent@example.com`
- `customer@example.com`

Access swagger ui at `http://127.0.0.1:8000/docs`.

 Main Features

- Customer complaint submission and authorized history.
- Role-based customer, agent, manager, and administrator access.
- Deterministic priority, SLA deadlines, due-soon/breached state, duplicate detection, and workflow validation.
- Assignment, notes, escalation history, filtering, pagination. 
- CSV import/export.
- Tracked jobs.
- Cached support dashboard with visible cache `MISS`/`HIT` behavior and parallel metric collection.
- Complaint trend narrative generated from computed metrics, with a deterministic fallback when the model provider is unavailable.

 Main API Routes

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `POST /complaints`, `GET /complaints`, `GET /complaints/{id}`
- `PATCH /complaints/{id}/assign`, `PATCH /complaints/{id}/status`
- `POST /complaints/{id}/notes`, `POST /complaints/{id}/escalate`
- `GET /complaint-categories`, `POST /complaint-categories`
- `GET /analytics/support-dashboard`
- `GET /analytics/sla-performance`, `GET /analytics/agent-ranking`
- `POST /complaints/import-job`, `GET /complaints/export`, `GET /jobs/{job_id}`
- `POST /ai/complaint-trend-summary`, `GET /health`

All business data is accessed by Streamlit through FastAPI. The active application exposes only customer and complaint functionality.
