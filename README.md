# VaxFlow — Vaccine Inventory & Patient Management System

<p align="center">
  <img src="src/images/logoit.png" alt="VaxFlow Logo" width="80"/>
</p>

<p align="center">
  <b>A full-stack web application for managing anti-rabies vaccine inventory, patient records, demand forecasting, and health center operations.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-18.2.0-61DAFB?logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.136.0-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Deployed-Vercel-000000?logo=vercel&logoColor=white" />
</p>

---

## Overview

VaxFlow is a full-stack vaccine management system designed for health facilities managing Anti-Rabies Vaccine (ARV) inventory and patient vaccination records. This repository contains the **FastAPI backend** that powers the web application.

The frontend (React + React Router DOM) is hosted separately at → [dxnah/VaxFlow](https://github.com/dxnah/VaxFlow)
The backend repository is at → [dxnah/vaxflow-backend](https://github.com/dxnah/vaxflow-backend)

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.136+ |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL (via Supabase) |
| ML Model | scikit-learn (Ridge Regression) |
| Data Processing | pandas, numpy |
| Runtime | Python 3.11 |
| Server | Uvicorn |
| Validation | Pydantic v2 |

---

## Project Structure

```
vaxflow-backend/
├── fast_api/
│   ├── main.py                          # FastAPI app, all REST endpoints
│   ├── models.py                        # SQLAlchemy ORM models
│   ├── schemas.py                       # Pydantic request/response schemas
│   ├── database.py                      # DB engine & session setup
│   ├── ml_forecast.py                   # ML forecast router & prediction logic
│   ├── vaxflow_arv_model.pkl            # Trained Ridge Regression model
│   ├── vaxflow_forecast_monthly.json    # Pre-generated monthly forecast data
│   ├── vaxflow_forecast_nested.json     # Pre-generated nested forecast data
│   ├── vaxflow_synthesized_dataset_final.xlsx  # Training dataset
│   ├── vaxflow_ml.ipynb                 # ML training notebook
│   └── vaxflow_retrain.ipynb            # Model retraining notebook
├── requirements.txt
├── .env                                 # Environment variables (not committed)
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.11
- PostgreSQL database (or a Supabase project)
- `pip` or a virtual environment manager

### Installation

```bash
# Clone the repository
git clone https://github.com/dxnah/vaxflow-backend.git
cd vaxflow-backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<dbname>?sslmode=require
```

For Supabase, the connection string format is:
```
postgresql://postgres.<project-ref>:<password>@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres?sslmode=require
```

### Running the API

```bash
# From the project root
uvicorn fast_api.main:app --reload
```

The API will be available at `http://localhost:8000`.
Interactive docs (Swagger UI) are at `http://localhost:8000/docs`.

---

## API Reference

All endpoints are prefixed with `/api/`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/login/` | Login for patients and admin users |
| POST | `/api/signup/` | Register a new patient account |

### Patients

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/patients/` | List all patients |
| GET | `/api/patients/{id}/` | Get a single patient |
| PUT | `/api/patients/{id}/` | Update patient details |
| DELETE | `/api/patients/{id}/` | Delete a patient |

### Vaccines & Batches

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/vaccines/` | List or create vaccines |
| GET/PUT/DELETE | `/api/vaccines/{id}/` | Manage a specific vaccine |
| GET/POST | `/api/batches/` | List or create vaccine batches |
| PUT/DELETE | `/api/batches/{id}/` | Manage a specific batch |

### Vaccination Records

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/vaccination-history/` | All vaccination history |
| GET | `/api/vaccination-history/patient/{id}/` | History by patient |
| PUT/DELETE | `/api/vaccination-history/{id}/` | Manage a record |
| GET/POST | `/api/dose-schedules/` | Dose schedule management |
| GET | `/api/dose-schedules/patient/{id}/` | Schedules by patient |

### Patient Registrations

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/registrations/` | All bite/exposure registrations |
| GET | `/api/registrations/patient/{id}/` | Registrations by patient |
| PUT/DELETE | `/api/registrations/{id}/` | Manage a registration |

### Inventory & Orders

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/suppliers/` | Supplier management |
| PUT/DELETE | `/api/suppliers/{id}/` | Manage a supplier |
| GET/POST | `/api/orders/` | Vaccine orders |
| PUT/DELETE | `/api/orders/{id}/` | Manage an order |

### Reports

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/usage-reports/` | Vaccine usage reports |
| PUT/DELETE | `/api/usage-reports/{id}/` | Manage a usage report |
| GET/POST | `/api/stock-reports/` | Stock level reports |
| PUT/DELETE | `/api/stock-reports/{id}/` | Manage a stock report |

### Notifications & Announcements

| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/notifications/` | Notification management |
| POST | `/api/notifications/mark_all_read/` | Mark all as read |
| DELETE | `/api/notifications/clear_all/` | Clear all notifications |
| GET/POST | `/api/announcements/` | Announcement management |

---

## ML Forecast Module

The ML module (`/api/ml/`) provides ARV demand forecasting using a trained **Ridge Regression** model. It uses a synthesized dataset with 30+ features including weather data, epidemiological indicators, and historical dose records.

### ML Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/ml/forecast/` | Full forecast data (filterable by year/month) |
| GET | `/api/ml/forecast/years/` | List of available forecast years |
| GET | `/api/ml/forecast/year/{year}/` | All 12-month predictions for a year |
| GET | `/api/ml/forecast/summary/` | Yearly aggregate summary |
| GET | `/api/ml/forecast/metrics/` | Model evaluation metrics (R², MAPE) |
| POST | `/api/ml/predict/` | Predict ARV demand for a given year & month |
| POST | `/api/ml/actuals/` | Submit actual dose data (triggers model retraining) |

### Prediction Example

```http
POST /api/ml/predict/?year=2026&month=6
```

Response:
```json
{
  "input": { "year": 2026, "month": 6, "monthName": "June" },
  "prediction": {
    "predicted_doses": 1712,
    "recommended_order": 1917,
    "safety_buffer_pct": 12,
    "unit": "ARV doses"
  },
  "model_info": {
    "model_name": "Ridge",
    "test_r2": 0.94,
    "test_mape": 4.2
  }
}
```

The `recommended_order` adds a **12% safety buffer** on top of the predicted demand.

### Auto-Retraining

When actual dose data is submitted via `POST /api/ml/actuals/`, the model retrains automatically in the background using the updated dataset — no manual intervention or notebook execution required.

### Model Features

The Ridge Regression model uses 40+ features grouped into:

- **Epidemiological** – bite cases (Categories 1/2/3), PEP completion rate, rabies confirmation rate
- **Environmental** – temperature, rainfall, humidity, heat index, breeding season cycle
- **Operational** – stockout flag, RIG availability, cold chain capacity, procurement delay
- **Socio-demographic** – dog population, urban density, poverty index, stray density
- **Temporal** – lag features (1, 2, 3, 6, 12 months), rolling averages, month sin/cos encoding

---

## Database Models

| Model | Table | Description |
|---|---|---|
| `Vaccine` | `api_vaccine` | Vaccine catalog with stock levels and ML recommendations |
| `VaccineBatch` | `api_vaccinebatch` | Batch tracking with expiry and supplier info |
| `Supplier` | `api_supplier` | Supplier contact and lead time management |
| `Patient` | `api_patient` | Patient accounts and profiles |
| `AdminUser` | `auth_user` | Admin/staff accounts (Django-compatible table) |
| `Registration` | `api_registration` | Bite/animal exposure registration records |
| `DoseSchedule` | `api_doseschedule` | Per-patient dose schedule tracking |
| `VaccinationHistory` | `api_vaccinationhistory` | Completed vaccination records |
| `VaccineOrder` | `api_vaccineorder` | Purchase orders with status tracking |
| `VaccineUsageReport` | `api_vaccineusagereport` | Monthly usage, waste, and remaining stock |
| `StockLevelReport` | `api_stocklevelreport` | Aggregate in/low/out-of-stock snapshots |
| `Notification` | `api_notification` | System alerts and notifications |
| `Announcement` | `api_announcement` | Public-facing health announcements |

---

## CORS Configuration

The API allows requests from the following origins:

- `http://localhost:3000` (local frontend development)
- `https://vaxflow-seven.vercel.app` (production frontend)

To add a new allowed origin, update the `allow_origins` list in `fast_api/main.py`.

---

## Deployment

| Layer | Platform | URL |
|---|---|---|
| Backend API | Render | https://vaxflow-backend.onrender.com |
| Frontend | Vercel | https://vaxflow-seven.vercel.app |

The backend is deployed on **Render**. A few things to note:

- Set `DATABASE_URL` as an environment variable in the Render service dashboard — the `.env` file is **not committed** to version control.
- Database connections use connection pooling (`pool_size=5`, `max_overflow=2`, `pool_pre_ping=True`) suited for Render's environment.
- The ML model (`.pkl`), forecast JSON files, and training dataset (`.xlsx`) must be present in the `fast_api/` directory at runtime.
- Render's free tier spins down after inactivity — expect a cold start delay on the first request.

---

## Related Repository

- **Frontend (React + React Router DOM):** [github.com/dxnah/VaxFlow](https://github.com/dxnah/VaxFlow)
- **Frontend Mobile (React Native):** [github.com/dxnah/VaxFlowMobile](https://github.com/dxnah/VaxFlowMobile)

---

## Team

*IT323 — Application Development and Emerging Technologies*

Built as a final project demonstrating full-stack development, REST API design, database modeling, and ML integration.


---

<p align="center">Made with 💉 by the VaxFlow Team</p>
