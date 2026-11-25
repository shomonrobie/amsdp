# AMSDP — B-4 database access: technical decision brief

> **Task ID:** `AMSDP-B4-DATABASE-ACCESS-BRIEF-2026-11-25`
> **Version:** 1.0 · **Date:** 25 November 2026
> **For:** Product Owner
> **Status:** Awaits one decision. Nothing in this brief was executed against the
> owner's host or database.

---

## 1. The decision being asked for

**B-4** is the outstanding choice of *how* the implementation agent may reach the
PostgreSQL database on the Product Owner's Ubuntu machine. The owner has
confirmed the database exists and is hosted there; the access **method** has not
been selected. This brief states exactly what would be read, what would be
changed (nothing, for the first two reads), the three safe options, and what each
one unblocks.

**What is *not* being requested:** exposing PostgreSQL to the internet, changing
`pg_hba.conf`, changing the bind address or the firewall, opening SSH, or putting
a credential into the repository.

---

## 2. Why the remaining work needs it

Every remaining task falls into one of two classes.

**Class 1 — needs a *read* of the live database (no writes).**

| Task | What is missing | Why a local run cannot substitute |
|---|---|---|
| **MP-01** runtime proof | `select version_num from alembic_version;` plus three `to_regclass()` reads and the compose service list | The deployment's schema revision is the last unproven fact about the running system; `/health` is a static body and does not report it |
| **MP-02** post-migration baseline | confirmation that the suite's expectations hold **on the migrated deployment schema** | The local database and the deployment run different revisions until the MP-35 revision is applied there |
| **MP-03** QUE-006 audible closure | one `queue_announcement_deliveries` row and one audit row after a real `call` | A human must also hear the audio (B-8), but the rows prove the pipeline |
| **MP-25 / MP-30** | tracking and handoff surfaces exercised against real data | Contract-level verification against the deployed service |
| **MP-40** multi-display demonstration | two displays served from the deployed stack, six simulated pollers from one address | AC-12's six-screen case is a property of the deployed limiter and cache, not of `TestClient` |

**Class 2 — needs a *write* to the deployment (a schema change).**

The multi-display registry now exists as revision `d3f5a7b91c24` and is applied to
the local development database. Serving a configured display on the owner's
deployment requires the same forward-only migration there:
`alembic upgrade head` inside an authorised maintenance window, **after** a
backup, with `alembic current` read first. This is the only write this programme
needs, it is additive-only (`CREATE TABLE` ×2, `CREATE INDEX` ×3), and it is
**not** covered by the B-4 read decision — it needs a separate go-ahead.


---

## 3. What a read would consist of

Three read-only statements and one listing. Nothing else.

```sql
select version_num from alembic_version;
select to_regclass('voice_packs'), to_regclass('queue_announcement_deliveries'),
       to_regclass('announcement_platform_config');
select count(*) from queue_announcement_deliveries;   -- MP-03 baseline only
```

```bash
docker compose ps        # which services are up, and their health
```

No table is written, no row is updated, no setting is changed, no backup is
needed for a read, and the outputs contain no patient data — a revision
identifier, three table names and a count.

---

## 4. The three safe options, in order of least exposure

| Option | What the owner does | What the agent gets | Exposure created | Notes |
|---|---|---|---|---|
| **A — owner-run, agent reads the output** *(recommended)* | runs the four commands above in their own terminal and pastes the output into the chat | the exact strings MP-01 requires | **none** — no new listener, no credential, no tunnel | Slowest to iterate (a round trip per read), but it satisfies MP-01/MP-02's acceptance cells *exactly*, because the criterion is a quoted read, not a live connection |
| **B — read-only role over an SSH tunnel** | creates a `SELECT`-only role (`amsdp_readonly`) and runs `ssh -L 55432:127.0.0.1:5432 <host>` from a machine the agent can reach | a live read-only connection for repeated queries | a new database role and an SSH session; **no** public port, and no `pg_hba.conf` change beyond the loopback entry a tunnel already uses | Best balance for MP-02/MP-03/MP-40, where several reads and drills are needed. The role cannot write even if misused |
| **C — attach to the existing exposure** | supplies a connection string for the already-published `:5433` | a live connection | **none new** — but it uses an exposure this programme has already recorded as an **open security risk** (Appendix E.6 of the plan) | Not recommended. It is listed because it is the cheapest for the owner, and the honest answer is that it is also the one that leaves a known risk in place |

**Option A is sufficient for MP-01 and MP-02.** It is not sufficient for MP-40,
whose six-screen load case must be generated *against* the running deployment for
ten minutes; that needs option B, or the owner running the load script themselves
and pasting the summary.

---

## 5. What is blocked while B-4 is open

| Task | Blocked on |
|---|---|
| **MP-01** | the read in §3 |
| **MP-02** (deployment half) | MP-01 |
| **MP-03** | MP-01 + a human to confirm audibility (B-8) |
| **MP-25, MP-30** | a deployed read of the tracking and handoff surfaces |
| **MP-40** | MP-38, MP-39, the demo seed **and** the deployed stack, including the load case |
| **MP-31, MP-32** (the MVP §12 run and the rehearsal) | the live stack |

**Not blocked, and continuing:** repository work, local-development work, test
suites, migrations on the local development database, and every documentation
obligation. That is why the multi-display public surface was delivered without
B-4.

---

## 6. Whether a production change is necessary

- **For the read: no.** Options A and B change nothing on the deployment except,
  in B, an added read-only role.
- **For multi-display on the deployment: yes, one additive migration.** It needs
  its own authorisation, a backup, `alembic current` read first, and a
  maintenance window. It cannot lose data — it creates two new tables and three
  indexes and touches nothing that exists — but "cannot lose data" is not the same
  as "does not need a window".
- **Never:** a reseed, a restore, a `pg_hba.conf` edit, a bind-address change, or
  a credential in the repository. **B-1** (destructive reseed) remains withheld.

---

## 7. The single question this brief asks

> Which access method does the Product Owner authorise — **A** (owner-run reads
> pasted into the chat), **B** (read-only role over a tunnel), or **C** (the
> existing `:5433` exposure)?

Choosing **A** closes MP-01 and MP-02 today. Choosing **B** additionally enables
MP-03 and the MP-40 load case. Whichever is chosen, the migration authorisation in
§6 remains a separate, explicit go-ahead.
