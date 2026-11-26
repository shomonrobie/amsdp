# AMSDP — Product Owner Decisions, 26 November 2026 (MP-23 and MP-04) V1.0

**Status:** RECORDED — decisions taken by the Product Owner; implementation evidence is reported separately
**Written:** 26 November 2026 · **Repository:** `E:\amsdp` · **Branch:** `hackathon-mvp`
**Supersedes, for the items named below only:** PO-05 in
`docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` §2.4, and the DEFERRED/GATED status of MP-23
and MP-04 wherever it is recorded (`docs/plan/AMSDP_Work_Package_Execution_Register_V1.0.md` §11.1).

This file records decisions the Product Owner has taken. It does not re-price work, does not accept any
deliverable, and does not close any other open item.

---

## 1. Decisions recorded

| Reference | Decision | Scope of the decision |
|---|---|---|
| **MP-23** | **Option A — implement the complete approved Business Rules §43 reporting scope** | All five §43 dimensions are authorised now: appointments by day / doctor / branch, status counts, walk-ins, queue activity, utilisation. Option B (defer) and Option C (subset) are **not** taken |
| **MP-04** | **Option B — re-open and implement the complete approved administration UI scope** | W3's full operator surface: library, audition/preview, the whole lifecycle (validate, submit, approve, reject, publish, retire), platform availability release, and the organisation/platform voice configuration. Read-only or lifecycle-only variants are **not** taken |
| **PO-05** | **SUPERSEDED for MP-04** | The 25 November deferral (`PO-05: Approve Option C — defer MP-04 and MP-26`) no longer applies to MP-04. **MP-26 remains deferred** — this record does not re-open it |

Both decisions were issued as a continuation of the implementation mandate of 26 November 2026, whose §4.2
reserved *implement / narrow / defer* to the Product Owner. The agent did not choose the option; it recorded
the choice and then implemented it.

---

## 2. What each decision changes

### 2.1 MP-23 — Option A

- **Unblocked:** MP-23 moves from `DECISION REQUIRED` to implementation.
- **Unchanged:** Business Rules §43 itself. Option A implements the approved text; it does not amend it, and
  no new figure is invented. Where §43 leaves a term open ("queue activity", "utilisation"), the implementation
  publishes its definition **inside the response** so a reader can check what was counted — see §3.1.
- **Unchanged:** M-7's dependency is satisfied by MP-23's existence, not by its acceptance.
- **Not authorised by this decision:** CSV/PDF export (§43 does not ask for it), any new schema, any change to
  the dashboard.

### 2.2 MP-04 — Option B

- **Unblocked:** MP-04 moves from `DEFERRED` to implementation, with W3's API (`backend/organization/voice_packs.py`,
  `voice_pack_policy.py`, `announcement_config.py`) already in place from earlier authorised work.
- **Unchanged:** every refusal. The screen decides only *what to offer*; `voice_pack_policy.py` still decides
  what is *allowed*, and its 403/409/422 answers are displayed unchanged.
- **Unchanged:** `ALLOW_SYNTHESIS_FALLBACK = False`. The UI offers no switch for it.
- **Not authorised by this decision:** uploading a new pack from the browser (the upload route exists; a file
  picker was not part of the approved admin scope), asset deletion, or any change to the policy module.
- **Still deferred:** MP-26 (W5 installer) remains behind PO-05.

---

## 3. Definitions adopted, and why they are published rather than assumed

### 3.1 MP-23 — the two open terms

| Term | Definition implemented | Why |
|---|---|---|
| Queue activity | Entries, per-status counts, per-source counts, `calls` (entries that reached `called`), `transitions` (total recorded status transitions), `avg_wait_minutes` (created to called), `avg_service_minutes` (called to completed) | BR §43 asks for "queue activity" without naming a metric. Reporting all five keeps the answer checkable instead of asserting one |
| Utilisation | Published-capacity seats in the period, booked seats, and `percent = booked / capacity`; `UNSCHEDULED` seats counted **separately** | A percentage whose denominator is undefined must not be printed. With no published capacity the response returns `percent: null`, and unscheduled work is shown in its own field so a day can honestly exceed 100% |

`booked` in the headline block is `BOOKED + AWAITING_CONFIRMATION + CONFIRMED`, which keeps the four BR §43
headline figures disjoint; the in-facility statuses are reported separately rather than folded into one number.

### 3.2 MP-04 — what "complete administration UI scope" means

Library (both languages, every status, grouped by lifecycle bucket) · audition/preview with the server's
validation problems and its `selectable` answer · validate, submit, approve, reject, publish and retire, each
carrying its review note where the policy records one · release/withhold a published platform pack · the
organisation's language and per-language pack selection, plus the platform defaults for `super_admin` · the
configuration **in force** (resolved by the server, never recomputed in the browser).

---

## 4. What this record does not claim

1. **No acceptance.** Nothing here is `ACCEPTED`; implementation evidence is IMPLEMENTED/TESTED where it was
   observed, and `VERIFIED` is not claimed for the owner's deployment.
2. **No live change.** No migration, reseed, restart or host configuration change accompanies this record.
3. **No reopened item except MP-04.** MP-26, MP-21, MP-27, MP-11 and MP-12 keep their recorded status.
4. **No re-pricing.** Appendix A estimates are unchanged.

---

## 5. Implementation cross-reference (added 26 November 2026, second pass)

This section adds **status only**. The decisions in §1–§3 are unchanged and were not re-taken.

| Decision | Implemented | Evidence | What is still owed |
|---|---|---|---|
| **MP-23 — Option A** | The endpoint (`GET /api/v1/reports/operational`, five §43 dimensions + reconciliation) **and** the report screen the option's deliverable text names (`frontend/pages/reports.js`, `frontend/lib/operational-report.js`) | `frontend/tests/operational-report.test.mjs` **12 pass**; `npm test` **526 / 524 pass / 0 fail / 2 skipped**; `next build` exit 0 | The 16 backend tests are **NOT EXECUTED** (no PostgreSQL at `127.0.0.1:5433` on this host); no browser session, so no `VERIFIED` |
| **MP-04 — Option B** | Library, preview, validate/submit/approve/reject/publish/retire, availability release, organisation configuration, platform defaults, **rollback**, the configuration in force | `tests/voice-pack-admin.test.mjs` **17 pass**; `tests/permissions-mirror.test.mjs` **4 pass** (the client matrix now equals `permissions.py`); `next build` exit 0 | Same database/browser limitation; `organization/tests/test_voice_packs_api.py` not executed here |

**Five defects found while verifying, all fixed** (detail in the V1.1 report §0): the missing report screen; the
client permission mirror withholding `org.read` from `org_admin`, which made the voice-pack page unreachable for
its primary role; a refusal-translation table keyed on machine tags the policy never emits; `super_admin` being
refused on a tenant's pack, which made an organisation's `pending_review` version unapprovable from any screen;
and a rollback route with no caller, so restoring a version still needed `curl`.

**§2.2's upload exclusion is retained**, and the reason is now the approved text rather than this record alone:
roadmap MP-04 is *"W3 voice-pack admin surface (preview / publish / retire)"* with deliverables *"Page, tests,
report"*, and creation of a version is the W3 API (audit finding F-50, already implemented and tested). The
residual question — whether an operator should author a version in the browser — is raised as **PO-D1** in the
V1.1 report §9.3 and is **not** decided here.

---

## 7. PO-D1 — browser-based voice-pack upload (decided 26 November 2026)

This section **records a decision taken after** §1–§3 and after the §5 status cross-reference. Nothing in §1–§6 is
amended, re-taken or withdrawn; the earlier text stays exactly as issued.

| Field | Value |
|---|---|
| Decision reference | **PO-D1** |
| Date taken | 26 November 2026 (Product Owner written instruction) |
| Question | Does MP-04 include a browser upload form for creating a voice-pack version? |
| Decision | **Option C — create a separate work package for browser-based voice-pack upload functionality** |
| Effect on MP-04 | None. MP-04 keeps its approved scope (preview, administration, publication, retirement). The browser upload form is **not** added to MP-04 |
| Effect on version creation | None. Creating a version stays the W3 API `POST /api/v1/voice-packs` (implemented and covered by `organization/tests/test_voice_packs_api.py`) |
| New work package | **MP-47** — `plan/AMSDP_MP-47_Browser_Voice_Pack_Upload_Scope_Proposal_V1.0.md` |
| Rationale (owner's words) | "Preserve the approved MP-04 scope and manage the additional upload capability independently." |
| Status of the new package | **PROPOSED** — Product Owner-authorised as a separately scoped package; awaiting detailed specification and implementation authorisation. Not implemented, not accepted |

**What this settles.** §5 recorded PO-D1 as *open* and the MP-04 implementation report §9.3 carried it as the one
remaining question on that package. It is now closed, in the direction the report recommended (A or C; the owner
chose C, which is the stronger of the two because it gives the upload capability its own requirements, tests and
acceptance instead of hiding it inside an administration package).

**What it does not settle.** MP-47's own details — accepted audio containers and size ceilings *for the browser
path*, retention of superseded asset bytes, storage location and quota, and whether a tenant administrator may
upload at all — are **not** decided here. They are listed as open items in the MP-47 proposal §7. No format, size,
retention or storage policy is invented by this record; the proposal cites only limits that already exist in
`backend/organization/voice_pack_policy.py`.

**Acceptance consequence.** MP-04 is to be assessed and accepted against its existing approved requirements. The
absence of a browser upload form is **not** an MP-04 defect, and MP-04 must not be reopened, widened or delayed on
account of MP-47.

---

## 8. Document control

| Field | Value |
|---|---|
| Location | `docs/decisions/AMSDP_Owner_Decisions_26_November_2026_V1.0.md` (`.clinerules` §11: `decisions/`) |
| Predecessor | `docs/decisions/AMSDP_Owner_Decisions_25_November_2026_V1.0.md` (PO-05 §2.4 superseded **for MP-04 only**) |
| Related | `docs/decisions/AMSDP_MP-23_Operational_Reports_Decision_Brief_V1.0.md` (§4 options, §5 recommendation) |
| Implementation evidence | `docs/implementation/AMSDP_MP-23_MP-04_Implementation_Report_V1.1.md` (current; V1.0 retained as history) — status cross-reference in §5 above; PO-D1's closure is recorded in its §12 amendment |
| Later decisions | **PO-D1** (§7, 26 November 2026): browser voice-pack upload is a separate work package (**MP-47**), not part of MP-04. Recorded additively; §1–§6 unchanged |
| Index entry | `docs/governance/AMSDP_Docs_Index_V1.0.md` |

