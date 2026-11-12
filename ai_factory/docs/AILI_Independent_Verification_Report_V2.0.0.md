# Independent Verification Report — Revised A01 Artifact (V2.0.0)

**Date:** 2026-11-07  
**Inspector:** Independent Read-Only Verification  
**Artifact:** `var/workspaces/AMSDP-000003/requirement_analysis_v2.0.0.json`  
**Mode:** READ-ONLY — no files modified.

---

## Overall Verdict: PARTIAL PASS

The revised artifact (29 requirements with source references) is a significant improvement. **2 of 29 classifications are inaccurate**: REQ-010 (claims PARTIAL, should be MISSING — no appointment model enforcement) and REQ-012 (claims PARTIAL, should be MISSING — no booking_source field). 27/29 are correct.

---

## Verification Table

| REQ | Claimed | Verdict | Source Evidence |
|-----|---------|---------|-----------------|
| 001 | SATISFIED | ✅ CORRECT | org/main.py:53-81 |
| 002 | PARTIAL | ✅ CORRECT | All 8 services scope org_id. All in-memory. |
| 003 | SATISFIED | ✅ CORRECT | org/main.py:86-118 |
| 004 | SATISFIED | ✅ CORRECT | patient/main.py:37-38 (no branch_id) |
| 005 | SATISFIED | ✅ CORRECT | identity/permissions.py:9-34 (6 roles) |
| 006 | PARTIAL | ✅ CORRECT | check() defined L36-43. Called in 0/16 endpoints. |
| 007 | SATISFIED | ✅ CORRECT | doctor/main.py:32-48 |
| 008 | SATISFIED | ✅ CORRECT | patient/main.py:31-50, 81-92 |
| 009 | SATISFIED | ✅ CORRECT | scheduling/main.py:32-44. Note: booked=0 always. |
| 010 | PARTIAL | ❌ MISSING | No model enforces capacity. Slots return booked=0. |
| 011 | PARTIAL | ✅ CORRECT | appointment/main.py:79-84. 5 of 10 BR statuses missing. |
| 012 | PARTIAL | ❌ MISSING | appointment_type (L20) != booking_source. BR field absent. |
| 013 | MISSING | ✅ CORRECT | No transfer endpoint. |
| 014 | PARTIAL | ✅ CORRECT | Cancel L80. No_show L82. Policy missing. |
| 015 | MISSING | ✅ CORRECT | No late-arrival logic. |
| 016 | MISSING | ✅ CORRECT | No overbooking mechanism. |
| 017 | PARTIAL | ✅ CORRECT | appointment/main.py:35-39. Race-prone serial. |
| 018 | PARTIAL | ✅ CORRECT | queuing/main.py:39. Queue-end only. |
| 019 | SATISFIED | ✅ CORRECT | queuing/main.py:28-32 |
| 020 | PARTIAL | ✅ CORRECT | queuing/main.py:72-76, 81-88 |
| 021 | PARTIAL | ✅ CORRECT | queuing/main.py:39. Daily-reset per key. |
| 022 | MISSING | ✅ CORRECT | No print endpoint. BR sect32. |
| 023 | MISSING | ✅ CORRECT | Future phase. BR sect33. |
| 024 | SATISFIED | ✅ CORRECT | audit/main.py:24-44 |
| 025 | PARTIAL | ✅ CORRECT | patient/main.py:19 (national_id stored) |
| 026 | MISSING | ✅ CORRECT | No subscription model. |
| 027 | PARTIAL | ✅ CORRECT | bcrypt+JWT L30-55. check() not wired. |
| 028 | PARTIAL | ✅ CORRECT | JWT branch L52. Patient org-wide. Doctor branch-filtered. |
| 029 | PARTIAL | ✅ CORRECT | appt L88-91. queue L81-88. |

**Not duplicates:** REQ-020 (queue audit) and REQ-029 (appointment history) track different concerns.

---

## Persistence Assessment

ALL 8 services use in-memory dicts only. Verdict: ✅ Artifact claim CORRECT. Full data loss on process restart.

| Service | Storage | File:Line |
|---------|---------|-----------|
| Identity | `_users_db: dict` | identity/main.py:15 |
| Organization | `_orgs_db, _branches_db: dict` | org/main.py:13-14 |
| Patient | `_patients_db: dict` | patient/main.py:10 |
| Doctor | `_doctors_db: dict` | doctor/main.py:10 |
| Scheduling | `_schedules_db: dict` | scheduling/main.py:10 |
| Appointment | `_appointments_db: dict` | appointment/main.py:10 |
| Queue | `_queues_db: list` + `_next_token: dict` | queuing/main.py:10-11 |
| Audit | `_audit_db: list` | audit/main.py:10 |

---

## Authorization Assessment

**0 of 16 data-modifying endpoints call `perm_check()`.** Only login (identity/main.py:42-62) and validate (L64-77) perform authentication. The standalone `/check-permission` endpoint (routes.py:47-52) is self-referential — it reads `user_id` from the request body without verifying the caller's authority.

Verdict: ✅ Artifact claim CORRECT — permission framework defined but NOT wired into endpoints.

---

## Test Coverage

E2E test (`backend/tests/test_e2e.py`): 15 integration tests covering the full workflow — org→branch→doctor→patient→staff→login→schedule→slots→appt→enqueue→queue→reschedule→audit→cross-org isolation. Plus 8 per-service test files.

---

## MVP Blockers (Prioritized)

| Pri | Issue |
|-----|-------|
| P0 | perm_check() called in 0/16 endpoints — no server-side authorization |
| P0 | All data in-memory — full loss on restart, no database |
| P1 | Schedule capacity never enforced — booked=0 always |
| P1 | BR sect16 booking_source field absent |
| P2 | 5 of 10 BR sect18 appointment statuses missing/different |
| P2 | 3 of 4 BR sect26 walk-in placement policies missing |

---

## Questions for Product Owner

1. **Status names:** Are "arrived" (CHECKED_IN) and "in_progress" (IN_CONSULTATION) acceptable equivalents, or must BR sect18 be matched exactly?
2. **In-memory storage:** Acceptable for hackathon demo, or must database be added?
3. **Authorization scope:** Wire perm_check() into all endpoints before Phase 1?
4. **Capacity enforcement:** Required for Phase 1 or operator-managed queue sufficient?
5. **Subscription expiry:** Basic read-only mode on expiry — Phase 1 or Phase 2?
6. **Transfer:** Cancel-and-create sufficient for Phase 1, or formal transfer required?

---

*End of Report. No source code, test, database, or deployment files were modified.*