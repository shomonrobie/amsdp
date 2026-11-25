# AMSDP — MP-17 Doctor Mobile Duplicate Allowance Implementation Report V1.0

**Work package:** MP-17 — *doctor mobile **duplicate allowance** (platform-level policy)*, **P2**, no unmet
dependency.
**Written:** 24 November 2026, Windows development checkout (`E:\amsdp`).
**Authoritative scope:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` row MP-17, acceptance
**1.0** — *"BR §9.7: default unique per organisation; the allowance permits duplicates within one organisation
only, never across tenants."*
**Where written:** `docs/implementation/` (`.clinerules` §11). New file; no document was moved, renamed or
deleted, so no migration-manifest entry is required.

---

## 1. What existed before this window, and what was missing

Business Rules §9 says three separate things about a doctor's mobile number, and only one of them was implemented:

| BR | Requirement | State before this window |
|---|---|---|
| §9.6 | *Default* doctor mobile-number uniqueness is within an organization | **Implemented**, hard-coded |
| §9.7 | Super Admin **may allow** duplicate doctor mobile numbers within an organization | **Absent** — no setting existed, no endpoint, no way to grant it |
| §9.8 | The same mobile number **may exist in different organizations** | **Implemented** by construction (every lookup is scoped by `organization_id`) |

The enforcement was two inline queries — one in `create_doctor` (`backend/doctor/main.py:98`, before this change)
and one in `update_doctor` (`:228`) — each answering `409 a doctor with this mobile number already exists` when a
same-tenant row matched. The rule was correct but had no switch, and because it was written twice it had two
copies of the same idea to keep in step.

So MP-17 is **not** a bug fix: it is the missing half of §9.7 — a per-organization allowance that a **platform
administrator** grants — plus the extraction that makes both write paths consult one helper instead of two
copies of the query.

The plan's phrase *"platform-level policy"* is the design constraint, and §9.7's own wording is the authority:
the allowance is granted by the Super Admin, **within one organization**, and never reaches another tenant.

---

## 2. What was built

### 2.1 `backend/common/config.py` — the policy helper (one new section, ~75 lines)

Added to the same file, and in the same shape, as the existing `registration_policy`, `appointment_config`,
`queue_config` and `queue_calling_config` blocks, so organization configuration keeps one idiom:

| Export | Purpose |
|---|---|
| `DEFAULT_DOCTOR_MOBILE_POLICY` | `{"allow_duplicate_mobile": False}` — BR §9.6's default, in one place |
| `get_doctor_mobile_policy(org_config)` | Reads `config["doctor_mobile_policy"]`; a missing block, a **non-dict** block, or a **non-boolean** value falls back to the default |
| `doctor_mobile_must_be_unique(org_config)` | The single enforcement predicate — the *negation* of the stored allowance, phrased so a caller cannot forget the default |
| `merge_doctor_mobile_policy(org_config, updates)` | Returns a copy with the block updated; `None` values are ignored, and the caller's dict is never mutated |

The block reads:

```json
{ "doctor_mobile_policy": { "allow_duplicate_mobile": false,
                            "updated_at": "...", "updated_by": "<user id>" } }
```

Two deliberate properties, both pinned by test (§4.1):

1. **A corrupt block is never permission.** `"yes"`, `1`, `"false"`, `[]`, a bare string, or a `null` block all
   read as *unique*. The first version of the helper used `(config or {}).get(...) or {}` and would have raised
   `AttributeError` on a string block — the negative test caught that and the helper now type-checks the block
   (§4.1, `test_a_malformed_policy_block_is_ignored`).
2. **The allowance is prospective.** Flipping it changes no doctor row; it only decides whether the next
   colliding write is a `409`. Withdrawing it does **not** merge, delete or deactivate the duplicates that were
   created while it was on — those rows are referenced by appointments and by the append-only audit trail.

### 2.2 `backend/doctor/profile.py` — one check, two callers, and the admin surface

- `mobile_in_use(session, organization_id, mobile, exclude_doctor_id=None)` — the org-scoped lookup. It cannot
  see another tenant's doctor, which is what keeps BR §9.8 true irrespective of the switch.
- `assert_mobile_available(session, org, organization_id, mobile, exclude_doctor_id=None)` — the enforcement
  point. It returns immediately when the organization's allowance is on (no query at all), and raises the
  existing `409` message otherwise. `org` may be `None`, and the default then applies: a caller that has not
  loaded the row can only make the rule stricter, never looser.
- `GET /api/v1/orgs/{org_id}/doctor-mobile-policy` — reads the effective policy; `doctor.manage`, because
  whoever may register a doctor is who needs to know whether a repeat number will be refused.
- `PATCH /api/v1/orgs/{org_id}/doctor-mobile-policy` — the platform gate. It requires `org.manage` **and**
  `auth.is_super_admin` (the `platform.admin` capability, Q-1), answering `403 only a platform administrator may
  change the doctor mobile-number duplicate policy`. It writes `updated_at` / `updated_by` and records an
  audit event `organization.doctor_mobile_policy.update` with `before`/`after`.

### 2.3 `backend/doctor/main.py` — both write paths now use the helper (−14 lines of duplicated query)

| Path | Before | After |
|---|---|---|
| `create_doctor` | Inline `session.query(Doctor).filter(org, mobile).first()` → `409`; the `Organization` row was loaded again later for the BMDC policy | The `Organization` row is read **once**, before the check; `assert_mobile_available(...)` decides |
| `update_doctor` | Inline query with `Doctor.id != doctor.id` → `409` | `assert_mobile_available(..., exclude_doctor_id=doctor.id)` — the same helper, so the edit path cannot drift from the create path |

The exclusion parameter is why re-saving a doctor whose number has not changed still succeeds; that case is a
test (§4.3).

### 2.4 What was deliberately **not** built

- **No schema change and no migration.** The allowance lives in `organizations.config` (JSON), like every other
  facility policy. `doctors` keeps its non-unique index `idx_doctor_org_mobile` (correct for both settings: with
  duplicates allowed it must not be unique, and uniqueness is enforced in the service where the policy is known).
- **No frontend surface.** The repository has no screen for `registration-policy` or `walk-in-config` either;
  platform-level org configuration is reached through the API by the operator. Adding a settings page would be a
  new screen, not a requirement of MP-17's acceptance criterion.
- **No change to the `409` contract.** The message and status code are unchanged, so every existing client and test
  that creates doctors keeps its behaviour.

---

## 3. Decisions taken, and why

| # | Decision | Why |
|---|---|---|
| D1 | The allowance is stored in `organizations.config["doctor_mobile_policy"]` | It is organization configuration, and every other facility policy already lives there; a new column would need a migration for one boolean |
| D2 | Default is **unique**, and an unreadable value falls back to unique | BR §9.6 is the default; a corrupt or absent configuration must never be read as permission |
| D3 | Only a platform administrator may change it (`403`, not a hidden route) | BR §9.7 names the Super Admin. A `403` that says why is auditable; a missing route that pretends the setting does not exist is not |
| D4 | Withdrawing the allowance is behind the same gate as granting it | It is one switch. Two rules (who may tighten, who may loosen) would be more code and a second thing to get wrong |
| D5 | Enforcement is one helper, not two inline queries | The two copies were identical apart from the self-exclusion; that is exactly the pair that drifts. The helper is also the seam that makes the decision testable without a database |
| D6 | The allowance does not skip the **tenant** scope, only the uniqueness refusal | BR §9.8 must hold under both settings. The lookup still filters by `organization_id`; when the allowance is on it is simply not executed |
| D7 | The policy write is audited as `organization.doctor_mobile_policy.update`, `target_type="organization"` | The row that changed is the tenant's configuration. The sibling `registration-policy` route records under `target_type="doctor"`; this one states what actually moved rather than copying that |
| D8 | No UI, no new dependency, no migration | MP-17's acceptance is a policy rule, and all three additions would be larger than the rule itself (§2.4) |

---

## 4. Verification — what was actually run, and what it showed

Every number below is a run in this tree on 24 November 2026, Windows, `E:\amsdp`, from the repository root
with the project virtualenv (`.\.venv\Scripts\python.exe`).

### 4.1 The policy layer — **29 tests, executable without a database**

```
python -m pytest backend/tests/test_doctor_mobile_policy.py \
                 backend/tests/test_doctor_mobile_enforcement.py -q
29 passed in 2.08s
```

| File | Tests | What it pins |
|---|---:|---|
| `backend/tests/test_doctor_mobile_policy.py` | 23 | BR §9.6 default; missing/empty/non-dict/non-boolean blocks read as **unique**; an explicit boolean decides the switch; the enforcement predicate is the exact negation of the stored allowance; `get_` returns a copy (mutating it cannot edit the platform default); `merge_` preserves sibling config, ignores `None`, and can withdraw the allowance |
| `backend/tests/test_doctor_mobile_enforcement.py` | 6 | `assert_mobile_available`: the default refuses a collision (`409`); **the allowance issues no query at all**; a free number passes; the edit path adds the self-exclusion filter; a `None` organization row and a corrupt block are strict, not permissive |

These two modules import only `common.config` and `doctor.profile` — no connection is opened — so they run on this
host, which has **no reachable PostgreSQL** (§4.4). They are the reason MP-17 is not another
"written-but-unrun" work package.

### 4.2 Negative control — the suite is not vacuous

`doctor_mobile_must_be_unique` was mutated to `return False` (the rule silently disabled — precisely the defect
that would let every tenant have duplicates), the same two files were re-run, and the file was restored:

| Step | Result |
|---|---|
| Baseline before the mutation | `29 passed in 1.48s` |
| Mutated (`return False`) | **`23 failed, 6 passed in 1.90s`** — every default-refusal, corrupt-block, `None`-org, self-exclusion and withdrawal assertion went red |
| Restored from a byte copy | SHA-256 `C4A667B772EDA8B8FDF87D05E82800DAEF12698BF763A6347C3B33FDDF33FDF9` **before and after**, and `29 passed in 2.08s` |

The six that still passed under the mutation are the ones that assert *behaviour of the allowance* (it permits,
it merges, it skips the lookup) — they do not read the predicate that was broken. That is the expected split, not
a gap.

### 4.3 The API-level tests — written and collected, **not run**

`backend/doctor/tests/test_doctor_mobile_duplicates.py` (256 lines, **12 tests**) drives the real endpoints
through `TestClient`, minting JWTs from real `staff_users` rows exactly as `test_doctor.py` does:

| Test | BR | Asserts |
|---|---|---|
| `test_default_refuses_a_second_doctor_on_the_same_mobile` | §9.6 | `201` then `409`, and one row in the database |
| `test_the_check_uses_the_canonical_form` | §9.6 | `+880 18…` collides with `018…` — normalization is not a bypass |
| `test_only_a_platform_administrator_may_grant_the_allowance` | §9.7 | branch_admin `PATCH` → **`403`**, and the duplicate is still refused afterwards |
| `test_the_allowance_can_be_read_by_doctor_management` | §9.7 | `GET` → `{"organization_id": …, "doctor_mobile_policy": {"allow_duplicate_mobile": false}}` |
| `test_the_allowance_permits_duplicates_within_the_organization` | §9.7 | after the grant, two `201`s on one number and **two rows**, same tenant |
| `test_withdrawing_the_allowance_keeps_duplicates_but_refuses_a_third` | §9.7 | withdrawal keeps the existing pair, refuses a third |
| `test_the_policy_change_is_audited_with_before_and_after` | §10 | `audit_events` row `organization.doctor_mobile_policy.update`, `target_type="organization"`, `before`/`after` |
| `test_a_number_used_at_another_facility_is_never_a_duplicate` | §9.8 | the same number at a second tenant is `201` **on the default policy** |
| `test_the_allowance_at_one_facility_does_not_reach_another` | §9.8 | two doctors on one number at tenant A leaves tenant B untouched (and vice versa) |
| `test_update_refuses_a_number_another_doctor_already_has` | §9.6 | `PATCH` onto a colleague's number → `409` |
| `test_update_accepts_a_collision_when_the_org_allows_it` | §9.7 | the same `PATCH` → `200` once the allowance is on |
| `test_resaving_a_doctor_does_not_collide_with_itself` | — | re-saving an unchanged number → `200` (the self-exclusion) |

**They were not executed.** `pytest --collect-only` reports `12 tests collected in 2.40s`, so the module imports and
is syntactically valid, but every test opens a real session; this host has no PostgreSQL (§4.4). They are recorded
as **written and collected, not run**, in the register as well as here.

### 4.4 Why they could not run — the environment, measured

```
Test-NetConnection 127.0.0.1 -Port 5433 → False
python -m pytest backend/tests/test_dqds.py -q --collect-only
  ERROR … sqlalchemy.exc.OperationalError: (psycopg2…
  Interrupted: 1 error during collection
```

The backend suite is PostgreSQL-backed by design (`backend/conftest.py` only adjusts `sys.path`; the DSN comes
from `AMSDP_DATABASE_URL` / `AMSDP_DB_PORT`, default `127.0.0.1:5433`). No database is reachable from this
checkout, so *no* endpoint-level test in this repository can run here — the same blocker recorded as **O-1** for
MP-19's 31 identity tests. It is an environment gap, not a defect in MP-17, and it is not worked around by
weakening a test.

### 4.5 Compilation and import checks

| Check | Result |
|---|---|
| `python -m py_compile` on the three changed production files and the three test modules | **exit 0** |
| `pytest --collect-only` on the API module | **12 tests collected** — the module imports (`doctor.main` → `profile` → `common.config`) without opening a connection |
| `assert_mobile_available` imported by the DB-free module | proves the production helper is importable and callable without a database |

### 4.6 What is **not** verified here

| Claim | Status |
|---|---|
| The allowance permits duplicates inside one organization, end to end | **NOT VERIFIED HERE** — the 12 API tests need a database (§4.3) |
| A non-platform administrator is refused with `403` | **NOT VERIFIED HERE** — same reason; the gate is one `getattr(auth, "is_super_admin", False)` line, inspected and compiled |
| The audit row carries the right `before`/`after` | **NOT VERIFIED HERE** — asserted by `test_the_policy_change_is_audited_with_before_and_after`, unrun |
| BR §9.8 (cross-tenant) | **TESTED by construction + unit**: the lookup is org-scoped in `mobile_in_use`; the two cross-tenant API tests are written, unrun |
| The policy layer and the enforcement *decision* | **TESTED** — 29 passed, with a 23-failure negative control (§4.1, §4.2) |

Nothing in this report promotes MP-17 to **VERIFIED**: no second, independent artefact (a live request against a
running service, or a database read-back) exists for the endpoint behaviour.

---

## 5. Files touched

| File | Lines now | Change |
|---|---:|---|
| `backend/common/config.py` | 368 | New `doctor_mobile_policy` section: `DEFAULT_DOCTOR_MOBILE_POLICY`, `get_doctor_mobile_policy`, `doctor_mobile_must_be_unique`, `merge_doctor_mobile_policy` |
| `backend/doctor/profile.py` | 1067 | `DoctorMobilePolicyUpdate`; `mobile_in_use`; `assert_mobile_available`; `GET`/`PATCH /api/v1/orgs/{org_id}/doctor-mobile-policy`; the three config helpers imported |
| `backend/doctor/main.py` | 278 | Both duplicate queries replaced by `assert_mobile_available`; the `Organization` row is read once, before the check, instead of twice |
| `backend/tests/test_doctor_mobile_policy.py` | 129 | **New** — 23 DB-free policy tests |
| `backend/tests/test_doctor_mobile_enforcement.py` | 97 | **New** — 6 DB-free enforcement-decision tests |
| `backend/doctor/tests/test_doctor_mobile_duplicates.py` | 256 | **New** — 12 API tests, collected, **not run** (§4.3) |

No schema change, no migration, no frontend file, no new dependency. One production file was mutated once for the
negative control and restored from a byte copy — SHA-256 `C4A667B7…FDF9` before and after (§4.2).

---

## 6. Governance and Skill Compliance (`.clinerules` §6)

### 6.1 Documents read and applied

| Domain routed (§4) | Document applied | How it shaped this work |
|---|---|---|
| Backend API / service endpoints | `saas-application-security.md` (adapted, Assessment §3), Business Rules Part II–X | The new routes take the tenant from the token, answer a non-disclosing `404` for a foreign org, and validate before writing |
| Authentication / RBAC / permissions | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–§8, `backend/common/permissions.py` | `org.manage` + `is_super_admin` (`platform.admin`, Q-1) for the write, `doctor.manage` for the read — no new capability invented |
| Multi-tenant data / org-branch isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–§6, §9.6–§9.8 | `organization_id` remains the only tenant key; the duplicate lookup never leaves the tenant, so §9.8 holds under both settings |
| Audit / data integrity | `saas-observability.md` (adapted), Business Rules Part X, `backend/common/audit.py` | The policy write records `before`/`after` and an actor; nothing merges or deletes a doctor row to restore uniqueness |
| Database schema / migrations | `saas-multitenant-data.md` §4–§5 (adapted) | No schema change was needed — the setting lives in `organizations.config` — so **no** Alembic revision was written or applied |
| Documentation placement | `.clinerules` §11–§12, `docs/governance/AMSDP_Docs_Index_V1.0.md` | This report is in `docs/implementation/`; the index annex and the execution register were updated in the same window (§8) |

`.clinerules` §12 step 3 was followed first: the Docs Index was consulted before planning, and the MP-17 row of the
master plan and BR §9.6–§9.8 were read verbatim rather than reconstructed from memory.

### 6.2 Skills

**No skill package is installed in this workspace** (`.clinerules` §5). No skill was claimed or simulated; the work
used the governance documents in §6.1 and the existing project artefacts.

### 6.3 Non-negotiables (`§3`) — point by point

| Rule | Status here |
|---|---|
| Never log or expose secrets | No token, credential or password appears in code, test output or this report |
| The UI is never the fallback safety boundary | There is no UI in this change; the platform gate is server-side and audited |
| Access enforced server-side, principal from the token | `require_org_access` + `require_permission`; the organization comes from the token, never from the body |
| Cross-tenant / cross-branch fails closed with **404** | `require_org_access(...)` on both routes; the duplicate lookup is org-scoped |
| `organization_id` is the only tenant key | No second tenant column; the policy block lives inside the organization row |
| Audit append-only; denials recorded | The policy change is audited with `before`/`after`; the `403` denial is recorded by the denial-audit middleware |
| Forward-only idempotent migrations for schema change | No schema change, therefore no migration — and none was invented |
| Never claim unverified capability | §4.3/§4.6 state the 12 API tests are **not run**; the register grades MP-17 `TESTED (policy + decision) / API unrun` |
| Do not use a tool/library merely because it was discovered | No dependency added; the tests use `pytest` and `TestClient`, already in use |

### 6.4 Deviations and exceptions

1. **The endpoint behaviour is not executed here.** The host has no PostgreSQL (§4.4). This is the same environment
   gap as MP-19's O-1, and it is stated in the register rather than smoothed over.
2. **One mutation, not a campaign.** §4.2 disables the enforcement predicate and shows 23 failures; the other
   branches (allowance on, `None` org, corrupt block) are covered by tests but were not individually mutated.
3. **No browser journey.** Nothing in MP-17 is a screen; there is no user-visible flow to click.

---

## 7. Open items, and what should happen next

| # | Item | Effect | Suggested handling |
|---|---|---|---|
| **O-1** | The 12 API tests in `doctor/tests/test_doctor_mobile_duplicates.py` are **unrun** (§4.3) | The `403` gate, the audited `before`/`after` and the two cross-tenant cases are written but unproven here | On a host with PostgreSQL: `python -m pytest backend/doctor/tests -q`; if green, amend §4.6 and the register row to `TESTED` |
| **O-2** | The allowance has no operator UI (§2.4) | A platform administrator must call `PATCH /api/v1/orgs/{id}/doctor-mobile-policy` | Not a gap in MP-17; there is no screen for `registration-policy` or `walk-in-config` either. A platform settings screen is a separate task |
| **O-3** | Withdrawing the allowance leaves existing duplicates in place | By design (§2.1), but "unique within the organization" is therefore not restored retroactively | A reconciliation path would need a *merge* workflow (BR §11 territory), not a silent edit |
| **O-4** | Q-3's two pre-existing frontend reds are untouched | Unrelated to MP-17 (no frontend file changed) | Owner decision on the dataset hash; `pathToFileURL` for `calendar-render.test.mjs` |

**Next eligible work package.** MP-18 (schedule-edit audit, **P2**) is next in plan order and needs no decision.
The register's next-task line advances to it (§8).

---

## 8. Where this report is registered

- **Docs Index:** `docs/governance/AMSDP_Docs_Index_V1.0.md` — annex *"MP-17 doctor mobile duplicate allowance
  report (2026-11-24)"* added with the file's byte size and line count, and the tree count updated **142 → 143**
  (measured).
- **Execution register:** `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` — an **MP-17** row in §2 with
  the evidence quoted from §4 here, §6 listing the files touched, and §7's next-task line advanced to **MP-18**.
- **Nothing was moved, renamed or deleted**, so no migration-manifest entry was created and no version number was
  advanced.
