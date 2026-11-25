# AMSDP — MP-33 Report: CI first green run, and what is actually red

**Status:** DONE — the CI state is now *observed and recorded* (not claimed): a green run exists and is linked; the
current tip is red for one named reason. No green run is claimed for the current tree.
**Written:** 24 November 2026, Windows development checkout (`E:\amsdp`).
**Task source:** `docs/plan/AMSDP_Master_Implementation_Plan_and_Roadmap_V1.1.md` §6 WP-I, MP-33 (P2, depends on
MP-02).
**Register:** `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §2 (row MP-33), §4 (Q-3, now diagnosed).

---

## 1. The criterion, and how it was read

Plan wording: *"**CI first green run**, or an explicit statement that it cannot be executed in this environment.
Deliverable: a green run URL/log, or a recorded BLOCKED with the reason — never a claim."*

The trap the criterion is written against is a report saying "CI is green" because nothing ever checked. So this task
answers three questions with artefacts: **does a pipeline exist, has it ever been green, and what is the state of the
current tip?** The third answer is not green, and that is recorded as it is.

---

## 2. What the pipeline is

`.github/workflows/ci.yml` (owner decision Q-5, 2026-11-12), two independent jobs:

| Job | Runtime | Steps |
|---|---|---|
| `backend` — "Backend — pytest on PostgreSQL 16" | Python 3.13 + `postgres:16-alpine` service on port 5433 | install the requirements union → `alembic upgrade head` → `python -m pytest -q` |
| `frontend` — "Frontend — build and unit tests" | Node 22 + `npm ci` | `npm run build` → `npm test` |

Triggers: push to `main` and `hackathon-mvp`, every pull request, and `workflow_dispatch`. Timeouts 25 and 15 minutes.
The remote is `https://github.com/shomonrobie/amsdp` and it is public, which is what made the state observable from
this host at all (see §3).

---

## 3. Observed state — read from the GitHub Actions API, not asserted

Queried on 2026-11-24 from this checkout (`https://api.github.com/repos/shomonrobie/amsdp/actions/runs`):

- **28 runs** of the `CI` workflow exist.
- **4 concluded `success`** (`?status=success` → `total_count: 4`). The most recent green run is **run #5,
  2026-11-14, commit `6bfbec4`** — <https://github.com/shomonrobie/amsdp/actions/runs/43613057907>. A green run
  therefore exists; it is simply not the current tip.
- The **latest run is #28**, 2026-11-23T14:21:48Z, branch `hackathon-mvp`, commit `a4ddc2c`, conclusion `failure` —
  <https://github.com/shomonrobie/amsdp/actions/runs/45193385881>. Its two jobs:

| Job | Conclusion | Detail |
|---|---|---|
| Backend — pytest on PostgreSQL 16 | **success** | all seven steps green, including `Apply migrations` (14:22:31→14:22:32) and `Run backend tests` (14:22:32→14:29:42, ~7 min) |
| Frontend — build and unit tests | **failure** | steps 1–5 green (`npm ci`; `Build` 14:22:07→14:22:17); **step 6 `Run frontend tests` failed**, 14:22:17→14:22:18, exit code 1 |

The failure annotation the API exposes for that job is only *"Process completed with exit code 1"* (plus a warning
that `actions/checkout@v4` and `actions/setup-node@v4` are being forced onto Node 24). The run **logs** endpoint needs
an authenticated token, which this host does not have, so the failing test *names* are not readable from here — the
one-second duration and the local reproduction in §4 are what identify them, and that identification is labelled an
inference, not a fact.

---

## 4. The local equivalents, executed today

The pipeline's own commands, run in this checkout against the fixture PostgreSQL the suite uses:

| CI step | Local equivalent | Result |
|---|---|---|
| `alembic upgrade head` | `cd backend && alembic current` / `alembic heads` | `c4d8e2a91f60 (head)` — the scratch database is already at head, single-headed |
| `python -m pytest -q` | `python -m pytest backend -q` | **847 passed, 0 failed in 1292.53s** (`runs/backend-mp10-2026-11-24.log`) — matches the CI backend job's green |
| `npm run build` | `cd frontend && npm run build` | **success** — Next.js production build, `/queue` 16.4 kB |
| `npm test` | `cd frontend && npm test` | **383 tests / 379 pass / 2 fail / 2 skipped** — the two reds are the same two Q-3 tests |

---

## 5. What the frontend red actually is (Q-3, diagnosed)

Both reds reproduce locally, in the same tree CI built:

1. `frontend/tests/banglanamesense-dataset.test.mjs` — *"dataset bytes match the hash recorded in DATASET_SOURCE"*:
   the tracked file `frontend/data/bangla_name_sense.json` hashes to
   `6f69a0ef5faf5688372a475f6f836d28d9ce9d3a1e9248b1931d463ce8257779`, while
   `frontend/lib/bangla-name-sense/dataset.js` records
   `ac037c24ebaf0208324351352bd62cedf2de16fbfde6a7d02966c55b8879e51e`. The dataset file is tracked by git
   (`git ls-files` lists it) and is not ignored, so this is a **provenance mismatch**, not a missing-file failure:
   the dataset (or the recorded constant) changed and the two were never reconciled.
2. `frontend/tests/calendar-render.test.mjs` — fails to load as a test file at all (*"'test failed'"*, 358 ms).

**Why this is reported and not fixed here.** Either the dataset was regenerated on purpose (then `DATASET_SOURCE`
must be updated **and** the provenance re-recorded) or it was corrupted (then the file must be restored). Choosing
between those two rewrites a provenance record, which is a product decision, not a test fix — updating the hash to
make the suite green would be exactly the "make it pass" anti-pattern MP-33 exists to prevent. Q-3 therefore stays
open, now with a diagnosis and two named options.

**What is still an inference.** CI's failing step is `Run frontend tests`, exiting 1 after ~1 s, and the local tree
reproduces exactly two red tests in that same command. That they are the cause is consistent and likely, but the run
log was not readable from this host, so it is recorded as an inference with its evidence, not as a verified fact.

---

## 6. Conclusion

MP-33's criterion is met in the form it allows:

- **A green run URL exists and is cited** — run #5, 2026-11-14.
- **The current tip is not green**, and the report says so, with the job, the step, the exit code and the two tests
  that reproduce the failure locally.
- **Nothing is claimed.** No statement here asserts a passing pipeline on the current tree, and the backend job's
  green belongs to a commit that predates MP-08 and MP-10 — so the current tree's CI state is *unknown until the next
  push*, which is a remote, state-changing action this agent does not take.

**What would turn the current tip green:** reconcile the BanglaNameSense dataset hash (§5, option 1 or 2) and repair
or remove `calendar-render.test.mjs`. Both are open decisions (Q-3), not implementation gaps.

---

## 7. Governance and Skill Compliance

**Domains:** deployment/CI truth (`.clinerules` §4 row "Docker, deployment, ports, infrastructure"); documentation.
**Documents read:** `docs/governance/AMSDP_Docs_Index_V1.0.md`, the master plan §6 WP-I and §7 (evidence gates), the
execution register, `.github/workflows/ci.yml`, `.clinerules`.
**Skills:** none installed (`.clinerules` §5); none claimed.
**Non-negotiables respected:** the report quotes observed values (run ids, timestamps, conclusions, hashes) instead of
inferring them; no credential was invented or echoed; the API was read unauthenticated and read-only; nothing was
pushed, triggered or re-run remotely.
**Evidence grade:** the CI state is **VERIFIED** — a second, independent artefact (the GitHub API) confirms it. The
claim "the current tip is green" is **not made**.
