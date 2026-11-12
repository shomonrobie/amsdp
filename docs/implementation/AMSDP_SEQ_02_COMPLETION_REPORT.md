# AMSDP — Sequence 2 Completion Report: Patient Queue Visibility (DQDS)

**Sequence:** 2 — Digital Queue Display System (DQDS), M9-C hardening pass
**Date:** 2026-11-09
**Tree:** `/home/shomonrobie/amsdp`, branch `hackathon-mvp`, base commit `eb87cac`
**Status:** **IMPLEMENTED + TESTED + VERIFIED** in this tree.
Acceptance is a separate product-owner act and is **not** claimed. No commit,
no push, no merge, no deploy was performed in this sequence.

---

## 1. Scope and objective

DQDS already existed (M9-C, `AMSDP_M9_Implementation_Readiness_Assessment.md`
§18). Sequence 2 was a **hardening and gap-closing pass**, not a rebuild:

1. Audit the existing public board end-to-end (backend endpoint, display page,
   business rules, PQV privacy decision, M9 readiness assessment).
2. Close the security/robustness gaps found in the audit.
3. Cover every audit case with an automated test.
4. Prove the result with real command output (tests, build, live HTTP).
5. Report honestly, including what is still deferred.

Explicitly out of scope: PQT (already delivered), notifications, org PQV
config, WhatsApp/SMS, deployment, commits.

## 2. Governance and skill compliance

Selected per `.clinerules` §4 routing table:

| Domain | Governance documents applied | Skill |
|---|---|---|
| Backend API / public endpoint | `saas-application-security.md` (adapted), Business Rules Parts II–X | none installed |
| Auth / access control | `saas-auth-and-authorisation.md` (adapted), Business Rules §7–8 | none installed |
| Multi-tenant isolation | `saas-multitenant-data.md` (adapted), Business Rules §4–6 | none installed |
| Queue / tokens / workflow | Business Rules Parts V–VII, M5 Queue Implementation Report | none installed |
| Rate limiting | `saas-api-throttling.md` (concurrency section, adapted) | none installed |
| Frontend UI | `saas-frontend-ux.md` (adapted), AMSDP UI/UX assessment, `frontend/lib/i18n.js`, `frontend/components/` | none installed |
| Audit / observability | `saas-observability.md` (adapted — redaction, denial recording) | none installed |

**Skills: NONE available.** Verified again in this session: no
`.clinerules/skills/`, no `.claude/skills/`, no repo `skills/` directory. The
governance documents above were used instead; no skill usage is claimed.

Non-negotiables actually exercised:

- **Cross-tenant fails closed with 404, never 403** — enforced in
  `_not_found()` and asserted by three tests plus a live call.
- **Tenant key is `organization_id`** — no second tenant column introduced;
  the doctor join is additionally constrained to the same `organization_id`.
- **Never trust the UI as a boundary** — the page hides nothing; every rule
  (active org/branch/doctor, status filtering, isolation) is enforced in the
  endpoint, and the page merely renders the answer.
- **No secrets/PII in output** — allow-list response builder; no patient or
  tracking-token material is reachable (tested recursively + by marker scan).
- **Denials are not silently swallowed** — see §11 for the one deliberate
  exception (public board has no audit subject; details below).
- **No schema change** — DQDS reads existing tables; no migration was needed
  or written.
- **No invented evidence** — every number in §7–§9 is copied from a command
  run in this tree during this session.


---

## 3. Audit findings (baseline before this sequence)

| # | Finding | Severity | Where |
|---|---|---|---|
| A1 | Unknown org / unknown branch returned 404, but a **suspended/expired organization** and a **disabled branch** still served a board | High | `_org_branch_or_404` had no status predicate |
| A2 | A queue row whose `doctor_id` pointed into another tenant would still join that tenant's doctor row (name leak) | High | doctor join not constrained to `QueueEntry.organization_id` |
| A3 | Doctors whose roster row was deactivated were still advertised | Medium | no `Doctor.status` predicate |
| A4 | Responses carried **no** `X-RateLimit-*` / `Retry-After` signalling; a 429 was a bare refusal | Medium | limiter raised without headers |
| A5 | Rate-limiter buckets were never pruned (unbounded growth on a public endpoint) | Medium | `_DQDS_RATE` grew per IP forever |
| A6 | `currently_serving` ignored `called` rows entirely (only `in_consultation`), so a just-called token showed as `—` until the consult started | Medium | aggregation |
| A7 | 404/429 responses were cacheable in principle; a shared cache could pin an error | Low-Medium | no `Cache-Control: no-store` on errors |
| A8 | The display page resolved route/`lang` during render → hydration mismatch risk, and had no `?lang=` override, no not-found state, no stale-on-error recovery, no `aria-live` affordances | Medium | `frontend/pages/queue-display/[org]/[branch].js` |
| A9 | No test covered limiter headers, inactive org/branch/doctor, cross-org doctor join, `called`-serving, or PQT-material absence | Medium | `backend/tests/test_dqds.py` (14 tests) |

Preserved behaviours that the audit confirmed as **correct and untouched**:
`skipped` stays counted in `patients_waiting` (Business Rules + M9 §18.2) and is
never shown as "now serving"; `completed` / `cancelled` / `no_show` stay
terminal and invisible; only today's rows for that exact `branch_id` are read.

## 4. Backend changes — `backend/queuing/display.py` (201 lines)

No route, table, migration or dependency changed. Endpoint remains
`GET /api/v1/queue/display/{org_code}/{branch_code}` (mounted by
`backend/queuing/main.py`, proxied by `frontend/next.config.js`
`/api/v1/queue/:path* → queuing:8006`).

| Finding | Fix |
|---|---|
| A1 | `_active(col)` → `or_(col == "active", col.is_(None))`; the organization and its branch are resolved **together** through `_org_branch_or_404()`, and any failure raises the single shared `_not_found()`. `NULL` status is treated as active on purpose: rows that predate suspension support were never explicitly disabled, so hiding them would be a silent outage. |
| A2 | Join constrained: `Doctor.organization_id == org.id`, plus `QueueEntry.organization_id == org.id`, `QueueEntry.branch_id == branch.id`, `QueueEntry.date == today`. A mis-joined row can no longer publish another tenant's doctor name. |
| A3 | `_active(Doctor.status)` added to the same filter. |
| A4 | `_rate_headers(remaining, reset_epoch)` emits `X-RateLimit-Limit` (30), `X-RateLimit-Remaining`, `X-RateLimit-Reset` on **every** response the limiter touches; refusal adds `Retry-After` (seconds, ≥1). |
| A5 | `_prune_rate_state()` sweeps expired buckets every `_DQDS_PRUNE_EVERY` (512) requests; bounded memory without a background task. |
| A6 | Aggregation buckets now track `called` and `in_consultation` separately; `currently_serving = in_consultation or called`. `patients_waiting` unchanged (`waiting` + `called` + `skipped`). |
| A7 | `_PUBLIC_CACHE = {"Cache-Control": "public, max-age=10"}` on board data; `_ERROR_HEADERS = {"Cache-Control": "no-store"}` on 404 and 429. |

Response construction is an explicit allow-list (`doctors_out` built key by key),
so internal aggregation state is structurally unreachable — the previous
`_serving_rank` helper field is gone entirely (grep for `_serving_rank` in the
file returns nothing).

## 5. Frontend changes — `frontend/pages/queue-display/[org]/[branch].js` (198 lines)

Plain JavaScript, Next.js 14 Pages Router, no new dependency. Same route
(`/queue-display/{org}/{branch}`), same public access (no AppShell, no auth
guard), same 10 s poll matching the `max-age=10` cache window.

| Finding | Fix |
|---|---|
| A8 (hydration) | Route and language are resolved **after mount** in a `useEffect` (route state starts `undefined` = "resolving"), so the server-rendered markup and the first client render agree. No `window` access during render. |
| A8 (language) | `initialLang()` precedence: `?lang=bn|en` → `localStorage['dqds_locale']` (survives TV restarts) → staff preview `sessionStorage['locale']` → `bn` default. Storage access is wrapped in `try/catch` (private-mode / no-storage displays degrade to the default instead of crashing). A visible toggle persists the board's own choice. |
| A8 (states) | Explicit phase machine: `loading → ready | notfound | error`, plus an **empty-queue** state ("no patients waiting"). A 404 renders a localized not-found panel (never a raw error); other failures render a retry panel with a working **Retry** button (bumps a nonce, re-runs the effect). |
| A8 (resilience) | Stale-while-error: a failed poll keeps the last known board on screen, flags it with a localized "connection lost — showing the last known queue" strip, and the next successful poll clears the flag automatically. An `inFlight` guard prevents overlapping polls; the interval is cleared on unmount/route change. |
| A8 (a11y) | `role="status"` on loading/empty, `role="status"` on the stale strip, `aria-live="polite"` on the doctor grid so token changes are announced, `aria-label` on the language toggle, real `<h2>` headings in the error/empty panels, `<button type="button">`. |
| — | Times are formatted with `Intl.DateTimeFormat` (`bn-BD` / `en-GB`) from the server's `updated_at`, so the board shows the API's timestamp rather than an unsynchronised client clock. |
| — | The shell (org/branch header + footer) stays mounted in **every** state, so a monitor always states which branch it belongs to; org/branch fall back to the URL codes before the first successful poll. |

i18n: the board keeps its own `L` map (`bn`/`en`) instead of
`frontend/lib/i18n.js`, because it is a standalone public surface with no auth
context and its copy has no overlap with staff screens (verified: `grep` for
`dqds` in `lib/i18n.js` returns no matches). This is a deliberate deviation,
recorded in §11.

## 6. Display styling — `frontend/styles/global.css`

Appended a clearly delimited DQDS block (existing `dqds-*` rules untouched):

- `.dqds-header-right`, `.dqds-lang` — header column + language toggle.
- `.dqds-stale` — the offline/stale strip; `.dqds-error h2`, `.dqds-error p`,
  `.dqds-retry` — localized error panel and its button.
- `@media (min-width: 1200px)` — TV/monitor scaling (card 1180 px, org 1.7 rem,
  doctor name 1.4 rem, token 2.5 rem, waiting count 1.9 rem, row padding).
- `@media (max-width: 480px)` — phone fallback: rows stack, info row spreads.

No global selector was added or redefined; everything is scoped under `.dqds-*`.


## 7. Tests — `backend/tests/test_dqds.py`, 24 tests, all passing

The 14 pre-existing DQDS tests were kept unchanged; **10 were added** for the
audit gaps. Test isolation was extended so the new cross-org fixture cannot
leak into later runs (`_ensure()` now also clears the foreign doctor and any
doctor owned by the two test orgs, children first; `_clear()` resets
`_DQDS_RATE`).

| # | Test | Covers |
|---|---|---|
| 15 | `test_dqds_rate_limit_headers` | 200 carries `X-RateLimit-Limit/Remaining/Reset` (remaining 0 on request 30); 429 is never bare (`Retry-After` ≥ 1, limit 0 remaining, reset, `no-store`) |
| 16 | `test_dqds_not_found_is_non_disclosing_and_uncacheable` | unknown org ≡ unknown branch ≡ cross-org branch → identical `404 {"detail":"not found"}` with `no-store` |
| 17 | `test_dqds_inactive_org_404` | suspended org → 404; reactivated → 200 |
| 18 | `test_dqds_inactive_branch_404` | disabled branch → 404; reactivated → 200 |
| 19 | `test_dqds_inactive_doctor_not_published` | deactivated doctor's stale rows are not advertised |
| 20 | `test_dqds_cross_org_doctor_name_never_leaks` | row in org A pointing at org B's doctor publishes nothing; name absent from the whole payload |
| 21 | `test_dqds_idle_doctor_not_listed` | doctors with no active entry today are not listed (documents §11 limitation) |
| 22 | `test_dqds_serving_prefers_in_consultation` | `in_consultation` beats a lower-position `called`; waiting count excludes the in-consultation patient |
| 23 | `test_dqds_skipped_never_shown_as_serving` | `skipped` counts as waiting but is never "now serving" |
| 24 | `test_dqds_never_returns_tracking_material` | no `tracking` / `token_hash` / `token_prefix` / `/track/` markers; serving token appears exactly once; queued tokens never appear |

Commands and real output:

```
$ cd backend && python3 -m pytest tests/test_dqds.py -q
24 passed, 3 warnings in 2.07s

$ (re-run, proving idempotence / no cross-run DB pollution)
24 passed, 3 warnings in 2.20s

$ (final run, after the trailing-newline fix to display.py)
24 passed, 3 warnings in 1.67s
```

## 8. Regression

```
$ cd backend && python3 -m pytest tests/ queuing/tests/ identity/tests/ \
    --ignore=tests/test_e2e.py -q
118 passed, 19 warnings in 8.92s
```

118 = the 108 recorded in M9 §18.6 + the 10 new DQDS tests. No pre-existing
test changed state, and `tests/test_e2e.py` is still excluded for the same
pre-existing, unrelated collection error documented in M9 §18.6.

Frontend production build (proves the rewritten page compiles and prerenders):

```
$ cd frontend && npx --no-install next build      # EXIT=0
○ /queue-display/[org]/[branch]   2.31 kB   86.8 kB     (prerendered as static)
✓ Generating static pages (9/9)
```


## 9. Live verification (VERIFIED, not just a green suite)

`python3 -m uvicorn queuing.main:app --port 8125` against the real Postgres,
with a seeded branch (`live-seq2-org` / `live-seq2-br` / `Dr. Live`) holding
1 `in_consultation` (L-001), 1 `called` (L-002), 1 `waiting` (L-003),
1 `skipped` (L-004), 1 `completed` (L-005), 1 `cancelled` (L-006).
Output below is captured verbatim (`/tmp/live2_out.txt`) from
`bash /tmp/live2_verify.sh`.

**1. The board — correct tokens, counts, cache and limiter headers**

```
=== 1. BOARD (expect 200) ===
HTTP/1.1 200 OK
date: Mon, 09 Nov 2026 06:14:43 GMT
server: uvicorn
cache-control: public, max-age=10
x-ratelimit-limit: 30
x-ratelimit-remaining: 27
x-ratelimit-reset: 1794204944
content-length: 277
content-type: application/json

{"organization": {"name": "Live Seq2 Hospital", "code": "live-seq2-org"}, "branch": {"name": "Live Branch", "code": "live-seq2-br"}, "doctors": [{"doctor_name": "Dr. Live", "currently_serving": "L-001", "patients_waiting": 3}], "updated_at": "2026-11-09T06:14:43.785744+00:00"}
```

`currently_serving` = `L-001` (the `in_consultation` row, not the `called`
row at position 2) and `patients_waiting` = 3 (`called` + `waiting` +
`skipped`); `completed` and `cancelled` are absent from the payload entirely.
`remaining: 27` because three earlier calls in this window already counted.

**2. Unknown org, unknown branch, cross-tenant branch code — byte-identical**

```
=== 2. UNKNOWN ORG (expect 404) ===
HTTP/1.1 404 Not Found
cache-control: no-store
content-length: 22
{"detail":"not found"}

=== 3. UNKNOWN BRANCH (expect 404) ===
HTTP/1.1 404 Not Found
cache-control: no-store
content-length: 22
{"detail":"not found"}

=== 4. CROSS-TENANT BRANCH CODE (expect 404) ===
HTTP/1.1 404 Not Found
cache-control: no-store
content-length: 22
{"detail":"not found"}
```

Same status, same 22-byte body, so nothing distinguishes "does not exist" from
"exists but is not yours" (A1/A2).

**3. Suspended organization → 404; restored → 200 (the point of A1)**

```
STATUS_SET=suspended
=== 5. SUSPENDED ORG (expect 404) ===
HTTP/1.1 404 Not Found
cache-control: no-store
{"detail":"not found"}

STATUS_SET=active
=== 6. RESTORED ORG (expect 200) ===
HTTP/1.1 200 OK
cache-control: public, max-age=10
x-ratelimit-remaining: 22
{"organization": {"name": "Live Seq2 Hospital", ...}, "doctors": [{"doctor_name": "Dr. Live", "currently_serving": "L-001", "patients_waiting": 3}], ...}
```

**4. Limiter — flip point and fully-signalled refusal (A4/A5)**

```
=== 7. EXHAUST LIMITER (40 rapid requests, codes only) ===
200 ×22 then 429 ×18

=== 8. LAST RESPONSE AFTER EXHAUSTION (expect 429) ===
HTTP/1.1 429 Too Many Requests
x-ratelimit-limit: 30
x-ratelimit-remaining: 0
x-ratelimit-reset: 1794204908
retry-after: 23
cache-control: no-store
content-length: 30
{"detail":"too many requests"}
```

(Between the board call in §1 and this loop, 30 allowed requests were
consumed in the window — the 23rd loop request was the first refusal, and
every refusal carried `Retry-After`, `remaining: 0` and `no-store`.)

Cleanup (verified, not assumed): every live fixture row (queue entries,
patient, doctor, branch, organization) was deleted, the server was stopped,
and the port was confirmed closed —

```
$ python3 /tmp/clean_live_seq2.py
CLEANED
$ curl --max-time 3 .../live-seq2-org/live-seq2-br
PORT_CHECK=000
PORT_CLOSED
```


## 10. Evidence status

| Item | Status | Evidence |
|---|---|---|
| DQDS endpoint hardened (A1–A7) | **IMPLEMENTED** | `backend/queuing/display.py` (201 lines), reachable via router mount `queuing/main.py` |
| Display page rewritten (A8) | **IMPLEMENTED** | `frontend/pages/queue-display/[org]/[branch].js` (198 lines), route in the Next build output |
| Display styling | **IMPLEMENTED** | DQDS block in `frontend/styles/global.css` |
| 24 DQDS tests | **TESTED** | `pytest tests/test_dqds.py -q` → 24 passed (three runs) |
| No regression | **TESTED** | `pytest tests/ queuing/tests/ identity/tests/ --ignore=tests/test_e2e.py -q` → 118 passed |
| Page compiles / prerenders | **TESTED** | `next build` EXIT=0, `/queue-display/[org]/[branch]` static, 2.31 kB |
| Public board serves correct tokens/counts | **VERIFIED** | live 200 body/headers (§9) |
| Cross-tenant/unknown/suspended fails closed 404 | **VERIFIED** | live 404 + live suspend/restore (§9) + 3 tests |
| Limiter signalling | **VERIFIED** | live 429 with `Retry-After` (§9) + test 15 |
| Accepted | **NOT CLAIMED** | product-owner act, outside this sequence |

Anything not listed as VERIFIED above is not claimed as verified.

## 11. Deviations, limitations, deferred items

1. **Rate limiter is per-process** (`_DQDS_RATE` dict). Behind multiple
   replicas each process allows its own 30 req/min. Deliberately deferred to
   M9-F (durable shared limiter), as already recorded in M9 §18.3/§18.10. The
   limit is a denial-of-service brake on a public feed, not an authorisation
   control, so this is acceptable for the MVP but must be revisited before
   horizontal scaling.
2. **Doctors with no active entry today are not listed.** The board shows
   doctors who have work in the queue, not the roster. Documented by test 21 so
   the behaviour is explicit rather than accidental. If the product wants an
   idle-doctor roster panel, that is a follow-up decision (it would also expose
   doctor names of doctors with no queue activity).
3. **Only the currently-serving token is published**; queued tokens are never
   exposed (test 24). That is the privacy decision in M9 §15.3, unchanged.
4. **DQDS has its own i18n map** rather than `frontend/lib/i18n.js` (rationale
   in §5). No staff i18n key was added or modified.
5. **No browser/E2E harness exists in this repo**, so the page's runtime
   behaviour is covered by the production build (compile/prerender) and by the
   endpoint tests — not by a browser run. This is stated rather than papered
   over; the earlier milestone report had the same limitation.
6. **Denial auditing**: the public board intentionally writes no audit event —
   requests carry no authenticated principal, no org is derived from a token,
   and there is no denial subject to record. Rate-limit refusals are logged by
   the ASGI server, not the audit trail. If the product later requires
   per-org abuse telemetry, it belongs to the M9-F limiter work.
7. **`NULL` status = active** for organization/branch/doctor. Deliberate (see
   §4/A1), and it is the reason the pre-suspension data path keeps working.

## 12. Handoff

Changed or added in this sequence (nothing staged, committed or deployed):

```
?? backend/queuing/display.py                        (new, M9-C + Seq 2)
?? backend/tests/test_dqds.py                        (new, 24 tests)
?? frontend/pages/queue-display/[org]/[branch].js    (new, Seq 2 rewrite)
 M frontend/styles/global.css                        (DQDS block appended at EOF)
?? ai_factory/docs/AMSDP_SEQ_02_COMPLETION_REPORT.md (this file)
?? ai_factory/docs/AMSDP_M9_Implementation_Readiness_Assessment.md (§18.12 addendum)
```

Note on the one `M` entry: `frontend/styles/global.css` **already carried
uncommitted work** from earlier milestones before this sequence started
(`git diff` against HEAD is a whole-file change). This sequence only appended
a trailing DQDS block (`.dqds-header-right`, `.dqds-lang`, `.dqds-stale`,
`.dqds-error`, `.dqds-retry` + the 1200 px / 480 px media queries); none of the
pre-existing uncommitted changes in that file or anywhere else in the tree were
altered, reverted, or staged. The rest of `git status` (other modified backends,
docs, `_tools/`, `runs/`, `var/`) is pre-existing work owned by other
sequences and was not touched here.

Next sequence can start from this state. Known open work handed over:
shared/durable rate limiter (M9-F), optional idle-doctor roster panel
(product decision), browser-level E2E harness (not present in the repo),
and product-owner acceptance of PQV/DQDS.

**Stop point:** Sequence 2 is complete. No commit, push, merge, or deployment
was performed, and no acceptance is claimed.

