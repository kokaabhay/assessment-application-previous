# Vendor Contract Management System

A full-stack vendor contract management application built with **FastAPI**, **SQLAlchemy**, **Pydantic**, **JWT authentication**, **LLM integration**, and **Streamlit**.

The application allows authenticated users to manage vendors and contracts, enforce ownership-based authorization, import/export contract data, and use an LLM to analyze contract risks and provide recommendations.

---

## Features

### Authentication & Authorization

- User registration
- User login
- JWT access tokens
- Password hashing
- Current-user endpoint
- Role-based authorization
- Resource ownership checks

### Vendor Management

- Create vendors
- View vendors
- Update vendors
- Delete vendors
- Vendor categories and status
- Vendor contract relationships
- Compliance document relationships

### Contract Management

- Create contracts
- View contracts
- Update contracts
- Delete contracts
- Ownership-based access control
- Admin access to all contracts
- Contract validation
- Spend validation
- Contract date validation

### CSV / JSON

- Export contracts as CSV
- Export contracts as JSON
- Import contract data from CSV

### LLM Contract Analysis

The application can analyze a contract using an LLM and return structured information:

- Summary
- Risk level
- Key risks
- Recommendations

The LLM is used only for contract analysis. Deterministic business rules such as date validation, spend validation, authorization, and database operations are implemented in Python/SQL.

### Streamlit UI

A Streamlit frontend consumes the FastAPI backend and provides a simple interface for:

- Login
- Viewing contracts
- Creating contracts
- Updating contracts
- Deleting contracts
- Exporting contract data
- Running LLM contract analysis

---

# Architecture

The project follows a layered architecture.

```text
project application/
│
├── app/
│   │
│   ├── main.py
│   │
│   ├── api/
│   │   ├── dependencies.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── contracts.py
│   │       └── vendors.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── exceptions.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   └── models.py
│   │
│   ├── repositories/
│   │   ├── contract_repository.py
│   │   └── vendor_repository.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── contracts.py
│   │   ├── vendors.py
│   │   └── llm.py
│   │
│   ├── services/
│   │   ├── contract_service.py
│   │   ├── vendor_service.py
│   │   └── llm_services.py
│   │
│   └── scripts/
│       └── create_admin.py
│
├── streamlit_app.py
├── .env
├── .env.example
├── requirements.txt
└── README.md
