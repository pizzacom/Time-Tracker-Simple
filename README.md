# ZeitTracker - Full-Stack Time Tracking Application

A modern, full-stack time tracking PWA with overtime management, role-based access control, and multi-format reporting.

## Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│  PostgreSQL  │
│  (nginx/PWA) │     │  (FastAPI)   │     │     (16)     │
│   Port 80    │     │  Port 8000   │     │  Port 5432   │
└──────────────┘     └──────────────┘     └──────────────┘
```

- **Frontend**: Vanilla JS PWA served by nginx (reverse proxies `/api/` to backend)
- **Backend**: FastAPI with async SQLAlchemy, JWT auth, PDF/Excel/CSV export
- **Database**: PostgreSQL 16 with UUID primary keys

## Features

- **Timer**: Start/stop with live tracking, manual entry creation
- **Calendar**: Monthly view with marked work days
- **Overtime**: Automatic Soll/Ist calculation, overtime balance, use-overtime
- **Absences**: Vacation (Urlaub), sick leave (Krank), special leave tracking with budget
- **Reports**: Monthly day-by-day report, PDF/Excel/CSV export
- **Admin Panel**: User/department/holiday management
- **Roles**: Admin, Abteilungsleiter (department leader), Worker
- **PWA**: Installable, offline-capable service worker
- **i18n**: German and English

## Quick Start

### Prerequisites
- Docker & Docker Compose

### Deploy

```bash
# 1. Configure environment
cp .env.example .env   # or edit the existing .env
nano .env               # Set secure passwords and JWT secret

# 2. Start all services
docker compose up -d --build

# 3. Access the app
open http://localhost
```

Default admin: `admin@example.com` / `Admin123!` (change in `.env`)

### Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start PostgreSQL separately, then:
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/zeittracker"
export JWT_SECRET="dev-secret-key"
export ADMIN_EMAIL="admin@example.com"
export ADMIN_PASSWORD="Admin123!"

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
# Serve with any static server
python -m http.server 3000
```

### Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v
```

### Backup

```bash
./backup.sh          # Creates compressed backup in ./backups/
./backup.sh 7        # Keep only last 7 days of backups
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/auth/login` | Login | - |
| POST | `/api/v1/auth/refresh` | Refresh token | Cookie |
| GET | `/api/v1/users/me` | Current user + overtime | Token |
| GET/POST | `/api/v1/users` | List/create users | Admin |
| GET/POST | `/api/v1/entries` | List/create time entries | Token |
| GET | `/api/v1/overtime/balance` | Overtime balance | Token |
| GET | `/api/v1/overtime/history` | Overtime ledger | Token |
| POST | `/api/v1/overtime/use` | Use overtime hours | Token |
| GET/POST | `/api/v1/absences` | List/create absences | Token |
| GET/POST | `/api/v1/departments` | Departments | Admin |
| GET/POST | `/api/v1/holidays` | Holidays | Admin |
| GET/PUT | `/api/v1/schedule/{user_id}` | Work schedule | Admin |
| GET | `/api/v1/reports/monthly` | Monthly report | Token |
| GET | `/api/v1/export/{format}` | PDF/Excel/CSV | Token |
| GET | `/health` | Health check | - |

## Project Structure

```
├── docker-compose.yml
├── .env
├── backup.sh
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── database.py
│       ├── models/        # SQLAlchemy ORM models
│       ├── schemas/       # Pydantic validation schemas
│       ├── routers/       # API route handlers
│       ├── services/      # Business logic
│       ├── middleware/     # Auth middleware
│       └── utils/         # JWT, password, time calculations
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── index.html
│   ├── login.html
│   ├── manifest.json
│   ├── sw.js
│   ├── icons/
│   ├── css/
│   │   ├── styles.css
│   │   └── login.css
│   └── js/
│       ├── app.js         # Main orchestrator
│       ├── api.js         # API client
│       ├── auth.js        # Session management
│       ├── i18n.js        # Translations (DE/EN)
│       ├── utils.js       # Utilities
│       ├── timer.js       # Timer + today entries
│       ├── calendar.js    # Calendar view
│       ├── entries.js     # Entry CRUD
│       ├── reports.js     # Reports + export
│       ├── overtime.js    # Overtime + absences
│       └── admin.js       # Admin panel
└── tests/
    ├── conftest.py
    └── test_api.py
```
