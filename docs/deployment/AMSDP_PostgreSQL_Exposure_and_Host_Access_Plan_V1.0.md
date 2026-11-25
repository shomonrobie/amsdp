# AMSDP — PostgreSQL Exposure and Host Access Plan V1.0

> **Task ID:** `AMSDP-PO-DECISIONS-2026-11-25`
> **Version:** 1.0 · **Date:** 25 November 2026
> **Status:** **APPROVED APPROACH — NOT EXECUTED.** Product Owner decision **PO-10, Option A+**,
> 25 November 2026. Execution requires a planned maintenance window; no step below was run in this
> window and none may be run against the live host without one.
> **Decision record:** `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` §2.9.

---

## 1. The problem, stated exactly

| Fact | Evidence |
|---|---|
| PostgreSQL is published on **all** host interfaces: `ports: ["5433:5432"]` with no loopback prefix | `docker-compose.yml` |
| `192.168.68.108:5433` was TCP-reachable from the development workstation on 2026-11-24 | audit, plan Appendix E.6 |
| The host has **no SSH listener** (`:22` refused, twice) | same |
| No service needs the published port — services reach the database at `db:5432` over the compose network | `docker-compose.yml` service definitions |
| The missing administrative path is why **B-4** cannot close | decision pack §4.1 |

So the current state is the worst combination: clinical-operational data reachable from the LAN, and
no secure way to administer the host that holds it.

---

## 2. The approved shape of the fix (one window, in this order)

The order matters. SSH is established **first**, because it is how the database change is verified and
how B-4 is answered afterwards. Binding the database to loopback before an administrative path exists
would make the database safer and permanently unadministrable from outside the host.

| Step | Action | Why this order |
|---|---|---|
| **1** | Establish a **key-only SSH listener** for one named administrative account: password authentication off, root login off, one authorised key | This is the only way to verify step 2 and to run the B-4 read |
| **2** | **Bind PostgreSQL to loopback**: `ports: ["127.0.0.1:5433:5432"]` (or delete the mapping and administer through `docker compose exec db psql`) | Removes the exposure at zero application cost |
| **3** | Re-create the database container so the new port mapping takes effect | A compose file change alone does not change a running container |
| **4** | Verify from **both** sides (§3) | An unverified security change is not a security change |
| **5** | Run the **B-4 read** on the host (§4) and return its output | It is the whole reason the window is being scheduled |

**Constraint from the brief:** the *repository* change for step 2 is a one-line edit, but it is not
applied here. The running stack is deployed from a commit; changing the file without the window would
only put the tree and the deployment further out of step.

---

## 3. Verification — what "done" looks like

| Check | Pass condition |
|---|---|
| LAN exposure removed | From the workstation, a TCP connect to `192.168.68.108:5433` **fails** |
| Application unaffected | All services healthy; a queue list, an appointment read and a dashboard tile answer normally |
| Database still administrable | On the host, `docker compose exec db psql -U <user> -d <db>` works |
| SSH is key-only | Password login is **refused**; key login works; root login is refused |
| No lock-out | The SSH session used to make the change stays open until the new session is proven |

**Rollback.** Revert the `ports:` line and `docker compose up -d db`; restore `sshd_config` from the
backup taken before editing it and reload the service. Both are single-file reversions, which is why
they are done in one window with the previous configuration retained until the new one is proven.

---

## 4. The B-4 read (run on the host, read-only, no mutation)

```sql
SELECT version_num FROM alembic_version;
```

plus the **three `to_regclass(...)` checks** quoted verbatim in
`docs/implementation/AMSDP_Product_Owner_Decision_Pack_V1.0.md` §4.1. They are not restated here so
that the two documents cannot drift apart.

**Rules for the read:**

- Read-only. No `UPDATE`, `INSERT`, `DELETE`, `ALTER`, `upgrade`, `downgrade` or reseed.
- If `version_num` **equals** the committed Alembic head, **stop** — nothing needs migrating.
- If it is **behind**, take a backup first (`pg_dump`), then `alembic upgrade head`, then re-read
  `version_num` and record both values.
- If it is **ahead** of the committed head, stop and report: the deployment is running code this tree
  does not contain.
- Paste the raw output — including an empty result — into the MP-01 verification report. An
  unrecorded read does not close B-4.

---

## 5. What this plan explicitly does not authorise

| Not authorised | Why |
|---|---|
| A live schema migration, upgrade, downgrade or reseed | **B-4** is unresolved; only the owner can authorise a mutation, and only after the read above |
| Any change to the running stack outside a maintenance window | The brief forbids disrupting live services |
| Opening a second database port, a tunnel or a VPN "just for the read" | It re-creates the exposure the window removes |
| Recording any credential, key or host secret in a document | `.clinerules` §3 |

---

## 6. Document control

| Field | Value |
|---|---|
| Authority | PO-10 Option A+, 25 November 2026 |
| Effect | Records the approved approach, its order, verification and rollback; nothing was executed |
| Placement | `docs/deployment/` per `.clinerules` §11 — it is a deployment procedure, not a report |
| Evidence | No step in this document is `VERIFIED`; the exposure is still open as of 25 November 2026 |

*End of plan.*
