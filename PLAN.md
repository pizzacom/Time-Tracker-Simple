# Time-Tracker Full-Stack Expansion Plan

**Created**: 10. Februar 2026  
**Status**: Planned  
**TL;DR**: Transform the existing client-side-only PWA time tracker into a full-stack application with a Python (FastAPI) backend, PostgreSQL database, JWT authentication, role-based access (Admin/Abteilungsleiter/Worker), Überstunden/Minusstunden management, Soll-Arbeitszeit tracking with holiday awareness, multi-format export (PDF/CSV/Excel), and Docker deployment. The frontend remains vanilla JS/HTML/CSS but is restructured to communicate with the REST API.

---

## Part 1: Current Project Description

The existing app at [app.js](app.js) (~1384 lines) is a **bilingual (DE/EN) PWA time-tracking app** built with pure vanilla JS/HTML/CSS. 

### Current Features

- **Live timer** with start/stop/reset, persisted across reloads via `localStorage`
- **Manual entry creation** with date, start/end time, break duration, description
- **Calendar view** with green-dot indicators for days with entries
- **Monthly reports** with summary cards (work days, total hours, total breaks, avg/day)
- **PDF export** via jsPDF + autoTable (monthly timesheet with every day listed)
- **CSV export** (semicolon-delimited, UTF-8 BOM)
- **JSON backup/restore** with merge/replace import modes
- **Settings**: user name, company name, default break
- **Dark/light theme**, **DE/EN language toggle** via `data-i18n` attributes
- **PWA**: service worker with cache-first strategy, manifest for standalone install

### Data Storage

All data in `localStorage` under `zeittracking_*` keys. Entry model: `{ id, date, startTime, endTime, breakMinutes, description, workMinutes }`.

### Notable Limitations

- No authentication, no server, no multi-user support
- No overtime tracking or target working hours
- PDF only shows last entry per day (bug)
- No cross-midnight support
- XSS risk via unsanitized `innerHTML`
- Hardcoded German strings in code bypassing i18n
- Cannot track Soll vs Ist (target vs actual hours)
- No role-based access (boss/worker distinction)
- No data persistence beyond single browser

---

## Part 2: Expansion Plan - 8 Phases

### Phase 1: Backend Foundation (API Server + Database)

#### 1.1 Project Structure (Monorepo)

```
Time-Tracker/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry, initialization
│   │   ├── config.py            # Settings (env vars, DB URL, JWT secret)
│   │   ├── database.py          # SQLAlchemy async engine + session factory
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User, roles
│   │   │   ├── department.py    # Abteilung / Department
│   │   │   ├── time_entry.py    # Time entry with entry_type
│   │   │   ├── overtime.py      # Overtime ledger
│   │   │   ├── work_schedule.py # Soll-Arbeitszeit (target hours)
│   │   │   ├── holiday.py       # Company holidays (Feiertage)
│   │   │   ├── absence.py       # Urlaub, Krank, Sonderurlaub
│   │   │   └── vacation_budget.py # Yearly vacation day entitlement
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   │   ├── user.py
│   │   │   ├── entry.py
│   │   │   ├── overtime.py
│   │   │   └── ... (etc)
│   │   ├── routers/             # API route modules
│   │   │   ├── auth.py          # Login, refresh, logout
│   │   │   ├── entries.py       # CRUD time entries
│   │   │   ├── overtime.py      # Überstunden tracking & usage
│   │   │   ├── absences.py      # Urlaub, Krank management
│   │   │   ├── reports.py       # Monthly reports, Soll vs Ist
│   │   │   ├── users.py         # User profiles & management
│   │   │   ├── departments.py   # Department management
│   │   │   └── export.py        # PDF/CSV/Excel generation
│   │   ├── services/            # Business logic
│   │   │   ├── overtime_service.py
│   │   │   ├── work_schedule_service.py
│   │   │   ├── export_service.py
│   │   │   └── ...
│   │   ├── middleware/          # Auth middleware, CORS, logging
│   │   │   ├── auth.py
│   │   │   └── cors.py
│   │   └── utils/               # Helpers
│   │       ├── time_calc.py     # Time calculations
│   │       ├── password.py      # Hashing
│   │       └── jwt.py           # Token generation
│   ├── alembic/                 # DB migrations (auto-generated)
│   ├── tests/                   # pytest test suite
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile              # Python 3.12 slim + uvicorn
│   ├── .env.example            # Template for environment variables
│   └── .gitignore
├── frontend/                    # Refactored vanilla JS app
│   ├── index.html              # Main app (protected, requires login)
│   ├── login.html              # Login page
│   ├── css/
│   │   ├── styles.css          # Main styles (keep existing, enhance)
│   │   └── login.css           # Login page styles
│   ├── js/
│   │   ├── api.js              # API client (fetch wrapper with JWT)
│   │   ├── auth.js             # Login/logout/token management
│   │   ├── app.js              # Main app logic (refactored from original)
│   │   ├── timer.js            # Timer functionality
│   │   ├── calendar.js         # Calendar view
│   │   ├── reports.js          # Reports & Soll vs Ist
│   │   ├── overtime.js         # Überstunden UI & ledger
│   │   ├── admin.js            # Boss/admin views
│   │   ├── i18n.js             # Translation system (keep existing pattern)
│   │   └── utils.js            # Helpers
│   ├── icons/                  # Existing PWA icons
│   ├── sw.js                   # Service worker (with API sync)
│   ├── manifest.json           # PWA manifest
│   ├── Dockerfile              # nginx:alpine + reverse proxy
│   └── nginx.conf              # nginx configuration
├── docker-compose.yml          # PostgreSQL + Backend + Frontend
├── .env.example                # Root env template
└── PLAN.md                     # This file
```

#### 1.2 Database Schema (PostgreSQL)

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  role ENUM('admin', 'abteilungsleiter', 'worker') NOT NULL DEFAULT 'worker',
  department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (email),
  INDEX (department_id),
  INDEX (role)
);

-- Departments (Abteilungen)
CREATE TABLE departments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  leader_id UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (name),
  INDEX (leader_id)
);

-- Time Entries
CREATE TABLE time_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  break_minutes INT NOT NULL DEFAULT 0,
  description TEXT,
  work_minutes INT NOT NULL, -- Computed: (end - start) - break_minutes
  entry_type ENUM('regular', 'overtime_used') DEFAULT 'regular',
  -- Note: Urlaub/Krank are tracked in 'absences' table, not as time entries
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (user_id, date),
  INDEX (date),
  CONSTRAINT work_time_positive CHECK (work_minutes >= 0)
);

-- Work Schedules (Soll-Arbeitszeit per worker, with date ranges)
CREATE TABLE work_schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  valid_from DATE NOT NULL,
  valid_until DATE, -- NULL = still active
  monday_minutes INT NOT NULL DEFAULT 480,    -- 8 hours
  tuesday_minutes INT NOT NULL DEFAULT 480,
  wednesday_minutes INT NOT NULL DEFAULT 480,
  thursday_minutes INT NOT NULL DEFAULT 480,
  friday_minutes INT NOT NULL DEFAULT 480,
  saturday_minutes INT NOT NULL DEFAULT 0,
  sunday_minutes INT NOT NULL DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (user_id, valid_from),
  CONSTRAINT valid_dates CHECK (valid_until IS NULL OR valid_until >= valid_from)
);

-- Overtime Ledger (immutable, append-only for audit trail)
CREATE TABLE overtime_ledger (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  minutes INT NOT NULL, -- Positive = earned, Negative = used/adjusted
  reason ENUM('earned', 'used', 'adjustment') NOT NULL,
  related_time_entry_id UUID REFERENCES time_entries(id) ON DELETE SET NULL, -- Links to the entry that triggered this
  note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- NOT updated; immutable
  INDEX (user_id, date),
  INDEX (user_id, reason)
);

-- Holidays (Public holidays, company-wide)
CREATE TABLE holidays (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date DATE NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  is_half_day BOOLEAN DEFAULT false,
  region VARCHAR(50), -- Optional: for Bundesland-specific holidays
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (date)
);

-- Absences (Urlaub, Krank, etc. per worker)
CREATE TABLE absences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  type ENUM('urlaub', 'krank', 'sonderurlaub') NOT NULL, -- vacation, sick, special leave
  note TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, date), -- One absence type per day per user
  INDEX (user_id, date),
  INDEX (type)
);

-- Vacation Budgets (yearly vacation day entitlement per worker)
CREATE TABLE vacation_budgets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  year INT NOT NULL,
  total_days INT NOT NULL DEFAULT 30, -- Yearly vacation entitlement
  used_days INT NOT NULL DEFAULT 0, -- Computed/cached from absences table
  remaining_days INT GENERATED ALWAYS AS (total_days - used_days) STORED,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, year),
  INDEX (user_id, year)
);

-- Settings (Global company config)
CREATE TABLE settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key VARCHAR(255) NOT NULL UNIQUE,
  value TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX (key)
);
```

#### 1.3 Implement FastAPI Backend

**Dependencies** (`requirements.txt`):
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
alembic==1.13.1
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-dotenv==1.0.0
slowapi==0.1.9
openpyxl==3.11.0
reportlab==4.0.7
pytz==2023.3
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

**Key features**:
- Use **SQLAlchemy 2.0** (async) with **asyncpg** for PostgreSQL
- **Alembic** for schema versioning (initialize with `alembic init alembic` in backend/)
- **JWT authentication**: 15-min access token + 7-day refresh token
- **Password hashing**: `bcrypt` via `passlib`
- **CORS middleware** for frontend origin
- **Role-based access control** via `Depends()` decorator pattern
- **Error handling**: Custom `HTTPException` with proper status codes
- **Logging**: Python `logging` module to stderr

#### 1.4 API Endpoints (RESTful, all prefixed `/api/v1`)

| Method | Endpoint | Auth Required | Role | Description |
|--------|----------|---|---|-------------|
| **Authentication** |
| POST | `/auth/login` | — | — | Login with email/password, returns access_token + refresh_token (httpOnly cookie) |
| POST | `/auth/refresh` | Refresh token | any | Refresh access token |
| POST | `/auth/logout` | any | any | Invalidate refresh token |
| **User Profile** |
| GET | `/users/me` | any | any | Get own user profile + Überstunden balance |
| PUT | `/users/me` | any | any | Update own profile (name, company info) |
| **User Management (Admin only)** |
| GET | `/users` | admin | admin | List all users with filters |
| POST | `/users` | admin | admin | Create new user account |
| PUT | `/users/{user_id}` | admin | admin | Edit user (role, department, active status) |
| DELETE | `/users/{user_id}` | admin | admin | Deactivate user |
| **Department Management (Admin/Abteilungsleiter)** |
| GET | `/departments` | admin | admin/abteilungsleiter | List departments (admin: all, boss: own) |
| POST | `/departments` | admin | admin | Create department |
| PUT | `/departments/{dept_id}` | admin | admin | Edit department |
| **Time Entries** |
| GET | `/entries` | any | any | Get own entries (filterable: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD) |
| POST | `/entries` | any | any | Create time entry |
| PUT | `/entries/{entry_id}` | any | any | Edit own entry |
| DELETE | `/entries/{entry_id}` | any | any | Delete own entry (with soft-delete option for audit) |
| GET | `/entries/user/{user_id}` | abteilungsleiter | abteilungsleiter/admin | Get worker's entries (boss can only see own dept) |
| **Work Schedule (Soll-Arbeitszeit)** |
| GET | `/schedule` | any | any | Get own current work schedule (Mon-Sun hours) |
| GET | `/schedule/user/{user_id}` | abteilungsleiter | abteilungsleiter/admin | Get worker's schedule |
| POST | `/schedule` | any | any | Create/update own schedule (worker self-service) |
| PUT | `/schedule/user/{user_id}` | abteilungsleiter | abteilungsleiter/admin | Set worker's schedule (boss/admin) |
| **Overtime (Überstunden/Minusstunden)** |
| GET | `/overtime/balance` | any | any | Get own Überstunden balance (SUM of ledger) |
| GET | `/overtime/history` | any | any | Get own overtime ledger (list of all earn/use/adjust events) |
| POST | `/overtime/use` | any | any | Use Überstunden: apply earned overtime to a day as credited work time |
| GET | `/overtime/user/{user_id}` | abteilungsleiter | abteilungsleiter/admin | Get worker's balance & history |
| **Holidays (Feiertage)** |
| GET | `/holidays` | any | any | Get holidays for a year (default: current year) |
| POST | `/holidays` | admin | admin | Add holiday (with optional import from public holiday API) |
| DELETE | `/holidays/{holiday_id}` | admin | admin | Remove holiday |
| **Absences (Urlaub/Krank)** |
| GET | `/absences` | any | any | Get own absences (filterable by year, type) |
| POST | `/absences` | any | any | Mark a day as Urlaub/Krank (self-service) |
| DELETE | `/absences/{absence_id}` | any | any | Remove own absence marking |
| GET | `/absences/user/{user_id}` | abteilungsleiter | abteilungsleiter/admin | Get worker's absences |
| GET | `/vacation-budget` | any | any | Get own vacation day budget (total/used/remaining) |
| PUT | `/vacation-budget/{user_id}` | admin | admin | Set worker's yearly vacation day entitlement |
| **Reports & Analytics** |
| GET | `/reports/monthly` | any | any | Get own monthly report (Soll vs Ist comparison, detailed day-by-day) |
| GET | `/reports/monthly/{user_id}` | abteilungsleiter | abteilungsleiter/admin | Get worker's monthly report |
| GET | `/reports/department/{dept_id}` | abteilungsleiter | abteilungsleiter/admin | Department overview (all workers with summary) |
| GET | `/reports/summary` | admin | admin | System-wide summary |
| **Exports** |
| GET | `/export/pdf` | any | any | Export own monthly PDF (query: ?year=2026&month=2) |
| GET | `/export/pdf/{user_id}` | abteilungsleiter | abteilungsleiter/admin | Export worker's PDF |
| GET | `/export/csv` | any | any | Export own data as CSV |
| GET | `/export/csv/{user_id}` | abteilungsleiter | abteilungsleiter/admin | Export worker's CSV |
| GET | `/export/excel` | any | any | Export own data as Excel (.xlsx) |
| GET | `/export/excel/{user_id}` | abteilungsleiter | abteilungsleiter/admin | Export worker's Excel |
| GET | `/export/department/{dept_id}/excel` | abteilungsleiter | abteilungsleiter/admin | Export department as Excel (one sheet per worker + summary) |

---

### Phase 2: Authentication & User Management

#### 2.1 Login Page

Create [frontend/login.html](frontend/login.html):
- Simple form with email + password fields
- Company branding / logo space
- "Remember me" checkbox (optional, for browser security)
- Error message display
- Loading state during login
- i18n support (DE/EN toggle)
- Responsive design (mobile-first)

#### 2.2 API Client (`api.js`)

Wrapper around `fetch()` that:
- Automatically attaches `Authorization: Bearer <access_token>` header to requests
- Handles 401 responses: attempts token refresh → retries original request
- On refresh failure (401): redirects to login page
- Provides convenience methods: `api.get()`, `api.post()`, `api.put()`, `api.delete()`
- Base URL from environment or config (e.g., `/api/v1`)
- Proper error handling with custom error class for UI display

#### 2.3 Auth Module (`auth.js`)

Handles:
- Login form submission (email + password)
- Token storage: access_token in memory, refresh_token in httpOnly cookie (set by server)
- Automatic session check on app load (`GET /users/me`)
- Logout (clears tokens, redirects to login)
- Session timeout handling
- "Protected page" redirect (if not authenticated, redirect to login)

#### 2.4 Admin/Boss Account Management

**Admin panel** (new tab or separate `/admin` route, accessible only to `admin` role):

1. **User Management**:
   - Table of all users with: email, name, role, department, active status
   - Create user modal: email, name, department, role, generate initial password
   - Edit user: role, department, active status
   - Deactivate user (soft delete)
   - Password reset: generate temporary password, send via... (email backend not in scope for Phase 1)

2. **Department Management**:
   - Table of departments with: name, leader, member count
   - Create department: name, select Abteilungsleiter
   - Edit department: name, leader assignment
   - Delete department (cascades or prevents if has members)

3. **Holiday Management (Feiertage)**:
   - Calendar view or table of holidays
   - Add holiday: date, name, optional half-day flag
   - Remove holiday
   - Import German public holidays: select Bundesland, auto-populate

4. **Absence Management (Urlaub/Krank)**:
   - View/manage absences for workers in own department (Abteilungsleiter)
   - Admin can see all absences across departments
   - Set yearly vacation day budget per worker (default: 30 days)
   - Overview: who is absent today, this week, this month

5. **Data Deletion (Admin only)**:
   - Select year (or year + month) to delete all time entries for that period for all users
   - Safety checks: preview count of affected entries, type confirmation phrase (e.g., "DELETE 2024"), re-enter admin password
   - Audit log entry created before deletion (records what was deleted, by whom, when)

---

### Phase 3: Refactor Frontend for API Integration

#### 3.1 Replace localStorage with API Calls

Refactor the existing [app.js](app.js) logic:
- Remove `loadState()` → call `api.get('/users/me')` + `api.get('/entries?...')`
- Remove `saveEntry()` → call `api.post('/entries')` or `api.put('/entries/{id}')`
- Remove `deleteEntry()` → call `api.delete('/entries/{id}')`
- Keep `localStorage` only for: theme preference, language preference, timer state (pure client-side)
- Handle loading/error states for all API calls with toasts

#### 3.2 Module Organization (ES Modules, no build step)

Split [app.js](app.js) into:
- `api.js` — fetch wrapper, all API calls
- `auth.js` — login/logout, session management
- `app.js` — main app initialization, tab switching
- `timer.js` — timer logic (unchanged, but sync with API on save)
- `calendar.js` — calendar rendering, date selection
- `entries.js` — CRUD operations for time entries
- `reports.js` — monthly report generation, calculations
- `overtime.js` — Überstunden UI, ledger display
- `admin.js` — admin panel (user/dept/holiday management)
- `i18n.js` — translation system (keep existing pattern)
- `utils.js` — time formatting, calculations

Use `type="module"` in `index.html` script tags:
```html
<script type="module">
  import('./js/app.js').then(module => module.init());
</script>
```

#### 3.3 Fix Existing Bugs During Refactor

1. **PDF multi-entry-per-day bug**: Change `entriesMap` to use array values instead of single object
2. **XSS vulnerability**: Replace all unsafe `innerHTML` with `textContent` or a `DOMPurify`-like sanitizer
3. **Calendar weekday labels**: Fix `data-i18n` attribute mappings (Sunday should be Sunday, etc.)
4. **Hardcoded German strings**: Move all non-translated strings to `translations` object (PDF labels, error messages, etc.)
5. **Support for multiple entries per day in reports**: Change rendering to loop through entries per day instead of single-entry assumption

---

### Phase 4: Soll-Arbeitszeit & Überstunden/Minusstunden

#### 4.1 Soll-Arbeitszeit (Target Hours) Feature

**Data Model**:
- Each worker has a `work_schedule` record with `valid_from`/`valid_until` (allows schedule changes: full-time → part-time)
- Per-weekday hours: Monday-Sunday (e.g., Mon-Fri 8h, Sat-Sun 0h)
- Support multiple active schedules with date ranges (resolved by finding the schedule that contains requested date)
- Holidays (Feiertage) reduce Soll for that day to 0 (checked via `holiday.is_half_day` if applicable)
- Absences (Urlaub, Krank) also reduce Soll to 0 for that day — no Minusstunden generated
- Days marked as Urlaub count against the worker's yearly vacation budget

**UI**:
1. **Worker's "Arbeitszeit" Settings** (in profile or dedicated tab):
   - Display current schedule (Mon-Sun target hours)
   - Option to create new schedule with different hours and effective date
   - History of past schedule changes (read-only)

2. **Admin/Boss Schedule Management**:
   - Set worker's schedule from admin panel
   - Effective date selection (for future schedule changes)
   - Quick templates: "Vollzeit" (8h/day), "Teilzeit" (4h/day), custom

#### 4.2 Monthly Soll vs Ist Dashboard

Enhance **Reports tab** with new section:

**Layout**:
- **Month summary card**:
  - Soll gesamt (sum of daily Soll for all working days in month)
  - Ist gesamt (sum of all time entries in month)
  - Saldo (Ist - Soll, positive = Überstunden, negative = Minusstunden)
  - Current Überstunden balance (link to ledger)

- **Daily breakdown table**:
  - Columns: Date | Weekday | Soll | Ist | Entry Count | Delta | Entries | Überstunden Used | Note
  - Soll & Ist color-coded: Green (on target: -2h to +2h), Red (under -2h), Blue (over +2h)
  - Click "Entries" to expand and show all entries for that day
  - Delta automatically shows if Überstunden were used (e.g., "8h (2h used)")

- **Action**: "Überstunden einlösen" button (see 4.3 below)

#### 4.3 Überstunden Ledger & Usage

**Data Model**:
- `overtime_ledger`: immutable, append-only
- Each row is an event: (date, user_id, minutes, reason, note)
- Balance = `SUM(minutes)` where `user_id = ?` (always correct, no desync)
- Reasons: `earned` (auto-added if Ist > Soll), `used` (worker applied overtime to a day), `adjustment` (admin override)

**Automatic Earning**:
- When time entries are saved/updated, backend calculates: if `sum(work_minutes)` for day > `soll_minutes` for that day, the difference is added to ledger as `earned`
- Alternatively: cron job at EOD to batch-process daily earnings

**Worker Usage ("Überstunden einlösen")**:

UI Flow:
1. Worker opens reports tab, sees Überstunden balance prominently
2. Clicks "Überstunden einlösen" or selects a Minusstunden day (red) and clicks "Mit Überstunden decken"
3. Modal appears:
   - Select date to apply overtime to
   - Input number of hours to use
   - Confirmation
4. Backend:
   - Validates: worker has sufficient balance
   - Creates `overtime_used` `time entry` for that date (work_minutes = used_hours)
   - Creates `overtime_ledger` entry with `reason = 'used'`, negative minutes
   - Summary is updated: delta becomes less negative or positive
5. Frontend updates in real-time; entry list for that day now shows the credited time

**Constraints**:
- Cannot use more Überstunden than balance (checked client + server)
- Cannot use Überstunden retroactively beyond a configurable cutoff (e.g., 6 months old), unless admin overrides
- Budget guard: if Überstunden would drop below 0, reject or warn

#### 4.4 Minusstunden Handling

**Definition**: Days where Ist < Soll.

**Visual Indicators**:
- Daily report: delta shown in red
- Summary: negative Saldo

**Covering Minusstunden**:
- Worker can retroactively use Überstunden to cover a past Minusstunden day
- Or leave it: accumulated Minusstunden are tracked and may be enforced by boss (e.g., "catch up this month")

**Boss Report**:
- Boss sees worker's Minusstunden on the department overview
- Can flag for follow-up or approve "catch-up" later date

---

### Phase 5: Boss/Abteilungsleiter Views

#### 5.1 Department Overview Page

**Route**: `/dashboard` or new "Team" tab (if Abteilungsleiter role).

**Layout**:
- **Team members list** with:
  - Name
  - Today's status: "Working" (timer running), "On break", "Finished", "Not started"
  - Current month Soll vs Ist (progress bar)
  - Überstunden balance (color: green if positive, red if negative/Minusstunden)
  - Last entry: timestamp + description snippet
  - Action buttons: "View full report", "Weekly summary", "Export"

- **Traffic light indicators** (quick health check):
  - Green: on target (within 2h of Soll)
  - Yellow: slight deviation (2-4h)
  - Red: significant under/over (>4h)

- **Team summary card**:
  - Total team members
  - Average daily Ist vs Soll
  - Team Überstunden balance
  - Late entries (not yet submitted for the day)

#### 5.2 Worker Report (for Boss)

**Route**: `/workers/{user_id}/report`, accessible to Abteilungsleiter (and admin).

**Same layout as worker's own report**, but:
- Read-only (no edit buttons) — no approval workflow, entries are immediately active
- Additional columns: entry creation time, edit timestamp
- Audit trail: shows edit history for each entry (what was changed, when)
- Boss can add notes/comments to days or entries
- Boss can manually adjust Überstunden (with reason + audit log)

#### 5.3 Department Export

**Routes**: All from `/export/department/{dept_id}`:

- **`/export/department/{dept_id}/excel`**:
  - Excel file with multiple sheets: one per worker, plus summary sheet
  - Each worker sheet: identical format to PDF export, but in Excel with formulas for totals
  - Summary sheet: table with all workers, their Soll/Ist/Balance, department total

- **`/export/department/{dept_id}/csv`** (optional):
  - Single CSV file with `worker_name | date | start | end | ...` rows

#### 5.4 Admin Dashboard

**Route**: `/admin`, accessible only to `admin` role.

**Sections**:

1. **System Overview**:
   - Total users, departments, entries (count + growth graph)
   - Current month stats: total Ist, total Soll, team Überstunden
   - Recent activity log (user creation, entry edits, etc.)

2. **User Management** (see Phase 2.4)

3. **Department Management** (see Phase 2.4)

4. **Holiday Management** (see Phase 2.4)

5. **Settings**:
   - Company name, default break duration
   - Max retroactive Überstunden usage (days)
   - Audit log retention
   - Export templates
   - Time zone (default: `Europe/Berlin`)
   - Default yearly vacation days for new employees

---

### Phase 6: Export Enhancements

#### 6.1 PDF Export (Server-Side)

Replace client-side jsPDF with server-side generation using Python `reportlab`:

**Features**:
- **Professional layout**:
  - Header: company logo (if provided), company name, worker name, month/year
  - Signature lines at bottom for worker + boss approval (print-only)
  
- **Content**:
  - Calendar grid: one row per day (including empty days)
  - Columns: Date | Weekday | Soll | Start | End | Break | Ist | Delta | Entry Type | Description
  - Proper multi-entry-per-day support: list all entries for a day with subtotal
  
- **Summary section**:
  - Total Soll (month)
  - Total Ist (month)
  - Total Überstunden earned (month)
  - Überstunden used (month)
  - Starting balance (1st of month)
  - Ending balance (last day of month)
  - Running balance per day (optional detail column)

- **Footer**:
  - Generated date/time
  - Page number (if multi-page)
  - Watermark option ("DRAFT" or "APPROVED")

- **Endpoint**: `GET /export/pdf?year=2026&month=2`

#### 6.2 CSV Export (Server-Side)

Enhanced version using Python's `csv` module:

**Features**:
- UTF-8 with BOM (Excel compatibility)
- Proper delimiter handling (`,` or `;`)
- Columns: Date | Weekday | Start | End | Break (min) | Work (min) | Soll (min) | Delta (min) | Entry Type | Description
- One row per time entry (not per day)
- Summary rows at end: `TOTAL | | | | | ∑Work | ∑Soll | ∑Delta`
- Handling of special characters in descriptions (quotes, newlines)

- **Endpoint**: `GET /export/csv?year=2026&month=2`

#### 6.3 Excel Export (Server-Side)

Using Python `openpyxl`:

**Features**:
- **.xlsx** format (modern Excel)
- **Sheet 1 "Zeiterfassung" (Timesheet)**:
  - Header with company/worker info
  - Table with: Date | Weekday | Start | End | Break | Work | Soll | Delta | Type | Description
  - Styled: alternating row colors, bold headers, borders
  - **Formulas**: Total row at end uses `SUM()` formulas (so Excel file is self-calculating)
  - Conditional formatting: cells with negative Delta (red), positive (green), Überstunden used (blue)
  - Frozen header row

- **Sheet 2 "Überstunden"**:
  - Summary of Überstunden balance
  - Ledger table: Date | Reason | Minutes | Running Balance
  - Current balance highlighted

- **Sheet 3 "Soll-Übersicht"** (optional):
  - Daily Soll breakdown per weekday
  - Holiday list
  - Schedule changes if applicable

- **Endpoint**: `GET /export/excel?year=2026&month=2`

- **Department Export** (for boss):
  - Separate sheet per worker (dynamically added)
  - Summary sheet with all workers in rows

#### 6.4 Export Dialog

**Frontend UI**:
- New "Export" button in Reports tab
- Modal with options:
  - Format: PDF / CSV / Excel (radio buttons)
  - Month/Year: date pickers
  - Include schedule details? Include Überstunden ledger? (checkboxes)
  - Download or email link?
- Generates file server-side, returns as download

---

### Phase 7: Docker Deployment

#### 7.1 Docker Compose Setup

**`docker-compose.yml`** (at repo root):

```yaml
version: '3.9'

services:
  db:
    image: postgres:16-alpine
    container_name: timetracker-db
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    ports:
      - "5432:5432"  # Only expose for local dev; remove in production

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: timetracker-api
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      JWT_SECRET: ${JWT_SECRET}
      JWT_ALGORITHM: HS256
      JWT_ACCESS_EXPIRE_MINUTES: 15
      JWT_REFRESH_EXPIRE_DAYS: 7
      ADMIN_EMAIL: ${ADMIN_EMAIL}
      ADMIN_PASSWORD: ${ADMIN_PASSWORD}
      CORS_ORIGINS: ${CORS_ORIGINS}
      LOG_LEVEL: ${LOG_LEVEL}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s
      timeout: 5s
      retries: 5
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app  # For hot-reload in dev

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: timetracker-web
    depends_on:
      - backend
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./frontend/nginx.conf:/etc/nginx/nginx.conf:ro
    environment:
      BACKEND_URL: http://backend:8000

volumes:
  postgres_data:

networks:
  default:
    name: timetracker-network
    driver: bridge
```

#### 7.2 Backend Dockerfile

**`backend/Dockerfile`**:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
COPY .env .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

#### 7.3 Frontend Dockerfile

**`frontend/Dockerfile`**:

```dockerfile
FROM nginx:1.25-alpine

# Copy static files
COPY . /usr/share/nginx/html/

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD wget --quiet --tries=1 --spider http://localhost/index.html || exit 1

EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
```

**`frontend/nginx.conf`** (basic):

```nginx
user nginx;
worker_processes auto;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;

    server {
        listen 80;
        server_name _;

        root /usr/share/nginx/html;
        index index.html;

        # Serve static files
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1d;
            add_header Cache-Control "public, immutable";
        }

        # SPA routing: serve index.html for all non-file routes
        location / {
            try_files $uri $uri/ /index.html;
        }

        # Proxy API requests to backend
        location /api/ {
            proxy_pass http://backend:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 30s;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

#### 7.4 Environment Variables

**`.env.example`** (at repo root):

```env
# Database
DB_USER=timetracker_user
DB_PASSWORD=YOUR_SECURE_PASSWORD_HERE
DB_NAME=timetracker

# JWT
JWT_SECRET=YOUR_SUPER_SECRET_KEY_HERE_MIN_32_CHARS
JWT_ALGORITHM=HS256

# Admin Initial Account
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=YOUR_INITIAL_ADMIN_PASSWORD_HERE

# CORS (internal network)
CORS_ORIGINS=http://192.168.1.100,http://timetracker.company.local

# Time Zone
TZ=Europe/Berlin

# Logging
LOG_LEVEL=INFO

# Backup Configuration
BACKUP_PATH=/mnt/nas/timetracker-backups
BACKUP_RETAIN_DAYS=90
BACKUP_CRON=0 2 * * *

# Company Defaults
DEFAULT_VACATION_DAYS=30
```

#### 7.5 Initialization & First Run

**Process**:
1. User clones repo
2. User copies `.env.example` → `.env` and edits it
3. User runs: `docker compose up -d`
4. Docker Compose:
   - Starts PostgreSQL, waits for health check
   - Starts backend, runs Alembic migrations automatically, starts FastAPI server
   - Starts frontend (nginx), proxies `/api/` to backend
5. Backend on first run (no users exist):
   - Creates default admin account from `.env` (`ADMIN_EMAIL` / `ADMIN_PASSWORD`)
   - Logs credentials to stdout (for initial login)
6. User opens browser, navigates to `http://localhost`, sees login page
7. User logs in with admin credentials
8. Admin creates departments and user accounts

**Logs**:
```bash
docker compose logs -f backend  # View backend logs
docker compose logs -f db       # View database logs
docker compose logs -f frontend # View nginx logs
```

#### 7.6 Updates & Maintenance

**Update application**:
```bash
git pull
docker compose up -d --build
```

**Backup database**:
```bash
docker compose exec db pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d).sql
```

**Restore database**:
```bash
docker compose exec -T db psql -U $DB_USER $DB_NAME < backup_20260210.sql
```

**Reset everything** (WARNING: deletes all data):
```bash
docker compose down -v
docker compose up -d
```

---

### Phase 8: Polish & Production Readiness

#### 8.1 Offline Capability

Enhance service worker:
- Cache API responses (GET endpoints) for offline access
- Queue creates/updates locally when offline (using IndexedDB)
- When back online, sync queue to backend with conflict resolution:
  - If entry was updated on server in the meantime, show user conflict dialog (local vs. server version)
  - Allow merge or discard
- Use existing `sync-entries` background sync tag (currently stubbed in [sw.js](sw.js))

#### 8.2 Input Validation

**Server-side** (Pydantic schemas):
- End time > start time
- Break ≤ work duration
- Date not in future (allow small tolerance: +1 day for timezone issues)
- Soll hours > 0 and reasonable (e.g., 0-24 hours/day)
- Email format validation
- Password minimum length

**Client-side** (for UX):
- Duplicate validation as server (before submit)
- Real-time validation: red border if fields invalid, error message below field
- Disable "Save" button if form invalid

#### 8.3 Audit Logging

Log sensitive operations:
- User login/logout: user_id, timestamp, IP address
- User creation/edit/deactivation: admin_id, target_user_id, changes, timestamp
- Entry create/edit/delete: user_id, old_data, new_data, timestamp
- Overtime ledger adjustments: admin_id, user_id, reason, timestamp
- Holiday management: admin_id, action, holiday_id, timestamp

**Storage**: Separate `audit_log` table (not for display, just tracking).

#### 8.4 Rate Limiting

Protect against brute force / DoS:
- `/auth/login`: max 5 attempts per email per 15 minutes
- `/entries` (POST): max 100 per day per user (reasonable limit)
- General: 1000 requests per minute per IP (adjustable)
- Use `slowapi` FastAPI extension

#### 8.5 Automated Testing

**Backend** (`tests/` directory):
```bash
pytest tests/
```

Test coverage:
- **Unit tests**: Time calculations (Soll vs Ist with holidays), overtime ledger logic, schedule resolution
- **API tests**: Each endpoint with different roles (admin, boss, worker, unauthenticated)
  - Test 200 (success), 403 (forbidden), 401 (unauthorized), 400 (validation), 409 (conflict)
- **Database tests**: Transactions, cascading deletes, constraints
- Use `pytest-asyncio` for async tests, `httpx.AsyncClient` for API client testing

**Frontend** (manual smoke tests):
- Login, logout, session expired
- Create entry, edit, delete
- Timer: start, stop, reset, add to day
- Calendar: navigate months, select dates
- Reports: view, filters work
- Overtime: earn, use, balance updates
- Admin: create user, create department
- Export: PDF downloads, Excel generates, CSV opens in Excel
- Responsive: test on mobile (480px), tablet (768px), desktop

**Docker smoke test**:
```bash
docker compose up -d
sleep 5
curl http://localhost/  # Should return HTML
curl http://localhost/api/v1/auth/login  # Should return 422 (POST required)
# Login with admin credentials
# Create an entry via API
# Export PDF, verify download
docker compose down
```

#### 8.6 Production Checklist

- [ ] `.env` values changed from defaults (strong `JWT_SECRET`, strong passwords)
- [ ] `CORS_ORIGINS` set to internal IP/hostname (not `*`)
- [ ] `LOG_LEVEL=WARNING` (not `DEBUG`)
- [ ] Database backups configured (daily to NAS, tested restore)
- [ ] Backup NAS path mounted and writable from Docker host
- [ ] Resource limits set in `docker-compose.yml` (memory, CPU)
- [ ] Time zone set to `Europe/Berlin` (or correct company time zone)
- [ ] Public holidays imported for current + next year
- [ ] Default vacation budget set (e.g., 30 days/year)
- [ ] Admin account password changed from initial `.env` value
- [ ] GDPR: data deletion feature tested (year/month bulk delete with safety checks)

#### 8.7 Network Configuration (Internal Only)

The app runs on the internal company network only — no public internet exposure required.

**Access options**:
- Direct IP: `http://192.168.x.x` (configure in Docker bind address)
- Company DNS: `http://timetracker.company.local` (configure in company DNS server)

**Docker bind** — in `docker-compose.yml`, bind frontend to specific IP if needed:
```yaml
frontend:
  ports:
    - "192.168.1.100:80:80"  # Bind to specific internal IP
```

No SSL/HTTPS, no reverse proxy (Caddy/Traefik) needed for internal-only deployment. If internet exposure is needed later, add Caddy with Let's Encrypt.

#### 8.8 Automated Database Backups

Configurable backup system using a cron-based Docker service or host cron job.

**Backup script** (`backup.sh`):
```bash
#!/bin/bash
BACKUP_DIR="${BACKUP_PATH:-/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="timetracker_backup_${TIMESTAMP}.sql.gz"

# Dump and compress
docker compose exec -T db pg_dump -U $DB_USER $DB_NAME | gzip > "${BACKUP_DIR}/${FILENAME}"

# Delete backups older than BACKUP_RETAIN_DAYS (default: 30)
find "${BACKUP_DIR}" -name "timetracker_backup_*.sql.gz" -mtime +${BACKUP_RETAIN_DAYS:-30} -delete

echo "Backup created: ${FILENAME}"
```

**Configuration** (in `.env`):
```env
# Backup settings
BACKUP_PATH=/mnt/nas/timetracker-backups   # NAS mount or local directory
BACKUP_RETAIN_DAYS=90                       # Keep backups for 90 days
BACKUP_CRON=0 2 * * *                       # Daily at 2:00 AM (configurable)
```

**Setup**: Add cron job on host:
```bash
crontab -e
# Add: 0 2 * * * /path/to/backup.sh >> /var/log/timetracker-backup.log 2>&1
```

Or add a dedicated backup container in `docker-compose.yml`:
```yaml
backup:
  image: postgres:16-alpine
  environment:
    PGHOST: db
    PGUSER: ${DB_USER}
    PGPASSWORD: ${DB_PASSWORD}
    PGDATABASE: ${DB_NAME}
  volumes:
    - ${BACKUP_PATH}:/backups
    - ./backup.sh:/backup.sh:ro
  entrypoint: |
    sh -c 'echo "${BACKUP_CRON} /backup.sh" | crontab - && crond -f'
  depends_on:
    - db
```

---

## Part 3: Architecture Decisions

### Why Python (FastAPI) Over Node.js?

- **Excel/PDF generation**: Python libraries (`openpyxl`, `reportlab`) are mature, easier to use than Node.js equivalents
- **Type safety**: Pydantic schemas provide runtime validation, similar to TypeScript but without compilation
- **Async support**: `asyncio` + `SQLAlchemy 2.0` provide true async/await without callback hell
- **Simplicity**: Good for straightforward REST APIs without complex real-time features
- **Labor law compliance**: Time tracking is semi-legal territory; immutable audit logs and strong typing reduce bugs

### Why PostgreSQL Over SQLite/MongoDB?

- **Date/time handling**: PostgreSQL's `DATE`, `TIME`, `TIMESTAMP` types with proper timezone support
- **Aggregate functions**: Window functions for running balance calculations (Überstunden)
- **Consistency**: ACID transactions ensure overtime ledger never gets out of sync
- **Scalability**: Works from 5 users to 500+ without migration
- **Relationships**: Foreign keys and cascading deletes prevent orphaned data
- **Full-text search** (future): Easy to add search by entry description

SQLite is simpler to deploy but lacks concurrency; MongoDB is overkill for structured tabular data.

### Why Vanilla JS Frontend (No Framework)?

- **Simplicity**: The existing app is already vanilla JS; minimal rewrite needed
- **No build step**: Users can deploy directly from source or simple Docker image
- **Approachability**: New developers can understand the code without learning React/Vue
- **Bundle size**: No framework overhead; app loads faster
- **PWA**: Service worker integration is straightforward

Downside: code organization requires discipline (hence modules + clear naming). Not suitable if you need complex state management; if this becomes necessary in future, migrate to Vue or React incrementally.

### Why JWT in httpOnly Cookies Over localStorage?

- **Security**: httpOnly cookies prevent XSS theft (JavaScript cannot access them)
- **Convenience**: Browser automatically sends cookie with requests (no manual header insertion)
- **Refresh token rotation**: Server can invalidate refresh tokens server-side

Downside: requires SameSite policy; CORS setup is slightly more complex.

### Why Immutable Overtime Ledger?

- **Auditability**: Every earn/use/adjustment is recorded with timestamp → no confusion about balance
- **Correctness**: Balance = `SUM(...)` is always correct, even if code has bugs; can recalculate anytime
- **Analytics**: Ledger tells a story (e.g., "used 8h on Feb 10 to cover Jan shortfall")
- **Compliance**: Labor law may require proof of how overtime was accumulated/used

Downside: more complex queries (but queries are fast).

### Why Docker Compose?

- **Reproducibility**: Same setup dev, test, production
- **Isolation**: DB, API, frontend in separate containers, no conflicts
- **Ease**: `docker compose up -d` replaces `npm install`, `pip install`, `npm start`, `python manage.py runserver`, etc.
- **Scalability**: Can move to Kubernetes later without major changes

---

## Part 4: Data Migration Plan

If migrating from the existing client-side app:

1. **Export existing data as JSON**: User goes to Data tab, exports all entries
2. **Backend endpoint for import**: Provide `/api/v1/import/json` endpoint
   - Accepts file upload
   - Validates all entries
   - Upserts into database (deduplicate if needed)
   - Returns summary: "Imported 150 entries, skipped 3 duplicates"
3. **One-time worker migration**: Each worker logs in for first time → app prompts "Import your old data?" → upload file → done

---

## Part 5: Future Enhancements (Out of Scope)

1. **Mobile app**: React Native version sharing API with web frontend
2. **Email notifications**: Sending daily summary, overtime alerts
3. **Slack/Teams integration**: Post daily entries to team channel
4. **Project-based time tracking**: Entries tied to projects/cost centers
5. ~~Approval workflow~~: **Decided against** — entries are immediately active, boss has read-only oversight
6. **Clock in/out via QR code**: Physical presence tracking
7. **Multi-language**: Currently DE/EN; add ES, FR, etc.
8. **Analytics dashboard**: Graphs, trends, productivity insights
9. **Salary integration**: Export data for payroll system
10. **Mobile-friendly timer**: Dedicated progressive web app for quick time tracking on phone

---

## Part 6: Summary & Key Milestones

| Phase | Estimated Steps | Key Deliverables |
|-------|----------|---|
| **1. Backend** | 4 | REST API running in Docker, PostgreSQL schema + migrations |
| **2. Auth** | 4 | Login page, JWT tokens, admin account creation, user management UI |
| **3. Frontend Refactor** | 3 | API client, module organization, fix old bugs |
| **4. Soll/Überstunden/Absences** | 4 | Work schedule, overtime ledger, monthly dashboard, Urlaub/Krank tracking, usage UI |
| **5. Boss Views** | 4 | Department overview, worker report, export functionality |
| **6. Exports** | 3 | PDF (server-side), CSV (server-side), Excel with formulas |
| **7. Docker** | 3 | Compose file, Dockerfiles, deployment guide |
| **8. Polish** | 6 | Testing, offline sync, audit logging, rate limiting, backups, data deletion, production readiness |

**Total estimated effort**: ~100-150 hours for 1-2 developers. Can be split into independent phases.

---

## Confirmed Decisions (from Q&A)

All questions have been answered and incorporated into the plan above. Summary of decisions:

1. **Network/Domain**: Internal network only. Access via IP address or company-internal DNS name. No reverse proxy (Caddy/Traefik), no SSL/HTTPS — the app runs on plain HTTP inside the internal network. Docker container binds directly to host IP.
2. **Email**: No email integration. Admin alerts are nice-to-have but skipped to reduce complexity. Password resets are handled manually by admin (generate new temporary password via admin panel).
3. **Backup strategy**: Automated database backups to local NAS/storage. Configurable schedule (daily/weekly/custom cron) and target path (local directory, mounted NAS share). Implemented via a backup script + cron job inside a Docker container or host cron.
4. **User limit**: Max ~100 users. No need for load balancing or horizontal scaling. Single Docker host is sufficient.
5. **Mobile**: Not a priority, but keep the existing responsive/PWA design. No native mobile app. Ensure the web app remains usable on mobile browsers (already partially done). Future enhancement if needed.
6. **Data retention**: Time entries stored indefinitely. Server-side admin feature to bulk-delete entries by year or year+month for all users, with multiple confirmation steps (type confirmation phrase, preview affected data count, require admin password re-entry) to prevent accidental deletion.
7. **Time zone**: Single time zone for all workers (configurable in settings, default: `Europe/Berlin`). No multi-timezone support needed.
8. **Holidays/Absences**: Full absence tracking — Urlaub (vacation days), Krankheitstage (sick days), and Feiertage (public holidays). Each worker gets a yearly vacation day budget. Marking a day as Urlaub or Krank counts as Soll fulfilled (no Minusstunden for that day).
9. **Approval workflow**: No approval needed. Entries are immediately active when saved. Boss has read-only access to worker entries with full audit trail of edits/changes for accountability.
10. **Entry approval**: Explicitly not needed. Workers self-manage their entries. Boss oversight is via read-only reports + audit trail, not via approval gates.

---

## Next Steps

1. **Start Phase 1**: Set up project structure, PostgreSQL schema, FastAPI base
2. **Phase 2**: Authentication + user management
3. **Iterate through phases**: Use this plan as checklist, mark completed items
4. **Each phase**: Implement → test → commit → move to next

---

*Last updated: 10. Februar 2026*
