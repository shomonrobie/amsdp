# AMSDP — Live Deployment Baseline Reconciliation Report, V1.0

**Date:** 2026-11-24 · **Checkout:** `E:\amsdp` (Windows workstation) · **Branch:** `hackathon-mvp`
· **HEAD:** `a4ddc2cf58e019b57dccf59f3a859743e3c48430`
**Task type:** read-only verification plus documentation reconciliation. **No production action.**
**Status:** the live migration is **completed**, not outstanding. This report corrects the claim that the
live database is two migration stages behind, reconciles every operative document to the verified
baseline, and states exactly which facts were freshly verified here and which were not.

---

## 1. Executive summary

For three consecutive documents — the merge publication report (2026-11-23), the Windows/Ubuntu
runbook (2026-11-23) and, downstream of both, the requirements reconciliation audit and the master
implementation plan (2026-11-24) — the project carried a single sentence: **"the live database is two
revisions behind head."** It was true when it was first measured. It stopped being true later the
same day, when the migration was applied.

The verified deployment record establishes the actual baseline:

| Item | Verified state |
|---|---|
| Previous database revision | `a9c4e1f7b2d8` |
| Live database revision | **`c4d8e2a91f60` (head)** |
| Migration date | 23 November 2026 · **applied successfully** |
| New tables | `voice_packs`, `queue_announcement_deliveries`, `announcement_platform_config` |
| Safety method | Rehearsed against a disposable restored database first; pre-migration backup taken |
| Data preserved in the rehearsal | organizations 421 · patients 2963 · doctors 601 · appointments 642 · queue_entries 11 · audit_events 20490 |

Fresh verification performed for this task, on 2026-11-24, from this Windows checkout:

- **Branch and HEAD match the baseline exactly** — `hackathon-mvp`, `a4ddc2cf58e019b57dccf59f3a859743e3c48430`.
- **The deployment is reachable and healthy**: `192.168.68.108:8110`–`8117` (eight services) and `:3100` (frontend) all returned **HTTP 200**.
- **The deployed code is the post-merge tree**: the live organization service advertises all eleven `/api/v1/voice-packs…` routes and the platform/org announcement-config routes; the live queue service advertises the W2 announcement-delivery routes. Those routes exist only in the merged tree whose single head is `c4d8e2a91f60`.
- **The revision graph is single-headed**: 16 revisions, head `c4d8e2a91f60`, chain `a9c4e1f7b2d8 → a7c3f19d2b64 → c4d8e2a91f60`, no dangling parent.

**Not** freshly verified: the live database revision itself and the presence of the three tables.
This host has no `alembic`, `psql` or `docker` binary and no database credential, and the task forbids
writing to production — which obtaining a token would require. That gap is stated, not papered over,
and MP-01 closes it with a quoted `psql` read.

**What changed, in one line:** every operative document now records the migration as **completed**;
the historical "two revisions behind" statements are preserved as history with dated corrections; the
remaining genuinely-open item is the **post-migration suite baseline**, not the migration.

---

## 2. Previously reported state, and why it was incorrect

### 2.1 What the documents said

| Document | Statement | Where |
|---|---|---|
| `implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md` | "the live database is still behind" | header, §7 blocker row, §10 next actions |
| `implementation/AMSDP_Windows_Ubuntu_Development_and_Deployment_Runbook_V1.0.md` | "The live database is **two revisions behind** the merged code" | §1.4, §4.3, §11 blocker row |
| `implementation/AMSDP_Implementation_State_and_Next_Task_Report_V1.0.md` | "that migration is the next planned task and is **not** done" | header, §D runtime row, §E E-1 |
| `audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | "live database two revisions behind head" (**GAP-01**, S1) | §1.1, §2.1, §7, §8, §12 |
| `plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | "live DB two revisions behind head"; MP-01 = "restore runtime + migrate" | §3.1, §5.2, §5.3, MP-01, R-1, GAP-01 row, Appendix B |

### 2.2 Why it was incorrect — four links, in order

1. **It was a true measurement.** On 2026-11-23 runbook §1.4 recorded, against the running `amsdp-db-1` container: `select version_num from alembic_version → a9c4e1f7b2d8` and `select to_regclass('voice_packs') → (null)`. The whole-tree suite run (`682 passed / 109 errors`) was produced against that database.
2. **The migration was applied after those documents were written** — later on 2026-11-23, rehearsed on a disposable restored database, with a pre-migration backup. **No document inside this repository recorded the application.** The verified deployment record lives outside the tree.
3. **The audit and the plan inherited the sentence as current fact.** Both labelled it `DOCUMENTED`/`REPORTED` — which is honest about provenance and useless about freshness: the measurement was already superseded when quoted.
4. **A probe error reinforced it.** The earlier session probed `:8000` and `:3000` and concluded "host unreachable". Those are **container-internal** ports on the Ubuntu host. From this Windows checkout the same deployment answers on `192.168.68.108:8110–8117` and `:3100`. Re-probed on 2026-11-24, every service answered on the first attempt.

**So the source was stale documentation, not old test output and not a fresh environment snapshot.** The `109 errors` *are* old test output, but they are a **consequence** of the pre-migration database and are fully explained — not an independent defect.

---

## 3. Authoritative previous and current migration revisions

| Field | Value |
|---|---|
| Repository | `shomonrobie/amsdp` |
| Branch | `hackathon-mvp` |
| Last verified commit | `a4ddc2cf58e019b57dccf59f3a859743e3c48430` (`a4ddc2c`, 2026-11-23 20:21:43 +0600) |
| Previous database revision | `a9c4e1f7b2d8` — *appointment types and capacity integrity* |
| Live database revision | **`c4d8e2a91f60`** — *add voice packs and platform config*, **single head** |
| Intermediate revision applied | `a7c3f19d2b64` — *add queue announcement deliveries* |
| Migration date | 23 November 2026 |
| Outcome | Applied successfully, after a rehearsal on a disposable restored database |
| Tables the two revisions created | `queue_announcement_deliveries` (`a7c3f19d2b64`); `voice_packs` and `announcement_platform_config` (`c4d8e2a91f60`) |
| Pre-migration backup | Taken |
| Rehearsal record counts preserved | organizations 421 · patients 2963 · doctors 601 · appointments 642 · queue_entries 11 · audit_events 20490 |

The revision graph, recomputed statically from `backend/alembic/versions/*` (16 files) by
`scripts/que-006-w3-voice-config/check_migration_graph.py`:

```
16 revisions in backend/alembic/versions
heads: c4d8e2a91f60
  ... <- a9c4e1f7b2d8 <- a7c3f19d2b64 <- c4d8e2a91f60
```

A9c4e1f7b2d8 is exactly two steps behind the head — which is where the phrase "two revisions behind"
came from, and why the arithmetic was never in doubt; only the freshness was.

---

## 4. Evidence inspected, and how it was verified

### 4.1 Documents read

- `docs/governance/AMSDP_Docs_Index_V1.0.md` (navigation index, read first per `.clinerules` §12)
- `docs/implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md`
- `docs/implementation/AMSDP_Implementation_State_and_Next_Task_Report_V1.0.md`
- `docs/implementation/AMSDP_Windows_Ubuntu_Development_and_Deployment_Runbook_V1.0.md`
- `docs/implementation/AMSDP_QUE006_Final_Merge_Readiness_Verification_Report_V1.0.md` (§7 records `SELECT version_num FROM alembic_version → c4d8e2a91f60` read back from a database)
- `docs/implementation/AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT.md` (the separate `amsdp_demo` database, which the record does not claim was migrated)
- `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md`
- `docs/audit/AMSDP_MVP_Hackathon_Readiness_Assessment.md`, `docs/audit/AMSDP_M7_Hackathon_Readiness_Report.md`
- `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md`
- `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md`

### 4.2 Code and configuration read

- `backend/alembic/versions/` — all 16 revisions (graph reconstruction; `c4d8e2a91f60` and `a7c3f19d2b64` read in full)
- `scripts/que-006-w3-voice-config/check_migration_graph.py` — executed (static, no database)
- `backend/organization/{voice_packs,announcement_config,voice_pack_policy,main}.py` — route inventory
- `backend/queuing/` — announcement route inventory
- `docker-compose.yml` — service/port map (`8110`–`8117`, `3100`; db published on `5433`)
- `.env.local` — **keys only** inspected (two API keys; **no database credential**). Values never read into any output.

### 4.3 Commands executed (all read-only)

```
git rev-parse --abbrev-ref HEAD ; git rev-parse HEAD ; git log --oneline -30 --no-decorate
python scripts/que-006-w3-voice-config/check_migration_graph.py
Invoke-WebRequest http://192.168.68.108:8110..8117/health        (GET)
Invoke-WebRequest http://192.168.68.108:3100/                    (GET)
Invoke-WebRequest http://192.168.68.108:8111/openapi.json        (GET)
Invoke-WebRequest http://192.168.68.108:8116/openapi.json        (GET)
Invoke-WebRequest http://192.168.68.108:8111/api/v1/voice-packs  (GET → 401, route mounted)
Test-NetConnection 192.168.68.108 -Port 5433 / 8110 / 22
Get-ChildItem / Select-String over docs/ and backend/ (read-only)
```

**Deliberately not executed:** `alembic`, `psql`, `docker`, any migration, any suite, any `POST`, any restore, any Docker or compose command.

---

## 5. Live verification status — fresh versus historical

The distinction this report insists on:

| Fact | Class | Basis |
|---|---|---|
| Branch `hackathon-mvp`, HEAD `a4ddc2c…` | **VERIFIED today** | `git rev-parse`, this checkout |
| Single head `c4d8e2a91f60`; `a9c4e1f7b2d8` is two steps behind | **VERIFIED today** | static graph reconstruction, executed |
| Eight services + frontend up and answering | **VERIFIED today** | HTTP 200 from `192.168.68.108:8110`–`8117`, `:3100` |
| Deployed code is the post-merge tree (W2 + W3 routes mounted) | **VERIFIED today** | `/openapi.json` of the organization and queue services; `/api/v1/voice-packs` returns `401 authentication required`, not `404` |
| PostgreSQL published on `0.0.0.0:5433` and reachable | **VERIFIED today** | TCP connect to `192.168.68.108:5433` succeeded |
| No SSH listener on the host | **VERIFIED today** | TCP connect to `192.168.68.108:22` failed |
| Live database at `c4d8e2a91f60`; three tables created; migration on 23 Nov 2026 | **REPORTED** (verified deployment record) | Not re-queried here — no client binary, no credential |
| Seeded counts preserved (421 / 2963 / 601 / 642 / 11 / 20490) | **REPORTED** | Rehearsal record; not re-counted here |
| `790 pass / 1 fail`, `682 passed / 109 errors`, `109 passed` | **HISTORICAL** | Prior sessions' logs; **no suite ran in this task** |
| `109` errors now clear on the migrated DB | **PREDICTED** | Inference from cause; must be proven by MP-02 |

**What the service probes cannot prove.** Every `/health` returns a static body
(`{"status":"ok","service":"…"}`) and queries no table. Liveness therefore says nothing about schema
revision. The deployed-route evidence is stronger — those routes ship in the same commit as the
migration file — but a route existing in the image still does not prove a table exists in the
database. Only a `psql` read of `alembic_version` / `to_regclass(...)`, or an authenticated call that
queries the three tables, settles it. Both are outside this task: the first needs a client this host
does not have, the second needs a `POST /api/v1/staff/login`, which writes a login-attempt row.

---

## 6. Documentation files reviewed and changed

| File | Action | What changed |
|---|---|---|
| `docs/implementation/AMSDP_Live_Deployment_Baseline_Reconciliation_Report_V1.0.md` | **created** | This report |
| `docs/audit/AMSDP_Requirements_Reconciliation_and_Implementation_Gap_Audit_V1.0.md` | amended | **§16 Amendment A-3** added (baseline, fresh-vs-historical evidence, root cause, scope of change); §1.1 verdict row, §1.4 recommendation, §2.1 live-DB row, §2.3 two "not executed" rows, §7 **GAP-01**, §7 totals note, §8 step 1 and §12 item 3 corrected in place |
| `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` | amended | **Appendix E — Amendment A-2** added; §3.1 runtime row, §5.2 critical-path label, §5.3 **M-1**, **MP-01**, **MP-02**, §9 **R-1**, §11 **GAP-01**, Appendix B MP-01 recipe, Appendix C next-action, change history and companion row corrected |
| `docs/implementation/AMSDP_Windows_Ubuntu_Development_and_Deployment_Runbook_V1.0.md` | amended | §1.4 marked **RESOLVED 2026-11-23** with a status banner and corrected closing advice; §4.3 prose made conditional; §4.3 command block now checks before upgrading; §8 sentence qualified as historic; §11 blocker row **CLOSED**; §12 evidence rows annotated as pre-migration measurements |
| `docs/implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md` | amended | dated correction note under the header; §7 blocker row marked **CLOSED 2026-11-23**; §10 action 1 marked **DONE**, action 2 restated as a prediction |
| `docs/implementation/AMSDP_Implementation_State_and_Next_Task_Report_V1.0.md` | amended | dated correction banner; header verdict, §D runtime row and §E **E-1** corrected |
| `docs/governance/AMSDP_Docs_Index_V1.0.md` | amended | this report registered in the annex; the correction recorded; `.md` count updated |
| `docs/architecture/AMSDP_Multi_Display_DQDS_Functional_Specification_V1.0.md` | read only | Its statement that new revisions chain on head `c4d8e2a91f60` remains correct |
| `docs/audit/AMSDP_MVP_Hackathon_Readiness_Assessment.md` (8 Nov 2026), `docs/audit/AMSDP_M7_Hackathon_Readiness_Report.md` | read only | Historical milestone assessments; neither makes a current migration claim, so neither was touched |
| `docs/implementation/AMSDP_UBUNTU_REPLACEMENT_PREFLIGHT_REPORT.md` | read only | Its statement concerns the separate `amsdp_demo` database; unchanged and not contradicted |
| `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.0.md` | read only | Superseded by V1.1; historical record retained untouched |
| `docs/implementation/AMSDP_PO13_Multi_Display_DQDS_Reconciliation_Report_V1.0.md` | read only | Its "no migration applied" statement refers to that task; still true |

**Nothing was deleted and no history was rewritten.** Every superseded sentence survives, struck
through or qualified with a date, so the record shows what was believed and when.

---

## 7. Incorrect blockers corrected or retained, with reasons

| Blocker / dependency | Was | Is now | Why |
|---|---|---|---|
| **GAP-01** — live DB behind head | S1, blocks every P0 acceptance | **Migration half CLOSED**; evidence half open; **S1 retained** | The migration is applied. The audit register is not being rewritten: the severity stays because *no post-migration suite baseline or §12 acceptance run exists*, which is a separate P0 dependency (MP-02, MP-31) |
| **MP-01** — "restore runtime + migrate" | P0, first task on the critical path | P0, **first task, redefined**: prove the runtime, read `alembic_version`, upgrade only if behind | Keeping MP-01 first is right: it is the task that converts a reported baseline into a verified one. Only the migration step changes from unconditional to conditional |
| **MP-02** — suite re-baseline | P0, "on the migrated database" | P0, unchanged, reason clarified | Still the gate on every "the suite is green" statement. It was never blocked by the migration; it is blocked by the absence of a recorded run |
| **M-1** milestone | "Runtime restored" | "**Runtime proven**" | Renamed because the restoration happened; what remains is proof |
| **R-1** migration risk | "live DB migration fails or loses data" | "a **future** migration fails or loses data" | The 23 Nov migration succeeded; the risk now applies to MP-35's `queue_displays` revision and later schema work |
| **Publication report action 1** | "back up + migrate + rebuild" | **DONE 2026-11-23**; verify first, never repeat | Acting on the old instruction would re-run an applied migration |
| **Runbook §11 blocker** | OPEN — release blocker | **CLOSED 2026-11-23** | Same evidence; the procedure text below it is retained as history |
| **State report E-1** | "back up + migrate the live DB" | "record the post-migration suite baseline" | The migration is done; the suite run is not |
| **`0.0.0.0:5433` PostgreSQL exposure** | OPEN | **OPEN — retained deliberately** | Out of scope by instruction (§6 of the task). Re-confirmed reachable; still needs an owner decision |
| **No SSH listener** | OPEN | **OPEN — retained** | Unchanged infrastructure item; not a deployment-baseline fact |
| **B-8 audibility · RBAC-R3 demo assignment · O-2 facility config · D-5 index numbering · OP-1 · OP-2 · SMS half of PO-02** | UNPROVEN / OPEN | **unchanged** | None of them depends on the migration state; none is affected by this correction |
| **`109` fixture errors** | cited as evidence of a live defect | **explained, historical** | They were fixture setup against the pre-migration schema. Treating them as current would be the same error in the opposite direction |
| **`790 pass / 1 fail`** | "the last recorded suite result" | **historical, pre-migration** | No suite has run since the migration. MP-02 must produce the number that replaces it |

**One blocker was created by the old baseline itself:** an instruction to run an unconditional
`alembic upgrade head` as the first operational step. Corrected in the runbook §4.3, the plan's
Appendix B and the publication report §10, so no future operator re-applies an applied revision.

---

## 8. Outstanding deployment and security risks

| # | Risk | State | Why it is not fixed here |
|---|---|---|---|
| 1 | **PostgreSQL published on `0.0.0.0:5433`** — reachable from the whole LAN; password-protected via `.env` only | **OPEN — SECURITY.** TCP `192.168.68.108:5433` answered on 2026-11-24 | Explicitly out of scope (task §6). Requires an owner decision and a compose/env change |
| 2 | **Live schema revision not independently confirmed** | **OPEN — evidence gap** | No `alembic`/`psql`/`docker` on this host, no DB credential, and a token would need a writing `POST`. MP-01 closes it |
| 3 | **No post-migration suite baseline** | **OPEN — verification gap** | MP-02. Until a log exists, no "suite is green" claim is admissible |
| 4 | **No SSH listener on the host** | OPEN | Owner decision; transport is Git today |
| 5 | **Docker/compose versions and container count of the live host** | UNVERIFIED here | Could not be inspected from this checkout |
| 6 | **`amsdp_demo` database** (separate from the live `amsdp` DB) | **UNVERIFIED** — the preflight report says it stays at `a9c4e1f7b2d8` | The verified record does not claim it was migrated; it will need the same two revisions before the demo stack is usable. Do not assume it moved |
| 7 | **B-8 audibility, RBAC-R3 demo assignment, O-2 facility config** | UNPROVEN | Need a human in the room and seeded-data inspection |

Risk 6 is the one most likely to be misread as covered by this reconciliation: **it is not.** The
migration record concerns the live `amsdp` database.

---

## 9. Confirmation: code, database, migrations and production untouched

**Confirmed.** Stated precisely, so it can be checked:

| Surface | State | Evidence |
|---|---|---|
| `backend/`, `frontend/`, `alembic/`, `ai_factory/`, `scripts/`, `docker-compose*.yml` | **untouched** | `git status --porcelain` filtered to those paths returns **no entries** |
| Alembic revisions | **untouched** — no file added, edited or deleted; no `alembic` command run | Static graph read only |
| Database | **no connection made** from this host; no `SELECT`, no `INSERT`, no restore, no reseed | No client binary and no credential present; `.env.local` holds two API keys only |
| Migrations | **none executed** — not against production, not against any database | No `alembic` binary; nothing run |
| Production services | **not restarted, rebuilt or modified**; no Docker command issued | `docker` is not installed on this host |
| Docker configuration / containers / volumes | **untouched** | Same |
| Git | no commit, no stage, no reset, no clean, no force-push, no branch or tag change | `git status` shows tracked modifications and untracked files only |
| Live API | **read-only GET requests only** — health, `/openapi.json`, one unauthenticated `401` probe, TCP port checks | Logged in §4.3; **no `POST`, no login, no write** |
| Secrets | **none read into any output**; `.env.local` inspected for key names only | §4.2 |

Working-tree state at the end of this task: **14 entries, all documentation** —
`M` on `.clinerules`, `docs/AMSDP_Business_Rules_V1.1.md`, `docs/product/AMSDP_Business_Rules_V1.0.md`,
`docs/governance/AMSDP_Docs_Index_V1.0.md`, `docs/audit/AMSDP_Phase_3_Queue_DQDS_QUE-006_Gap_Analysis_V1.0.md`,
`docs/implementation/AMSDP_Final_Merge_Publication_Report_V1.0.md`,
`docs/implementation/AMSDP_Windows_Ubuntu_Development_and_Deployment_Runbook_V1.0.md`; untracked
`docs/plan/`, the specification, the gap audit, the state report, this report and two earlier
reconciliation reports. **Nothing staged, nothing committed.**

---

## 10. Recommended next engineering task

**MP-01, redefined — "prove the runtime, never re-apply the migration" — on the Ubuntu host, with the
Product Owner's authorisation.**

Concretely, in this order:

```bash
docker compose exec db psql -U amsdp -d amsdp -c "select version_num from alembic_version;"
#   expect c4d8e2a91f60 → nothing to apply; if it differs → _tools/pg_backup.sh first, then upgrade
docker compose exec db psql -U amsdp -d amsdp -c \
  "select to_regclass('voice_packs'), to_regclass('queue_announcement_deliveries'), to_regclass('announcement_platform_config');"
docker compose ps
for p in 8110 8111 8112 8113 8114 8115 8116 8117; do curl -fsS http://192.168.68.108:$p/health; echo; done
```

Then **MP-02** — the whole-tree suite against the migrated database — because that is the only item
that converts the `109 errors` from a prediction into a closed result.

**Can MP-01 begin on this baseline?** **Yes.** The baseline is internally consistent, the revision
graph is single-headed and verified, the deployment is confirmed reachable and running the post-merge
code, and the one unverified fact (the database revision) is exactly what MP-01's first command
establishes. The single condition is that MP-01 is executed as a **verification** with a conditional
upgrade, never as an unconditional migration — the recipe in the plan, the runbook and this report all
now say so.

**Not part of MP-01, but not to be lost:** the `0.0.0.0:5433` exposure (owner decision), the
`amsdp_demo` database (still at `a9c4e1f7b2d8` unless separately migrated), and the open items in §8.

---

## 11. Governance and skill compliance

| Requirement (`.clinerules`) | Compliance |
|---|---|
| §2 automatic routing | Domains: documentation governance, deployment/infrastructure, database migration, audit. Row-selected documents read: `saas-cicd-workflow.md` (adapted: git safety, honest CI state), `saas-multitenant-data.md` §4–5 (migration chain, idempotency), Business Rules Part X (audit), the docs index |
| §3 non-negotiables | No secret exposed (`.env.local` keys only); no capability claimed that was not verified; denials none to record; no schema change; audit trail untouched |
| §4 routing table | Deployment row and database-migration row applied; **no skill is installed** in this workspace, so governance documents were used and that fact is stated here rather than a skill being invented |
| §6 compliance reporting | This section |
| §7 evidence standard | Every claim carries one of VERIFIED / REPORTED / HISTORICAL / PREDICTED / NOT VERIFIED in §5; the migration itself stays **REPORTED**, never upgraded to VERIFIED |
| §9 execution boundaries | Read-only commands only; no suite, migration, container, server or destructive git command; outputs kept short |
| §11 document placement | This report is in `docs/implementation/`; amendments were made inside the documents they correct; **no new folder**; **no file deleted or migrated**, so no manifest entry is required |
| §12 documentation reading and index currency | Index read first; every cited document was opened in this session; the index was updated in the same task |

**Skills unavailable / not applicable:** no formal skill package exists in this workspace (verified in
earlier sessions and unchanged). Nothing was pretended.

---

## 12. Evidence limitations — what a reader must not over-credit

1. **The live database revision is reported, not measured here.** The authoritative record is the
   verified deployment record of 2026-11-23. This report says so in §5 rather than implying a fresh SQL read.
2. **The three tables were not queried.** Table presence is reported, not verified. The deployed-route evidence shows the *code* that uses them is live; it does not show the *tables*.
3. **Health endpoints are liveness only.** `{"status":"ok","service":"…"}` proves a process answers; it proves nothing about the schema.
4. **No suite was run.** The `790/1`, `682/109` and `109` figures are historical counts quoted as such. The prediction that the 109 clear on the migrated database is a prediction (it is however strongly entailed: they were `UndefinedTable: voice_packs`, and the migration creates that table).
5. **The seeded counts are rehearsal evidence.** They demonstrate the rehearsal preserved data; they are not a live row count taken in this task.
6. **One write path was deliberately not taken.** No authenticated request was made, because obtaining a token needs a `POST /api/v1/staff/login` that writes a login-attempt row. A stronger verification was possible and was not taken, because the task forbids writing to production.
7. **`amsdp_demo` is out of scope.** Nothing here establishes its revision.

---

## 13. Document control

| Field | Value |
|---|---|
| Report | AMSDP Live Deployment Baseline Reconciliation, V1.0 |
| Date | 2026-11-24 |
| Task type | Read-only verification plus documentation reconciliation |
| Authorisation | The task brief; documentation-only |
| Amends | Audit §16 (Amendment A-3); plan Appendix E (Amendment A-2); in-place corrections to the runbook, the merge publication report and the implementation-state report |
| Supersedes | The "live database two migration stages behind" baseline wherever it is operative. The historical statements themselves are **retained**, dated, not deleted |
| Does **not** supersede | Any Product Owner decision, any BR clause, any approved scope, the `0.0.0.0:5433` finding, or any open item in §8 |
| Next action | **MP-01** as redefined (§10), then **MP-02** |
| Status | **Complete** for the documentation reconciliation; one verification gap (live schema read) is deliberately carried to MP-01 |

*End of report.*