# AMSDP — MP-46 Denial-Record Capability Field — Product Owner Decision Request — V1.0

| | |
|---|---|
| **Document** | `docs/decisions/AMSDP_MP-46_Denial_Capability_Decision_Request_V1.0.md` |
| **Question owner** | Product Owner |
| **Raised by** | Independent audit of the 27 November 2026 backend execution (finding **F-02**) |
| **Work package affected** | **MP-46** — read-only enforcement and denial accounting |
| **Status if unanswered** | MP-46 stays **TESTED**; it is **not** VERIFIED and **not** ACCEPTED |
| **Status after the answer** | **ANSWERED — Option A approved** (Product Owner, 2026-11-27; recorded in **§11**). MP-46 stays **TESTED** until its remaining verification and acceptance requirements are independently satisfied; it is still **not** VERIFIED and **not** ACCEPTED |
| **Nothing is implemented by this brief** | No code, test, model, migration or specification was changed to produce it |

---

## 1. The question, in one paragraph

The approved requirement **MD-19** says an authenticated display-management denial is audited with
“actor, **capability**, org/branch”. The shipped `queue.display.denied` row records the actor, the actor
role, the organisation, the branch, the target display, the HTTP status, the facility code and the
reason — but **no capability identifier**. The specification's own acceptance criterion for this area,
**AC-21**, counts rows and does not enumerate fields, so the suite is green without ever asserting the
capability. The Product Owner must say which of these is authoritative: **does MD-19 require the
capability identifier to be persisted, or is “capability” a description of what the denial is *about*
rather than a stored field?**

**Decision required:** Option **A** (persist it), **B** (record that role/action is sufficient), or
**C** (defer with a recorded deviation). §7 states each option's consequences; §8 states what happens if
the question is left open.

---

## 2. What the approved specification actually says

### 2.1 MD-19 — requirement (specification Appendix E.3, line 479, verbatim)

> **MD-19** | **Denials are recorded, not silently swallowed — without creating an oracle or an
> amplification path.** Authenticated display-management denials are audited (`queue.display.denied`:
> actor, capability, org/branch). An anonymous request for a **disabled** display raises one
> `queue.display.disabled_requested` event per display per 5 minutes (throttled, no client IP stored).
> Unknown-code probes are counted by the limiter only and are **not** audited: an unauthenticated public
> probe must not be able to write unbounded rows into an append-only audit trail.

Its stated verification, immediately beside the requirement text:

> One denial of each class produces exactly one audit row (or the documented throttle); 100 anonymous
> unknown-code probes produce **zero** audit rows and only limiter state

**This is the crux:** the requirement's prose names `capability`, and the requirement's own verification
column — like AC-21 — tests **row counts**, not fields.

### 2.2 AC-21 — acceptance criterion (specification line 521, verbatim)

> **AC-21** | An authenticated cross-branch display write produces one `queue.display.denied` row; a
> disabled display requested repeatedly produces at most one `queue.display.disabled_requested` row per
> 5 minutes; 100 unknown-code probes add **no** audit rows | Audit-table counts before and after, quoted

### 2.3 MP-46's acceptance criteria in the master plan (line 566, verbatim)

> Four verb probes return `405`; no cookie is set; one denial = one row; 100 unknown-code probes add zero
> audit rows (spec AC-20, AC-21)

### 2.4 Provenance and approval

| Item | Position |
|---|---|
| Origin | **PO-13**, decided and approved by the Product Owner on **2026-11-24**; MD-13…MD-19 and AC-15…AC-22 were added to the specification as Appendix **E** (Amendment A-1) |
| Approval of the wording | The Appendix was registered as approved-scope requirement text (`docs/implementation/AMSDP_PO13_Multi_Display_DQDS_Reconciliation_Report_V1.0.md`, line 41) |
| Later amendment to MD-19 | **None found.** No Product Owner decision, addendum or plan amendment located in this phase narrows or removes the `capability` word |
| Traceability | MD-18/MD-19 → MP-46 (plan line 418); MP-46 → AC-20/AC-21 (plan line 566) |

So the field list in MD-19 is **approved text**, and nothing found later replaced it. That is why this
cannot be resolved by an agent reading the documents: the words are approved, and they disagree with what
the approved acceptance criterion measures.

---

## 3. What the implementation does

`backend/queuing/displays.py:115–142` — one helper writes the denial row **before** the refusal, then
raises with a marker header so the shared middleware does not add a second generic row:

```python
record_audit(session, service=SERVICE, org_id=auth.organization_id,
             branch_id=branch_id or auth.branch_id or None,
             action=DENIED_ACTION,
             target_type="queue_display",
             target_id=(display.id if display is not None else ""),
             actor_id=auth.user_id, actor_role=auth.role,
             after={"status": status_code,
                    "code": (display.code if display is not None else ""),
                    "request": detail},
             reason=reason)
```

| MD-19 element | Recorded? | Where |
|---|---|---|
| actor | **yes** | `actor_id` (`auth.user_id`) |
| capability | **no** | nothing in `after`, nothing in the row |
| org | **yes** | `organization_id` (`auth.organization_id`) |
| branch | **yes** | `branch_id` |
| — (also present) | yes | `actor_role`, `action = "queue.display.denied"`, `target_type`, `target_id`, `after.status`, `after.code`, `after.request`, `reason` |

Two call sites exist, both in the same module: `displays.py:149` (403, insufficient permissions) and
`displays.py:415` (404, display not found). The capability identifier MD-19 asks for is **already in
scope at both sites**: `DISPLAY_MANAGE = "queue.display.manage"` (`displays.py:58`) is the very string
`_require_manage` passes to `check_granted` a few lines earlier. Nothing has to be looked up.

**Test coverage of the field: none.** A search for `capability` across
`backend/tests/test_display_admin.py`, `backend/tests/test_denial_audit.py` and
`backend/tests/test_multidisplay.py` returns **zero** matches. No test asserts the field, so no test
fails, so the suite's green state carries no opinion about this question.

---

## 4. Where the discrepancy actually lies

Three readings are defensible from the documents alone, and only the Product Owner can choose:

| Reading | Basis | Consequence |
|---|---|---|
| **R-1 — the field is required.** “`queue.display.denied`: actor, capability, org/branch” is a list of what the row must contain | MD-19's prose, approved 2026-11-24 | MP-46 is **incomplete** against MD-19; the row is missing an approved element |
| **R-2 — the list is descriptive.** It says *what the denial is about* (an actor exercising, or failing to exercise, a capability) rather than mandating a stored field | MD-19's own verification column and AC-21 both test row counts and identity, never fields | MP-46 **meets** MD-19; no change needed; the requirement text should be annotated for clarity |
| **R-3 — the documents measure different things.** MD-19 is a requirement, AC-21 an acceptance criterion, and the criterion is weaker | Standard requirement/criterion asymmetry | MP-46 can be **ACCEPTED against AC-21** while remaining **non-conformant with MD-19**, i.e. accepted with a declared, recorded gap |

R-3 is the honest description of today's state; it is not a resolution. Note the asymmetry's direction:
a requirement is normally the stronger document, so accepting against the weaker criterion silently
narrows approved scope — which an agent must not do (`.clinerules` §1: never silently override approved
business rules).

---

## 5. Would this need a schema change?

**No, under the reading that satisfies MD-19 with the existing table.** `audit_events.after` is a `JSON`
column (`backend/common/models.py`, `class AuditEvent`), and the codebase already puts request-scoped
detail there: `common/denial_audit.py::denial_record()` stores `request_id` inside `after` rather than in
a column. Adding `"capability": DISPLAY_MANAGE` to the `after` dict is a payload change, not a schema
change — **no Alembic revision, no migration, no model change.**

| Implementation shape | Schema change? | Notes |
|---|---|---|
| `after["capability"]` (JSON) | **No** | Matches the existing precedent (`status`, `code`, `request`, `request_id` all live there); queryable with PostgreSQL JSON operators, not indexed |
| A dedicated `capability` column on `audit_events` | **Yes** | A forward-only, idempotent migration plus a model change; touches the shared audit table used by every service — wide blast radius for one field |
| A capability column on a display-specific audit table | **Yes, and a new table** | Not justified by the requirement |

The JSON route is the proportionate one **if** the Product Owner chooses Option A. That is a
recommendation about implementation shape only; it does not decide whether to implement.

---

## 6. If Option A were chosen, what would change

Recorded for decision-making — **not authorised and not performed**:

1. `backend/queuing/displays.py` — pass the capability into `_denied()` (a parameter defaulting to
   `DISPLAY_MANAGE`, or supplied at each call site) and add `"capability": …` to the `after` dict. Two
   call sites.
2. `backend/tests/test_display_admin.py` — one assertion that the written row's `after["capability"]`
   equals `queue.display.manage`, on both the 403 and the 404 path (the existing MP-46 tests already read
   the audit row, so this extends them rather than adding a module).
3. Nothing else: no model change, no migration, no new dependency, no change to the throttle, and no
   change to the middleware's generic `request.denied` path (which has no capability concept — it is
   shared by every service).
4. A re-run of `backend/tests/test_display_admin.py` and `backend/tests/test_denial_audit.py` would be
   required to carry the claim past TESTED, and a full-suite run to keep the 1,061 figure honest.

Estimated effect: **small** — two call sites, one payload key, two assertions. It is not done because of
authority, not effort.

---

## 7. Options

| Option | What the Product Owner would be deciding | Consequence |
|---|---|---|
| **A — persist the capability** *(recommended)* | MD-19 stands as written; the row gains `after.capability` | MP-46 returns to incomplete-against-MD-19 until a two-line change and its assertions land; no migration; MP-46 then conforms to MD-19 **and** AC-21 |
| **B — role/action is sufficient** | MD-19's list is descriptive; `actor_role` + `action = queue.display.denied` + `after.code`/`request` identify the capability context | Requires an **explicit amendment note** against MD-19 so approved text and implementation agree; MP-46 may then be assessed against AC-21 without a declared gap |
| **C — defer with a recorded deviation** | MD-19 stands as written, and MP-46 does not yet satisfy it | MP-46 can stay TESTED but must carry a **declared deviation**; it cannot be presented as conformant with MD-19 |

**Recommendation: A**, for three reasons. The word is in approved requirement text and nothing later
removed it; the identifier is already in scope at both call sites, so the change is two lines plus
assertions; and no schema change is needed, so the cost of conforming is lower than the cost of carrying
an amendment to approved scope. **The recommendation is advisory — the decision is the Product Owner's,
and no part of Option A has been performed.**

---

## 8. What happens if the question stays open

- **MP-46 remains TESTED.** It is not VERIFIED (no browser or live-API evidence) and not ACCEPTED (a
  Product Owner decision that has not been asked for, let alone given).
- **AC-21 is satisfied as written** — one row per denial is proven, the throttle is proven, and the
  100-probe zero-row rule is proven (`backend/tests/test_multidisplay.py`,
  `test_a_disabled_display_404s_identically_and_is_audited_once` and `test_unknown_codes_write_no_audit_rows`).
- **MD-19 is partially satisfied**: the denial classes and the throttle conform; the field list does not.
- **Acceptance risk:** if MP-46 is later accepted without a recorded position on this point, the project
  will have accepted a work package against the weaker of two approved documents without saying so. That
  is the specific outcome this brief exists to prevent.
- **No register status changes.** `docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §15.4 keeps
  MP-46 at “IMPLEMENTED · backend TESTED”.

---

## 9. Authority boundary observed by this brief

Not performed, and not authorised by the audit-resolution mandate: modifying MD-19 or AC-21; declaring
role equivalent to capability; modifying `_denied()`; modifying `audit_events`; creating a migration;
modifying any test; moving MP-46 to VERIFIED or ACCEPTED. This brief asks; it does not act.

---

## 10. Response line (copy, edit, return)

```
F-02 / MP-46 capability field: Option (A / B / C) — <one sentence of rationale if B or C>.
```

If **B** or **C** is chosen, say whether the amendment note is appended to the specification's Appendix E
(MD-19) or recorded only in the work-package register — the two are different records, and the choice
should be explicit.

---

<!-- Created 2026-11-27 under the audit-resolution mandate §4 (finding F-02). Decision request only:
     nothing in this document changes code, tests, schema, specification or any work-package status. -->

---

## 11. Product Owner answer — PO-DEC-01 (recorded 2026-11-27)

| | |
|---|---|
| **Question** | Does **MD-19** require the capability identifier to be **persisted**, or is "capability" a description of what the denial is about rather than a stored field? (§1–§2) |
| **Answer** | **Option A — persist the capability field.** "The MD-19 capability field is required. The recorded implementation of `after.capability = "queue.display.manage"` on both denial paths is approved. No further specification amendment or code change is required for this decision." |
| **Recorded as** | **PO-DEC-01**, Product Owner response to the consolidated decision pack, 2026-11-27 |
| **Recorded here by** | The agent, appending this section only, under Product Owner authorisation **OA-2** (documentation-only). **§1–§10 stand exactly as asked**; the question above them is preserved |
| **Effect on MP-46** | None on its status. MP-46 remains **TESTED** — the answer resolves the *specification question*, it is not independent evidence and not an acceptance signature (`.clinerules` §7) |
| **Effect on MD-19** | **None.** The field is ratified as already implemented. No amendment, no deviation row, no Appendix E edit |
| **Effect on code, tests, schema, deployment** | **None.** No file under `backend/` or `frontend/`, no test, no migration, no configuration, no database was touched to record this answer (OA-2 scope) |

### 11.1 What Option A settles

1. `after.capability = "queue.display.manage"` is the **approved** record content on **both** denial paths — the
   authenticated **403** path and the non-disclosing **404** path — as implemented in
   `backend/queuing/displays.py::_denied()`.
2. "Capability" in MD-19 is a **stored field**, not a description of the denial's subject. **Option B is not
   adopted**, so the recorded role/action pair is not declared sufficient in the field's place.
3. **Option C is not adopted.** No deviation is recorded against MD-19, and no deferral row is opened.

### 11.2 What it does not settle, and must not be read as settling

1. **Caller versus target branch on the 404 path (RO-08 / OPC-3).** The Product Owner agreed that the
   **caller's** organisation and branch are recorded and the **target** is identified through `target_id` —
   consistent with the current interpretation. That is a **documented interpretation**, not an MD-19
   amendment: MD-19 still does not distinguish caller from target branch. Recorded in register §17.3.
2. **Independence of the evidence.** The implementation was **read**, not re-executed. Nothing in this answer is
   a new execution, so no status moves under `.clinerules` §7.
3. **The pre-answer sequence.** The capability field reached `_denied()` during the 27 November second window,
   **before any answer existed**, while the implementation report's §4.1/§9 recorded that no Product Owner
   decision was required — an agent reconciliation, not an owner decision. Option A ratifies the **content**
   that resulted; it does not convert the earlier sequence into an authorised act. The sequence is preserved,
   not erased, as **RO-02** in `docs/audit/AMSDP_Reconciliation_Findings_RO-01_to_RO-10_V1.0.md` and in
   register §17.1.
4. **Acceptance.** `AC-21` still counts rows and still does not enumerate fields. Whether a field-enumerating
   assertion is added is a test-scope question that **OA-2 did not authorise** and that no decision here
   answers. It is raised as an open item in register §17.5.

**Trail.** Register **§17** (PO-DEC-01 record, corrections, corrected tally); Docs Index **Revision 57**;
`docs/audit/AMSDP_Backend_Execution_Audit_27Nov2026_V1.0.md` post-audit annotation;
`docs/implementation/AMSDP_MP-46_MP-38_Compliance_Implementation_Report_V1.0.md` §13.

<!-- §11 appended 2026-11-27 under Product Owner authorisation OA-2. §1–§10 and the header table above
     were not rewritten; one status row was added to the header table so the answer is visible on arrival. -->
