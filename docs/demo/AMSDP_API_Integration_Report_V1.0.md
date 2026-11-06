# AMSDP API Integration Report — V1.0

> **Date:** 2026-11-05  
> **Purpose:** Maps every frontend page to its backend API endpoints.  
> **Proxy:** Next.js rewrites `/api/v1/*` → service-specific Docker hosts.

---

## 1. Login Page (`/`)

| Frontend Element | HTTP | Endpoint | Backend Service |
|-----------------|------|----------|-----------------|
| Login form submit | POST | `/api/v1/staff/login` | Identity (port 8000) |

**Auth flow:**
1. User submits username + password → POST `/api/v1/staff/login`
2. On success, token + user object stored in `sessionStorage`
3. Redirect to `/dashboard`

---

## 2. Dashboard (`/dashboard`)

| Frontend Element | HTTP | Endpoint | Backend Service |
|-----------------|------|----------|-----------------|
| User info display | — | Reads from `sessionStorage.getItem('amsdp_user')` | — |
| Navigation links | — | Client-side links to sub-pages | — |
| Logout | — | Clears `sessionStorage`, redirects to `/` | — |

---

## 3. Patients Page (`/patients`)

| Frontend Element | HTTP | Endpoint | Backend Service |
|-----------------|------|----------|-----------------|
| Search form | GET | `/api/v1/patients?organization_id=...&q=...` | Patient (port 8002) |

**Query params**: `organization_id` (required), `q` (search string), `page`, `limit`  
**Response**: `{"items": [...], "total": N, "page": 1}`

---

## 4. Doctors Page (`/doctors`)

| Frontend Element | HTTP | Endpoint | Backend Service |
|-----------------|------|----------|-----------------|
| Load button | GET | `/api/v1/doctors?organization_id=...` | Doctor (port 8003) |

**Response**: `{"items": [...], "total": N}`

---

## 5. Schedules Page (`/schedules`)

| Frontend Element | HTTP | Endpoint | Backend Service |
|-----------------|------|----------|-----------------|
| Load button | GET | `/api/v1/schedules?organization_id=...` | Scheduling (port 8004) |

**Response**: Array of schedule objects with `slot_templates`

---

## 6. Appointments Page (`/appointments`)

| Frontend Element | HTTP | Endpoint | Backend Service |
|-----------------|------|----------|-----------------|
| Load button | GET | `/api/v1/appointments?organization_id=...` | Appointment (port 8005) |

**Response**: Array of appointment objects

---

## 7. Queue Page (`/queue`)

| Frontend Element | HTTP | Endpoint | Backend Service |
|-----------------|------|----------|-----------------|
| Load Queue form | GET | `/api/v1/queue?org_id=...&branch=...&doctor=...&date=...` | Queuing (port 8006) |

**Query params**: `organization_id`, `branch_id`, `doctor_id`, `date` (all required)  
**Response**: `{"date":"...","doctor_id":"...","waiting":N,"entries":[...]}`

---

## Complete Endpoint Inventory (40 endpoints)

| # | Service | Method | Path | Purpose |
|---|---------|--------|------|---------|
| 1 | Identity | POST | `/api/v1/staff/users` | Create staff user |
| 2 | Identity | POST | `/api/v1/staff/login` | Authenticate, get JWT |
| 3 | Identity | GET | `/api/v1/staff/validate` | Validate token |
| 4 | Identity | GET | `/api/v1/staff/users` | List staff |
| 5 | Identity | GET | `/api/v1/staff/users/{id}` | Get staff user |
| 6 | Identity | PATCH | `/api/v1/staff/users/{id}` | Update staff user |
| 7 | Identity | POST | `/api/v1/staff/check-permission` | RBAC check |
| 8 | Org | POST | `/api/v1/orgs` | Create organization |
| 9 | Org | GET | `/api/v1/orgs` | List organizations |
| 10 | Org | GET | `/api/v1/orgs/{id}` | Get organization |
| 11 | Org | PATCH | `/api/v1/orgs/{id}` | Update organization |
| 12 | Org | POST | `/api/v1/branches` | Create branch |
| 13 | Org | GET | `/api/v1/orgs/{id}/branches` | List branches |
| 14 | Org | GET | `/api/v1/branches/{id}` | Get branch |
| 15 | Org | PATCH | `/api/v1/branches/{id}` | Update branch |
| 16 | Patient | POST | `/api/v1/patients` | Register patient |
| 17 | Patient | GET | `/api/v1/patients` | Search patients |
| 18 | Patient | GET | `/api/v1/patients/{id}` | Get patient |
| 19 | Patient | PATCH | `/api/v1/patients/{id}` | Update patient |
## Proxy Configuration (`frontend/next.config.js`)

| Route Prefix | Proxied To (Docker hostname) |
|--------------|----------------------------|
| `/api/v1/staff/*` | `http://identity:8000` |
| `/api/v1/orgs/*` | `http://organization:8001` |
| `/api/v1/branches/*` | `http://organization:8001` |
| `/api/v1/patients/*` | `http://patient:8002` |
| `/api/v1/doctors/*` | `http://doctor:8003` |
| `/api/v1/schedules/*` | `http://scheduling:8004` |
| `/api/v1/appointments/*` | `http://appointment:8005` |
| `/api/v1/queue/*` | `http://queuing:8006` |
| `/api/v1/audit/*` | `http://audit:8007` |

---

*All 40 endpoints operational as of 2026-11-05. Verified via E2E test suite (15 tests) and curl probes.*
| 20 | Patient | POST | `/api/v1/patients/merge` | Merge duplicates |