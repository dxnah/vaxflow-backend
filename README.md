# VaxFlow Backend

A Django REST Framework backend for the VaxFlow 
Vaccine Management System.

## About the System
VaxFlow is an ML-assisted vaccine management system 
for Animal Bite Treatment Centers. This backend 
supports both the web admin dashboard and the 
mobile patient app.

## Tech Stack
- Python
- Django
- Django REST Framework
- SQLite (development)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/vaccines/ | List all vaccines |
| POST | /api/vaccines/ | Add a new vaccine |
| GET | /api/vaccines/<id>/ | Get one vaccine |
| GET | /api/announcements/ | List announcements |
| POST | /api/announcements/ | Add announcement |
| GET | /api/patients/ | List all patients |
| POST | /api/login/ | Patient login |
| POST | /api/register/ | Patient registration |

## Models
- **Vaccine** — vaccine inventory and stock status
- **Announcement** — center announcements for patients
- **Patient** — registered patient accounts

## Setup Instructions

### 1. Clone the repository
git clone <your-repo-url>
cd vaxflow-backend

### 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

### 3. Install dependencies
pip install django djangorestframework

### 4. Run migrations
python manage.py migrate

### 5. Run the server
python manage.py runserver

## Testing with httpie
http GET http://127.0.0.1:8000/api/vaccines/
http POST http://127.0.0.1:8000/api/login/ username="patient1" password="pass123"
