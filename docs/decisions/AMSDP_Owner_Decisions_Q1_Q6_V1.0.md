# AMSDP — Owner Decisions Q-1 … Q-6

> **Document ID:** `AMSDP_Owner_Decisions_Q1_Q6`
> **Version:** V1.0 · **Date:** 2026-11-13
> **Decisions taken by:** Product Owner, 2026-11-12
> **Raised in:** `docs/audit/AMSDP_Project_Context_Report_V1.0.md` §11 (owner questions Q-1 … Q-6)
> **Status of this document:** decision record only — **what was decided and why**.
> Implementation status, evidence and open items are deliberately kept out of it and
> live in `docs/implementation/AMSDP_Owner_Decisions_Implementation_Report_V1.0.md`.

---

## How to read this document

Each record states the question that was put to the owner, the decision that was
approved, the boundary of that approval, and what the decision forces on the
codebase. The boundary matters as much as the decision: an approval for one
corrective change is not an approval for the neighbouring feature, and several of
these questions sit directly against `.clinerules` §3 non-negotiables.

**Precedence.** These records sit under `.clinerules` §1 level 2 (explicit
project-owner instructions and approved AMSDP business rules). They do not
override the Business Rules, the frozen system design, or §3 non-negotiables. If a
record appears to conflict with one of those, the conflict is reported rather than
resolved silently.

**Attribution.** The decision text below is the record kept by the implementing
agent of the owner's approved answers; the questions themselves are quoted from
the context report §11. Where a record needed a precise engineering word (status
code, capability name, file path) the wording is stated explicitly here so the
code can be held against it.

---

## Q-1 — Platform administration boundary

**Question (context report §11).** `super_admin` holds the bare wildcard `"*"`,
so the platform administrator is granted every permission string the codebase can
ever pass to the checker, including ones that do not exist. Is that the intended
authority of the platform role?

**Decision.** Replace the wildcard with an explicit, reviewable set of platform
administration capabilities. Platform-level administration, authorized
cross-organization support access, and platform operational support are approved.
Do **not** expand the platform role's permissions beyond that approved purpose, and
do **not** leave an unrestricted wildcard in place.

**Boundary of the approval.**
- In scope: the permission matrix entry for the platform role, the shared
  authorization helpers, and the audit of platform-administrator access to
  another organization's data.
- Out of scope: new platform features, changes to any tenant role's
  capabilities, a new administrative UI, and any change to the business rules.
- The tenant roles (`org_admin`, `branch_admin`, `receptionist`, `doctor`,
  `assistant`) keep exactly the capabilities the Business Rules give them.

**What the decision forces.** The platform capability must be an enumerable,
testable object rather than a role-string bypass; cross-organization access must
still fail closed for every tenant role (§3: non-disclosing 404, never 403); and
platform access to a tenant's data must be recorded in the audit trail.

**Why it matters.** A wildcard cannot be reviewed, cannot be tested for
over-grant, and silently becomes larger every time a new permission string is
introduced. An enumerated list is a security control; a wildcard is an absence of
one.

---

## Q-2 — Denial auditing

**Question (context report §11).** The audit trail records what was *allowed*.
A refused request (403/404/422) leaves no trace at all. Should denials be
recorded, and on what terms?

**Decision.** Yes — denials are audited, in the shared audit subsystem, for
403 (forbidden), 404 (non-disclosing tenant boundary) and 422 (rejected request).
The recording must satisfy all of the following, each of which is a condition of
the approval rather than a suggestion:

1. no sensitive data (no credentials, tokens, passwords or personal data);
2. no disclosure of cross-tenant existence — the audit behaviour must not turn a
   non-disclosing 404 into an oracle;
3. no duplicate audit events for a single denial;
4. correlation/request identifiers preserved when available;
5. the response to the caller is unchanged in status and body;
6. a failure in the audit path must never turn a denial into a success;
7. tests cover the behaviour;
8. a status code that is **deliberately** not audited may be excluded **only** if
   the reason is documented.

**Boundary of the approval.**
- In scope: a shared recording mechanism covering every backend service, and the
  tests for it.
- Out of scope: new security features, changes to authorization outcomes, any
  change to the append-only guarantee of the trail, and any new transport or
  external log sink.
- The tenant column stays `organization_id` — no second tenant key is introduced.

**What the decision forces.** Exactly one recording site per denial; attribution
only from a *verified* identity; redaction of token-bearing paths; and an
explicit, written reason for anything left unaudited.

---

## Q-3 — Notification worker

**Question (context report §11).** `backend/common/notifications/worker.py` exists
but is not a service in `docker-compose.yml`, so notifications are not delivered
by the stack. Should the worker be wired into the stack, or accepted as it is?

**Decision.** Accept the worker as currently implemented. It is **not** to become
a compose service in this task. Update the relevant demo documentation to state
the manual tracking-link sharing fallback that the demo actually relies on.

**Boundary of the approval.**
- In scope: documentation of the real demo behaviour.
- Out of scope: adding a compose service, adding a real SMS/WhatsApp provider
  (still blocked on separate owner approval — the `mock` provider remains), or
  changing notification behaviour, hooks, outbox or retry logic.
- No code change to the notification subsystem is authorized by this decision.

---

## Q-4 — Limitations report accuracy

**Question (context report §11).** `docs/demo/AMSDP_Limitations_Report_V1.0.md`
states the frontend has no patient registration form. That is not accurate: staff
roles can register patients. The document understates the product.

**Decision.** Correct the inaccurate claim. Correct **only** what is inaccurate —
do not expand the document beyond what the correction requires, and do not
rewrite the document's other entries in this task.

**Boundary of the approval.**
- In scope: the specific incorrect statement(s) named in the question.
- Out of scope: a general refresh of a document that is stale in many other
  places (it still describes in-memory storage, for example). That wider refresh
  is a separate, larger decision.
- The correction must remain true of the tree it describes, and must not claim a
  capability the backend does not enforce.

---

## Q-5 — Continuous integration

**Question (context report §11).** The repository has no CI pipeline at all:
nothing runs the backend suite or builds the frontend on a change.

**Decision.** Add a GitHub Actions pipeline that runs the backend tests, builds
the frontend, and runs the existing test commands. Do **not** introduce new test
frameworks, do not restructure the repository, and do not change deployment
behaviour. If a gate cannot be executed in this environment, report that honestly
instead of claiming it passed.

**Boundary of the approval.**
- In scope: one workflow file, and the minimum test-only dependency declaration
  needed to install the suite's tooling.
- Out of scope: new test suites or frameworks, coverage gates, linters the
  project does not already run, release automation, registry publishing, and any
  change to the Dockerfiles or compose files.
- CI credentials must be ephemeral, CI-only literals; no repository, deployment
  or demo secret may be introduced, echoed or stored.

---

## Q-6 — Owner-controlled documents

**Question (context report §11).** Two Product Owner-controlled documents carry
uncommitted edits (`docs/AMSDP_Master_Feature_List_V2.0_Draft.md` +118/−11 and
`docs/architecture/AMSDP_System_Architecture_V1.0.md` +63/−11). What is to become
of them?

**Decision.** Preserve them verbatim. They are the owner's writing; they are
committed as part of the documentation commit of this task and are not edited,
reformatted, renamed, split or "tidied" by the implementing agent.

**Boundary of the approval.**
- In scope: staging and committing those two files exactly as they stand.
- Out of scope: any edit to their content, any change to their paths, and any
  judgement about whether the edits themselves are correct — that is the owner's
  review, not the agent's.
- `.clinerules` §11 continues to apply: they stay read-only for the agent.

---

## Cross-cutting conditions

These apply to all six decisions and are not separate approvals:

- `.clinerules` §3 non-negotiables are untouched: no secret is logged or exposed,
  access stays enforced server-side, cross-tenant access fails closed with 404,
  the tenant key stays `organization_id`, and the audit trail stays append-only.
- Any schema change would ship as a forward-only idempotent Alembic migration —
  none of these six decisions requires one.
- Every claim in the accompanying implementation report must meet the §7 evidence
  standard (IMPLEMENTED / TESTED / VERIFIED / ACCEPTED). A green suite is not
  VERIFIED.
- No commit made under these decisions may include unrelated work, and nothing is
  pushed without a separate owner instruction.


