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

to run scripts

python -m app.scripts.create_admin   -> for creating admin
python -m tests/tests.py -q          -> for running test

For all demo user designations except admin use password `Password123!`:

 
- `manager@example.com`
- `agent@example.com`
- `customer@example.com`

For admin:
`admin@gmail.com` and password is AdminPassword123!

Access swagger ui at `http://127.0.0.1:8000/docs`.

 Main Features

- Customer complaint submission and authorized history.
- Role-based customer, agent, manager, and administrator access.
- Deterministic priority, SLA deadlines, due-soon/breached state, duplicate detection, and workflow validation.
- Assignment, notes, escalation history, filtering, pagination. 
- CSV and JSON import/export.
- Tracked jobs with accepted/rejected import details.
- Cached support dashboard with visible cache `MISS`/`HIT` behavior and parallel metric collection.
- Complaint trend narrative generated from computed metrics, with a deterministic fallback when the model provider is unavailable.

 Main API Routes

Important Endpoints
-------------------
POST /auth/register                  Register a user
POST /auth/login                     Login and receive JWT
GET  /auth/me                        Read current user
POST /complaints                     Create a complaint
GET  /complaints                     List authorized complaints
GET  /complaints/{id}                Read a complaint
PATCH /complaints/{id}/assign        Manager/admin assignment
PATCH /complaints/{id}/status        Workflow status update
POST /complaints/{id}/notes          Add a complaint note
POST /complaints/{id}/escalate       Manager/admin escalation
GET  /complaint-categories           List categories
POST /complaint-categories           Admin category creation
GET  /analytics/support-dashboard    Dashboard metrics
GET  /analytics/sla-performance      SLA metrics
GET  /analytics/agent-ranking        Manager/admin agent ranking
POST /complaints/import-job           Manager/admin CSV/JSON background import
GET  /complaints/export?format=csv    Authenticated role-scoped CSV export
GET  /complaints/export?format=json   Authenticated role-scoped JSON export
GET  /jobs/{job_id}                   Background job status
POST /ai/complaint-trend-summary      Agent/manager/admin trend summary
GET  /health                          Service health check

All business data can be accessed via Streamlit using the FastAPI backend. 
