---
name: saas-cicd-workflow
description: CI/CD, migration-release and Git rules for CarbonTally. Use when adding or changing a GitHub workflow, a release gate, a migration apply step, a rollback, or anything that touches main/dev_v2, secrets scanning or the migration drift gate. The repository has two workflows today — do not describe a pipeline that does not exist.
---

# CI/CD — Gates, Migration Release, Git Safety

**Tier 2.** Defers to [carbontally-agent-governance.md](carbontally-agent-governance.md).

## 1. When to activate

Any change under `.github/workflows/`, any release/migration apply plan, any rollback, any
branch-protection claim, or any statement about what CI verifies.

## 2. Current state — state it accurately

- **Two workflows exist:** `migration-drift.yml` and `tracked-secrets.yml`.
- **No workflow runs** lint, type checks, unit tests or E2E. `mypy` is configured and not in CI.
- Both trigger on `main`/`master` (and `p8-release-*`), **not** on the active `dev_v2` branch.
- Do not write or imply "CI will catch it". If you need a gate, add it deliberately and say so.

## 3. The migration drift gate is the important control

- The chain is pinned by **count, tip and content fingerprint**
  (`e2e/environment/scripts/canonical_schema_verify.py`, `backend/tools/migration_drift.py`).
- Moving a pin is an **authorised, measured act** — never a test fix, never a guess. Re-measure
  with the recorded recipe; do not normalise a value to make a run pass.
- The gate refuses a production-looking DSN and requires explicit authorisation for a production
  apply. **CI must never apply a migration to production.**
- A migration that cannot be reversed must say so; do not pretend a down-migration exists.

## 4. Secrets

- `tracked-secrets.yml` scans **git objects** (not just the worktree) against a
  `(rule, path, sha256-of-value)` baseline, and has its own tests. It is stronger than a
  worktree grep — use it, do not reimplement it.
- Never commit `.env` files, credentials, API keys, tokens, signed URLs or generated secrets.
- If a secret reaches history, that is an incident: rotate first, then clean.

## 5. Branch and rollback discipline

- Work proceeds on feature/release branches and lands on `dev_v2`. Do not assume a PR-only
  model, and do not claim branch protection you have not observed.
- **Rollback is `git revert`.** Never force-push, never rebase shared history, never
  `git reset --hard` over other agents' work.
- Every workflow that matters uploads an evidence artefact (90-day retention); a report cites
  the run, not the intention.

## 6. Adding a gate

If you add a workflow, state in the report: what it runs, on which branches, what makes it
fail, and what evidence it keeps. A gate that cannot fail is decoration.

## 7. Anti-patterns

- **The Imaginary Pipeline** — documenting lint/typecheck/E2E as if they run.
- **The Auto-Deploy Migration** — applying SQL to production on merge.
- **The Force-Push Fix** — rewriting history to hide a bad commit.
- **The Green Build** — "CI passed" when only the secret scan ran.
- **The Guessed Pin** — changing a fingerprint without a measurement.

## 8. Self-check

- [ ] Did I claim a CI capability that does not exist?
- [ ] Does my change move a migration pin? Was it measured, and is it deliberate?
- [ ] Does anything apply to production from CI? (it must not)
- [ ] Does the rollback use revert rather than history rewriting?
- [ ] Did I touch secrets, and are they absent from the diff?
- [ ] If I added a gate, can it actually fail?
