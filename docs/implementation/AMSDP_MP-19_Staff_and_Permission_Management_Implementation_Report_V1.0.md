# AMSDP — MP-19 / MP-20 Staff and Permission Management Implementation Report V1.0

**Work package:** MP-19 (staff and permission management UI, **P1**) with MP-20 (doctor-assignment editor,
**P1**, depends on MP-19) delivered in the same screen.
**Written:** 24 November 2026, Windows development checkout (`E:\amsdp`).
**Authoritative scope:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` rows MP-19 and MP-20:
MP-19 — *edit, deactivate, role, branch scope, capability grants limited to `DELEGABLE_CAPABILITIES`*, with the
acceptance test "the UI cannot grant beyond the delegable set; self-escalation still 403; last-admin protection
intact; every change audited"; MP-20 — *doctor-assignment editor (multi-doctor for assistants)*, with
"changes audited as `staff.doctor_assignment_changed`; revocation takes effect on the next request; cross-org
assignment returns 404".
**Where written:** `docs/implementation/` (`.clinerules` §11). New file; no document was moved, renamed or
deleted, so no migration-manifest entry is required.

---

## 1. What existed before this window, and what was actually missing

The staff screen was a **read-mostly roster**: it listed staff and offered creation, and nothing else. The
Phase-1 administration gap (`GAP-17 thin administration UI`, features F-09/F-06) was therefore real: a role
could not be changed, an account could not be deactivated, a branch scope could not be corrected, a delegable
capability could not be granted or revoked from the product, and an assistant's doctor assignment could not be
maintained at all.

The **server** half was already there and is not restated as new work: `POST /api/v1/staff/users`,
`GET /api/v1/staff/users`, `PATCH /api/v1/staff/users/{id}`, `GET/POST /api/v1/staff/users/{id}/capabilities`,
`DELETE /api/v1/staff/users/{id}/capabilities/{capability}` and `GET /api/v1/staff/capabilities` exist in
`backend/identity/main.py` and `backend/identity/routes.py`, with `staff.read` / `staff.manage` gates,
`can_grant_role` on role assignment, the last-active-`org_admin` guard under a row + organization lock, the
non-disclosing 404 for another tenant's row, and an append-only audit row per write.

So MP-19 is a **frontend completion** with one deliberate extraction: the client-side *policy* (role ladder,
what may be offered, branch-scoped roles, capability label keys, create-form pre-flight, roster filter) was pulled
out of the page into `frontend/lib/staff-policy.js`, so the rules the screen offers can be asserted directly
instead of being inferred from JSX by regular expression. §2 describes both halves; §4 records what was run.

---

## 2. What was built

### 2.1 `frontend/lib/staff-policy.js` (114 lines) — the screen's rules, in one testable place

| Export | Purpose |
|---|---|
| `ROLE_LEVEL`, `ROLE_ORDER` | A mirror of `backend/common/permissions.py::ROLE_HIERARCHY`, pinned by test (§4.5). Least-privileged-first ordering for pickers |
| `BRANCH_SCOPED_ROLES`, `needsBranch(role)` | Which roles take their scope from a branch; drives whether the create form requires one |
| `canOfferRole(actor, target)`, `grantableRoles(actor)` | A caller is offered only roles **strictly below** their own; `super_admin` is exempt. Mirrors the server's `can_grant_role` |
| `mayGrantCapabilities(actor)` | Grant/revoke is organization-administrator authority only — the backend's Q4 rule, mirrored so the dialog is not offered to someone the API would refuse |
| `ROLE_KEYS`, `roleLabelKey`, `CAPABILITY_LABEL_KEYS`, `capabilityLabelKey` | i18n keys instead of English labels; an unknown capability renders as its own slug rather than disappearing |
| `assignedDoctorIds(user)` | `doctor_ids` with the legacy single `doctor_id` as a fallback (PO-RBAC-01) |
| `isActiveStatus`, `validateNewStaff(form, opts)`, `staffMatchesFilter(staff, filters)` | Status reading, create-form pre-flight, roster filter |

The module states in its own header that **none of it is an authorization boundary**: the server decides every
request, and these helpers decide only what the screen *offers*.

### 2.2 `frontend/pages/staff.js` (704 lines) — one screen for the whole lifecycle

- **Roster**: `GET /api/v1/staff/users?organization_id=…`, with search, role filter and status filter applied by
  `staffMatchesFilter`. Columns: username / display name, role, branch scope, status, assigned doctors, action.
  Branch and doctor lookups come from `GET /api/v1/orgs/{id}/branches` and `GET /api/v1/doctors`.
- **Create** (`NewStaffDialog`): username, password, display name, role, branch, e-mail, mobile, interface
  language. The role list is `grantableRoles(user.role)`; the branch is required exactly when `needsBranch(role)`;
  `validateNewStaff` refuses a short password **before** the request, and the server refuses it again.
- **Edit** (`EditStaffDialog`): display name, e-mail, mobile, language, role, branch scope, status, capability
  grants, doctor assignment.
  - The role select is **disabled on your own row** (`isSelf={editing.id === user.id}`) and carries the
    `ownRoleLocked` hint: the server answers 403, so offering it would only produce a red box.
  - Branch scope sends `""` to clear it (organization-wide) and omits the field to leave it alone — the
    convention the PATCH handler defines.
  - **Saving is a diff** against the row the server last sent (`const patch = {}`, filled only where a value
    changed). An unchanged form closes the dialog and writes **no** audit row; `doctor_ids` is diffed the same
    way.
  - **Deactivation is a two-step action**: the first click swaps the button for a confirmation row
    (`deactivateConfirm` / `activateConfirm`), so a stray click cannot sign someone out.
- **Capability grants**: the catalogue is read from `GET /api/v1/staff/capabilities` — never hard-coded, so the
  screen can neither offer a grant the API refuses nor hide one it would accept. Each row shows grant/revoke and
  the scope it was made for. Grant posts `{capability, branch_id: editing.branch_id || null}`; revoke **names the
  branch** (`?branch_id=…`) when the grant is branch-scoped, because omitting it would leave the organization-wide
  row in place and the button would appear to do nothing.
- **Doctor assignment (MP-20)**: one checkbox per active doctor (`staff-doctor-<id>`), saved as `doctor_ids` in
  the same PATCH. Multiple doctors per assistant is the supported shape; the server audits
  `staff.doctor_assignment_changed`, and the change takes effect on the next request because assignments are read
  per request rather than cached in the token.
- **Denial handling**: gated on `staff.read` (list) and `staff.manage` (every control), with `PermissionDenied`
  instead of an empty table. API failures become sentences: `staffManageDenied` (403), `usernameTaken`,
  `lastAdminGuard`, `ownRoleLocked`, otherwise the server's own detail.
- **i18n**: every visible string goes through `t(...)`, and **all** keys exist in both `bn` and `en` (§4.6).

### 2.3 Documentation header on the page

The page opens with a comment block stating the three rules that shape it — the browser is never the boundary,
the delegable catalogue is read from the server, and a caller cannot change their own role here — plus why
deactivation is a status change rather than a delete. This is the convention the rest of `frontend/pages/` keeps.

### 2.4 One defect removed in passing

The file carried a leftover `export async function getServerSideProps() { return { props: {} }; }` above its
licence header. No other page in this tree has one, the page is entirely client-side (it reads the session with
`getUser()`), and the stub forced a dynamic render for a screen with no server-side data. It was removed; the
route now prerenders like its neighbours — the build reports `/staff` as a prerendered route (`●`) instead of
`ƒ (Dynamic)` (§4.2) — and removing the stub is safe because it accepted no context and returned no props.

---

## 3. Decisions taken, and why

| # | Decision | Why |
|---|---|---|
| D1 | The screen's rules live in `lib/staff-policy.js`, not inside the page | The page is JSX and this project ships no DOM renderer; a pure module can be asserted directly. It also stops the role ladder being copied a second time into the browser |
| D2 | The delegable **set** comes from the server; only its **labels** are client-side | A hard-coded list drifts: the UI would offer a grant the API refuses, or hide one it accepts. Labels cannot come from the server because they must be translated |
| D3 | `organization_id` is still sent in the create body, with a comment saying it is never trusted | The model accepts it and the server re-derives the tenant from the token; removing it would churn the payload for no security gain, and the comment stops the next reader from assuming it is authoritative |
| D4 | Edit sends a **diff**, not the whole record | MP-19's acceptance criterion is "every change audited"; writing unchanged fields would produce audit rows for changes that did not happen, which makes the trail useless exactly when it is being demonstrated |
| D5 | Branch scope: `""` clears, omitted leaves alone | That is the convention `PATCH /api/v1/staff/users/{id}` itself documents, so the page and the API speak the same language |
| D6 | Revoking a branch-scoped grant names the branch | Without `?branch_id=` the API revokes the organization-wide row and leaves the branch row active — the button would look broken |
| D7 | The caller's own role select is disabled, and the API still refuses self-escalation | The lock is a courtesy that avoids a guaranteed 403; the authorization stays server-side (§3 non-negotiable "hidden or disabled elements do not equal real authorization") |
| D8 | Deactivation is a **status change** in two clicks, never a delete | The row, its audit trail and the appointments it booked must survive; the second click exists because deactivating the wrong account signs a colleague out mid-clinic |
| D9 | The leftover `getServerSideProps` stub was removed | No other page has one, the page is client-only, and it forced a dynamic render for a screen with no server data |
| D10 | Doctor assignment rides on the same PATCH as `doctor_ids` | `StaffUserUpdate` already accepts it and already audits `staff.doctor_assignment_changed`; a second endpoint would have duplicated that logic |
| D11 | No new dependency was added | The evidence is `node --test` over the module plus source-level assertions, the convention `queue-call-control.test.mjs` and `facility-doctor.test.mjs` already set. A browser suite is a separate decision (§7) |

---

## 4. Verification — what was actually run, and what it showed

Nothing in this section is asserted from memory; every number is a run in this tree on 24 November 2026, Windows,
`E:\amsdp`. Commands ran from `E:\amsdp\frontend` unless stated.

### 4.1 Frontend suite

| Run | Result |
|---|---|
| Last recorded baseline (MP-10 run, register §5) | `tests 383 / pass 379 / fail 2 / skipped 2` |
| After MP-19 + MP-20 (`npm test`) | `tests 409 / pass 405 / fail 2 / skipped 2` |

The arithmetic closes exactly: **+26 tests, +26 passes, the same two failures and the same two skips.** The 26 are
the two staff modules — 12 rule tests in `tests/staff-policy.test.mjs` and 14 in `tests/staff-page.test.mjs` — so no
existing test changed state. The two failures are pre-existing, in files this work package did not touch, and
reproducible with `staff.js` unmodified:

1. **`tests/banglanamesense-dataset.test.mjs:60`** — the shipped dataset's bytes no longer match the hash recorded
   in `DATASET_SOURCE`:

```
+ actual   '6f69a0ef5faf5688372a475f6f836d28d9ce9d3a1e9248b1931d463ce8257779'
- expected 'ac037c24ebaf0208324351352bd62cedf2de16fbfde6a7d02966c55b8879e51e'
```

2. **`tests/calendar-render.test.mjs`** — the file does not load on Windows at all; its first `await import(...)`
   builds the specifier by string concatenation (`FE + '/node_modules/…'`, line 26), so the loader sees the scheme
   `e:` and aborts:

```
Error [ERR_UNSUPPORTED_ESM_URL_SCHEME]: Only URLs with a scheme in: file, data, and node are supported by the
default ESM loader. On Windows, absolute paths must be valid file:// URLs. Received protocol 'e:'
```

Both are the pair the execution register already recorded under **Q-3** as "dataset provenance mismatch + a test
file that does not load", and register §5 lists the same two names in every run since the baseline. They are
reported here rather than suppressed, and neither is attributable to MP-19: the failures and skips are unchanged
(`2`/`2` before and after) and every one of the 26 tests added is a pass.

### 4.2 Build

`npm run build` → **`✓ Compiled successfully`**, and the route table reports

```
● /staff     5.71 kB     125 kB
```

`●` (prerendered) rather than the `ƒ (Dynamic)` it showed before the stub was removed (§2.4). The page compiled
through the real SWC/Next pipeline, so the JSX in both dialogs is syntactically valid — not merely *read* by a
test.

### 4.3 The two staff test modules

| Module | Tests | Result |
|---|---|---|
| `tests/staff-policy.test.mjs` (rules) | 12 | **12 passed** |
| `tests/staff-page.test.mjs` (wiring, mirrors, i18n) | 14 | **14 passed** |
| Both together | 26 | **26 passed, 0 failed** |

`staff-page.test.mjs` is new in this window and asserts, against real files:

1. the page imports the shared policy and does **not** re-declare `ROLE_LEVEL` / `ROLE_ORDER`;
2. it reads the endpoints the identity service actually serves (roster, branches, doctors, catalogue, grants);
3. every key in its create payload exists on `StaffUserCreate` (parsed out of `backend/identity/models.py`);
4. edit is a diff (`const patch = {}` plus `patch.<field>` assignments);
5. deactivation is two-step (`deactivateConfirm` / `activateConfirm` both present);
6. the caller's own row is the locked one (`isSelf={editing.id === user.id}`, `ownRoleLocked` hint, disabled
   select);
7. the capability catalogue is fetched and **not** hard-coded (the literal `'appointment.book_cross_branch'` is
   asserted *absent* from the page), and the revoke URL names the branch;
8. the screen is gated on `staff.read` / `staff.manage` — the same strings the backend gates on;
9. every staff route the page calls (roster and create, `PATCH` update, the capability catalogue, grants list/create
   and revoke) is declared in `backend/identity/routes.py` / `backend/identity/main.py`;
10. 17 static testids plus 5 dynamic ones exist for a future browser suite;
11. **every** `t('…')` literal in the page exists in **both** `bn` and `en` (31+ keys);
12. every label the policy names (`ROLE_KEYS`, `roleLabel`, `active`, `inactive`, `CAPABILITY_LABEL_KEYS`) is
    translated;
13. `ROLE_LEVEL` deep-equals `ROLE_HIERARCHY` parsed from `backend/common/permissions.py`;
14. `CAPABILITY_LABEL_KEYS` keys deep-equal `DELEGABLE_CAPABILITIES` parsed from the same file.


### 4.4 Mutation — do the new tests actually catch a regression?

Removing the branch scope from the revoke call (the D6 defect, `const scope = '';`) produced

```
tests 14 / pass 13 / fail 1
AssertionError: The input did not match the regular expression /\?branch_id=' \+ encodeURIComponent\(grantRow\.branch_id\)/
```

`frontend/pages/staff.js` was then restored from a byte copy and hash-checked:

```
was=600BB633B593A6A853A6D608DCAE04DFDEAE17247A700638F1453F5947239888
now=600BB633B593A6A853A6D608DCAE04DFDEAE17247A700638F1453F5947239888
RESTORED BYTE-IDENTICAL
```

Both modules were re-run after the restore: **26 passed**.

### 4.5 What the mirror tests protect

Both mirrors in this project are deliberate and load-bearing: the browser needs the role ladder to draw a
picker, and labels must be translatable. Without a pin, a capability added server-side in a later work package
would simply not appear in the dialog — silently, with a green suite. Now, adding one to
`DELEGABLE_CAPABILITIES` **fails the frontend suite** until a label key and its two translations exist.

### 4.6 What the i18n test caught in this window

The first version of the grant/revoke handlers reused the existing status labels (`t('granted')` → `"Active"`),
so the confirmation after granting a capability read "Active" — a *status*, not a confirmation. The key-coverage
test does not catch that (the key existed); review did. Two new keys were added in both locales
(`capabilityGranted`, `capabilityRevoked`) and are now what the handlers use. The test's own job is narrower and
does hold: a key missing from either locale cannot ship.

### 4.7 Backend — written, compiled, **not run here**

`backend/identity/tests/test_staff_admin_surface.py` (15 tests) and `test_capability_grants.py` (16 tests) exist
for this surface — 31 tests covering the catalogue endpoint, branch scope changes and their audit rows, role
changes, deactivation, cross-tenant/cross-branch 404s, delegable-versus-non-delegable grants, idempotent re-grant,
revocation as a state change, and re-granting after revocation. In this window:

- `python -m py_compile` on both files → **OK** (they parse);
- `python -m pytest backend/identity/tests -q --collect-only` → **the two staff files collect cleanly**, and the run
  is stopped only by a sibling file that needs the database:

```
E   sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "127.0.0.1",
    port 5433 failed: Connection refused (0x0000274D/10061)
ERROR backend/identity/tests/test_identity.py - sqlalchemy.exc.OperationalError
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
31 tests collected, 1 error in 4.98s
```

The `31` is exactly `15 + 16`: this Windows checkout has no PostgreSQL listening on the configured port, so
`test_identity.py` (44 tests) aborts while importing and nothing can be executed — but nothing in the two MP-19
modules is broken either.

The honest state is therefore: **31 backend tests exist, collect, and were not run in this window.** They are not
reported as passing. MP-19's server-side acceptance criteria (self-escalation still refused, last-admin protection
intact, cross-org assignment 404, `staff.doctor_assignment_changed` audited) stay **unverified here**, as does any
live API call or database read-back: neither is possible on this host.

### 4.8 Evidence grade for MP-19 / MP-20

| Claim | Grade | Basis |
|---|---|---|
| The screen exists, compiles and is reachable | **TESTED** | `npm run build` compiled; the route is in the route table |
| The rules it offers match the server's rules | **TESTED** | `staff-policy.test.mjs` (12) + the two mirror tests in `staff-page.test.mjs` |
| Every string is translated in both locales | **TESTED** | §4.6, enforced by test |
| The wiring calls endpoints and fields that exist | **TESTED** | §4.3 items 2, 3, 9 |
| A real browser performs these actions successfully | **NOT VERIFIED** | no E2E harness in this repository (§7) — nothing was clicked |
| The API returns these payloads | **NOT VERIFIED HERE** | no database on this host (§4.7) |

---

## 5. Files touched

| File | Lines | Change |
|---|---:|---|
| `frontend/pages/staff.js` | 704 | Rewritten from scratch: full lifecycle screen, two dialogs, both gate states, `getServerSideProps` stub removed |
| `frontend/lib/staff-policy.js` | 114 | The screen's rules, extracted so they can be asserted without a browser |
| `frontend/lib/i18n.js` | 354 | Keys added in `bn` (lines 137, 149–153) and `en` (lines 295, 307–311): `allRoles`, `allStatuses`, `email`, `password`, `create`, `saving`, `deactivateConfirm`, `activateConfirm`, `lastActiveSelf`, plus `capabilityGranted`, `capabilityRevoked` added after review (§4.6) |
| `frontend/tests/staff-page.test.mjs` | 210 | **New** — 14 wiring/mirror/i18n assertions (§4.3) |
| `frontend/tests/staff-policy.test.mjs` | 159 | 12 rule tests (written with the policy module; re-run and green here) |
| `backend/identity/tests/test_staff_admin_surface.py` | 223 | 15 tests — written, compiled, **not run** (§4.7) |
| `backend/identity/tests/test_capability_grants.py` | 240 | 16 tests — written, compiled, **not run** (§4.7) |

No backend production file was modified for MP-19/MP-20: the server surface already existed and already
enforced every rule the screen now offers.


---

## 6. Governance and Skill Compliance (`.clinerules` §6)

### 6.1 Documents read and applied

| Domain routed (§4) | Document applied | How it shaped this work |
|---|---|---|
| Frontend UI / components / pages / forms / dialogs | `saas-frontend-ux.md` (as adapted in `docs/governance/AMSDP_Engineering_Governance_Assessment.md` §3), `docs/implementation/AMSDP_UI_UX_and_Reusable_Components_Assessment.md`, the shared components in `frontend/components/ui/` | The dialogs use the existing `Modal`, `FormRow`, `Field`, `Input`, `Select`, `PermissionDenied` and `RequireLogin` rather than new primitives; every field has a label and every status message a `role="alert"`/`role="status"` |
| Auth / RBAC / permissions | `saas-auth-and-authorisation.md` (adapted), `docs/product/AMSDP_Business_Rules_V1.0.md` §7–8, `backend/common/permissions.py`, `frontend/lib/auth.js` | `staff.read` / `staff.manage` gates, `grantableRoles`, `mayGrantCapabilities`, and the rule that the disabled control is a convenience while the server stays authoritative |
| Multi-tenant data / org-branch isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–6 | `organization_id` comes from the session and the server re-derives it from the token; another tenant's row is a non-disclosing 404, and the page renders the server's own message rather than a guessed one |
| Audit / data integrity | `saas-observability.md` (adapted), Business Rules Part X, `backend/common/audit.py` | The diff-based PATCH and the two-step deactivation exist so the append-only trail records changes, not re-writes |
| Documentation placement | `.clinerules` §11–§12, `docs/governance/AMSDP_Docs_Index_V1.0.md` | This report is in `docs/implementation/`; the index annex and the execution register were updated in the same window (§8) |

`.clinerules` §12 step 3 was followed first: `docs/governance/AMSDP_Docs_Index_V1.0.md` was consulted before
planning, and the roadmap row for MP-19/MP-20 was read verbatim rather than reconstructed from memory.

### 6.2 Skills

**No skill package is installed in this workspace** (`.clinerules` §5: no `.clinerules/skills/`, `.claude/skills/`
or repo `skills/` directory, no Cline skill configuration). No skill was claimed or simulated. The work used the
governance documents named in §6.1 and the existing project artefacts.

### 6.3 Non-negotiables (`§3`) — point by point

| Rule | Status here |
|---|---|
| Never log or expose secrets | No token, credential or password is logged. The password field is write-only: it is never read back into the edit dialog and never placed in a notice or error string |
| The UI is never the fallback safety boundary | Stated in the page header and in D7. Every control the page disables is refused again by the API, and the page surfaces the refusal instead of hiding it |
| Access enforced server-side, principal from the token | The page sends `organization_id` for the roster query and the server ignores it for non-super-admins; `PATCH` scopes by the token's org/branch |
| Cross-tenant / cross-branch fails closed with 404 | Nothing in the page turns a 404 into a client-side "not allowed" screen; the server's non-disclosing 404 is what the user sees |
| `organization_id` is the only tenant key | No second tenant column introduced |
| Audit append-only; denials recorded | No delete path in this screen at all — deactivation is a status change (D8), revocation is a status change on the grant row. Denials are the server's 403/404 plus its audit row; the page adds no silent swallow |
| Forward-only idempotent migrations for schema change | No schema change: MP-19/MP-20 add no table, column or index, so no migration is part of this work package |
| Never claim unverified capability | §4.7/§4.8 state plainly that the backend tests were not run here and that no browser ran; the register row is graded accordingly |
| Do not use a tool/library merely because it was discovered | No dependency added (D11) |

### 6.4 Deviations and exceptions

1. **No browser verification.** MP-19's own acceptance language ("the UI cannot grant…", "self-escalation still
   403") is best confirmed by clicking; this repository has no Playwright/E2E harness and adding one is a
   dependency + configuration decision, not a side effect of a page rewrite. Recorded as an open item (§7 O-2),
   and the register row is **not** marked VERIFIED because of it.
2. **No backend run in this window.** §4.7 — host has no reachable PostgreSQL. The 31 tests are written and
   compile; they must be run on a host with the database before MP-19 can be called TESTED end-to-end.
3. **Mutation coverage is one case, not a campaign.** §4.4 demonstrates the suite is not vacuous for the rule most
   likely to regress silently (revoke scope). A fuller mutation pass over the other 13 assertions was not run.


---

## 7. Open items, and what should happen next

| # | Item | Effect | Suggested handling |
|---|---|---|---|
| **O-1** | **Backend suites unrun** (§4.7) — no PostgreSQL reachable from this Windows checkout | The 31 staff/identity tests and the whole Phase-1 backend suite are unconfirmed in this window | Run `python -m pytest backend/identity/tests -q` on a host with the database before MP-19 is treated as TESTED end-to-end |
| **O-2** | **No E2E harness** — Playwright is not configured in this repository | List/create/edit/deactivate/role/branch/grant/revoke are asserted against source, not against a running stack | A separate work package: add Playwright, a `test:e2e` script, auth seeding, and the staff journeys (including the denied case). This report does not pretend it exists |
| **O-3** | The full mutation campaign over `staff-page.test.mjs` was not run (§6.4.3) | Confidence for 13 of the 14 assertions rests on inspection | Optional; cheap to do when the E2E work package runs |
| **O-4** | Pre-existing red pair Q-3 — the BanglaNameSense dataset-hash assertion **and** `tests/calendar-render.test.mjs` failing to load on Windows (`ERR_UNSUPPORTED_ESM_URL_SCHEME`) | The frontend suite is not green; both are unrelated to MP-19 and unchanged by it | Needs an owner decision on the dataset hash, and a one-line fix (`pathToFileURL`) for the calendar test. Not touched here |
| **O-5** | MP-20 acceptance mentions "revocation takes effect on the next request" | True by construction (grants and assignments are read per request in `common/auth.py`), but not demonstrated live in this window | Covered by O-1: the identity tests assert it, and they must be run |
| **O-6** | MP-17 (duplicate allowance) and MP-18 (schedule-edit audit) remain ahead of MP-21 in plan order | Not started | Next eligible task per the register after MP-19/20 is closed |

**Next eligible work package.** With MP-19 and MP-20 delivered to the grade recorded in §4.8, the register's
"what is executable right now" list advances to **MP-17** (duplicate appointment allowance, P2, depends on
MP-02) and **MP-18** (schedule-edit audit, P2), both of which can be worked without a product decision. The
P1 row that follows in the administration work package is **MP-21** (subscription lifecycle), which the roadmap
marks with an owner gate, so it is not next.

---

## 8. Where this report is registered

- **Docs Index:** `docs/governance/AMSDP_Docs_Index_V1.0.md` — annex *"MP-19 staff and permission management
  report (2026-11-24)"* added, with the file's byte size, its "read when" line, and the tree count updated
  **141 → 142** (measured).
- **Execution register:** `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` — a row each for **MP-19**
  and **MP-20** in §2, the evidence pointers quoted from §4 here, and §7's next-task line advanced.
- **Nothing was moved, renamed or deleted**, so no migration-manifest entry was created and no version number
  was advanced (D-5).
