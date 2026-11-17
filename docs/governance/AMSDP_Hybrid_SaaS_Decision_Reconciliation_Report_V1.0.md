# AMSDP — Hybrid SaaS Decision Reconciliation Report V1.0

> **Document ID:** `AMSDP_Hybrid_SaaS_Decision_Reconciliation_Report`
> **Version:** V1.0 · **Amended 2026-11-17 (post-commit correction, §M)** · **Branch:** `hackathon-mvp` — baseline `409a929`, reconciliation commit `597d9b1`
> **Task:** `AMSDP-HYBRID-SAAS-DECISION-RECONCILIATION-2026-11-17` (the reconciliation itself);
> `AMSDP-SAAS-POST-COMMIT-CORRECTION-2026-11-17` (this documentation-only amendment, §M)
> **Status:** **docs-only reconciliation — committed and pushed, awaiting owner review.** No code,
> schema, migration, endpoint, component, test, compose file or running stack was touched. The
> reconciliation was committed as `597d9b1` and pushed to `origin/hackathon-mvp` (§B, §M); the
> documentation-only amendment recorded in §M corrects the O-SaaS-15 record, two stale A3 summaries and
> this report's own historical commit status. Nothing here is `ACCEPTED`.
> **Written to:** `docs/governance/` (`.clinerules` §11 — the subject is the governance reconciliation
> of an existing document set against owner decisions, not new implementation).
> **Registered in:** `docs/governance/AMSDP_Docs_Index_V1.0.md` (Revision 29; amendment registered in
> Revision 30).

---

## A. Task and authority

The Product Owner reviewed the six-document Hybrid SaaS architecture set
(`docs/architecture/saas/`), produced on 2026-11-17, and issued a decision packet: sixteen numbered
decisions `O-SaaS-1…O-SaaS-16` plus four architectural directions `A1–A4`. The task was to bring the
whole set into line with those decisions **by in-place revision** — no new specification documents, no
renumbering, no deletion of earlier wording — and then to report.

Authority order applied (`.clinerules` §1): verified runtime state → the owner's decisions and approved
business rules → AMSDP governance → adapted agent rules → skills (none installed) → general defaults.
The owner's decisions sit at level 2; this report therefore treats them as binding and treats every
mechanism the specifications describe as still `SPECIFIED`, unbuilt.

## B. Baseline

| Item | Value |
|---|---|
| Branch | `hackathon-mvp` |
| HEAD at task start | `409a929` — `docs(chatgpt): adopt the multi-sector plan and the AMSDP Connect proposal` |
| Working tree at task start | clean |
| Working tree at task end | six modified files under `docs/architecture/saas/`, plus this report and the docs index — **nothing staged at the end of the task** (the owner then instructed the commit; see the row below) |
| Committed after the task | `597d9b1` — `docs(saas): reconcile the six-document SaaS set with the owner decision packet`; 8 files, 1,220 insertions, 346 deletions; branch `hackathon-mvp`, pushed to `origin/hackathon-mvp` (verified after the push: `HEAD` and `origin/hackathon-mvp` both `597d9b11cd782d57ea829a01ce275f297f5a72b3`). See §M |
| Tests run | **none** — no executable artefact changed, so there was nothing to run. No test result is claimed anywhere in this report |
| Services started | none |

`git diff --stat` for the set at the end of the task:

```text
 ..._Hybrid_SaaS_Architecture_Specification_V1.0.md | 674 +++++++++++++++------
 .../AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md  |  65 +-
 ...MSDP_Hybrid_SaaS_Implementation_Roadmap_V1.0.md | 161 +++--
 ...ity_and_Access_Management_Specification_V1.0.md | 171 ++++--
 ...nd_Entitlement_Management_Specification_V1.0.md | 103 +++-
 ...d_Organization_Management_Specification_V1.0.md |  88 ++-
 6 files changed, 926 insertions(+), 336 deletions(-)
```


## C. The decision packet, as applied

Rulings are recorded **verbatim** in `AMSDP_Hybrid_SaaS_Architecture_Specification_V1.0.md` §14.3,
which is the single `O-SaaS` registry. The summary below is a pointer table; where it and §14.3 differ,
§14.3 wins.

| ID | Ruling in one line | Applied in |
|---|---|---|
| O-SaaS-1 | Separate platform identity; the legacy `super_admin` alias and its `platform.*` grants stay until the replacement is tested, then are removed; the tenant role is renamed by controlled migration, never dropped | architecture §12 (ADR-003); IAM §7.4, §13 |
| O-SaaS-2 | **Option A** audit split: `platform_audit_events` for platform-only events, the tenant's `audit_events` (real `organization_id`) for tenant-affecting events, column never nullable | architecture §7.2–§7.3, §9.4; subscription §9.3; roadmap 2.15 / 3.10 |
| O-SaaS-3 | Five-state lifecycle confirmed; automatic expiry capped at `read_only` — never auto-suspend, never delete | architecture §5.3 (ADR-005); tenant §5.1–§5.5 |
| O-SaaS-4 | Ten module keys confirmed as the commercial vocabulary; Core always available, never sold, gated or disabled | architecture §6; subscription §4.1, §11.3 |
| O-SaaS-5 | `lifecycle_state` authoritative, `status` a transitional duplicate whose retirement is deferred with a stated precondition | architecture §7.4 (ADR-005); tenant §5.1; `EQ-8` |
| O-SaaS-6 | Dedicated (P2) and institution-controlled (P3) deployment are **not in MVP**; licence/renewal mechanics stay `SPECIFIED`, undesigned | architecture §2, §4.3 (ADR-012); subscription §4.4; roadmap §8 |
| O-SaaS-7 | **Multi-membership adopted**; ADR-SAAS-013 superseded by ADR-SAAS-014; one active organization per token; switching is an explicit re-authorisation | architecture §7.2, §12, §12.1; IAM §8; roadmap §5.2.1 |
| O-SaaS-8 | `platform_admin` and `platform_ops` separable; holding both is an explicit, individually approved, audited exception | architecture §9.3 (ADR-003); IAM §7.3 |
| O-SaaS-9 | Legacy `organizations.status='inactive'` is preserved, never auto-mapped; only a validated, reviewed backfill to `active` | architecture §7.4; tenant §12.1 |
| O-SaaS-10 | A platform operator is shown in a tenant's audit view by **named identity plus platform role** | architecture §9.4; tenant §10.2 rule 8 |
| O-SaaS-11 | Password-history reuse checks are **post-launch**, `DEFERRED`, risk accepted | IAM §4.6, §13.1 |
| O-SaaS-12 | The operator-assisted reset may return the code to the requesting administrator, under constraints (authenticated operator, audited request, one-time code, no code in logs) | IAM §6.2 |
| O-SaaS-13 | Support grants need **explicit `org_admin` consent every time**; no policy pre-approval, including for `grace` tenants | architecture §9.3; IAM §7.3; roadmap 3.6 |
| O-SaaS-14 | Suspension requires a **second approver**, exactly like closure | architecture §9.3; tenant §5.2 rule 2; roadmap 3.11–3.12 |
| O-SaaS-15 | **Platform operator MFA is required before production launch.** A temporary exception, explicitly documented as a security risk and restricted to a limited authorised operator group, may be used for the hackathon MVP only; it does not satisfy the production requirement and MFA is not deferred | architecture §9.3 rule 7, §14.3; IAM §13.2; roadmap §9.6 |
| O-SaaS-16 | Closure needs platform-administrator approval **plus a second approver**; clinical data is **retained by default**; anonymisation only on legal approval as a separate audited act; `closed` ≠ deleted | architecture §9.3; tenant §11.3 item 5; roadmap §6 |
| A1 | Microservices remain the target; the shared database/schema is the acknowledged V1 compromise | architecture §3.4 (ADR-017) |
| A2 | Three deployment patterns (`shared` / `dedicated` / `institution`); MVP is `shared` | architecture §2, §4.3 (ADR-012) |
| A3 | **Healthcare organization profiles** — `private`, `government`, `ngo`, `community`, `outreach` — are configurable presets in whitelisted tenant configuration, independent of deployment pattern; never a hard restriction, and they alter no isolation, authorisation, lifecycle or audit rule | architecture §2.2, §13 (ADR-SAAS-015) |
| A4 | Platform authority is not a request-path dependency: entitlements are distributed data, enforced locally | architecture §3.5 (ADR-016); subscription §5.4 |

## D. The vocabulary the set now uses

Two independent axes, defined once in architecture specification §1.3 and used by all six documents:

| Axis | Labels | What it means |
|---|---|---|
| Decision | `OWNER-APPROVED` / `SPECIFIED` / `OPEN` / `DEFERRED` / `SUPERSEDED` | who decided, and whether it is decided at all |
| Evidence | `NOT IMPLEMENTED` / `IMPLEMENTED` / `TESTED` / `VERIFIED` | what the tree actually does |

`PROPOSED` is retained **only** as a declared synonym of `SPECIFIED` (and as a historical term inside
revision-history rows). `ACCEPTED` is used only in `.clinerules` §7's sense — the owner signed it — and
never as evidence. `FORBIDDEN` is not used as a status label anywhere in the set; prohibitions are
written as prohibitions.

**The rule that keeps the set honest:** a decision moves the decision axis only. Nothing in this
reconciliation advanced a single evidence label, and every mechanism in every document remains
`NOT IMPLEMENTED`.

## E. What changed, document by document

Every document was revised **in place**: same filename, same version `V1.0`, a `Revision 2` line in the
header, and a `§15.1` (or `§16.1`) revision-history table. No section was deleted; superseded wording
sits under an explicit banner. Sizes are `wc -c` before (`409a929`) → after.

| # | Document | Size | What Revision 2 added or changed |
|---|---|---|---|
| 1 | `AMSDP_Hybrid_SaaS_Architecture_Specification_V1.0.md` | 57,124 → 98,511 | §1.5 decision record; two-axis vocabulary (§1.3); A1 microservice target and its transitional compromises (§3.4, ADR-017); A2 three deployment patterns (§2, §4.3, ADR-012); A3 profiles (§2.2, ADR-015); A4 platform authority (§3.5, ADR-016); **ADR register (§12)** incl. ADR-014 superseding 013 and §12.1 explaining what stays true; **traceability (§13)**; §14.3 registry **closed** with all sixteen verbatim rulings; **§14.3.1 engineering questions `EQ-1…8`**; §14.4 self-check; §15.1/§15.2 revision history. Stale `B1/B2/B3` wording normalised to `P1/P2/P3` (one verbatim question row keeps the original terms, deliberately) |
| 2 | `AMSDP_Identity_and_Access_Management_Specification_V1.0.md` | 41,112 → 46,345 | Header + two-axis vocabulary (§1.3); §2.1 as-built baseline annotated as the *multi-membership target's* starting point; principal table re-labelled (`OWNER-APPROVED` model vs `SPECIFIED` table); §4.1 `A-1…A-3` re-labelled `SPECIFIED`; §6.2 constraint on the operator-assisted reset (O-SaaS-12); §7.4 R-3 made conditional on `TESTED`/`VERIFIED` (O-SaaS-1); **§8.1 rewritten to multi-membership** with `EQ-1…3` and new §8.1.1; §13 turned from an open-item list into an applied-rulings table; §13.1 multi-membership risk + O-SaaS-15 record (restated as a production-launch requirement in the Revision 3 amendment, §M); §14 self-check/traceability; §15.1/§15.2 |
| 3 | `AMSDP_Tenant_and_Organization_Management_Specification_V1.0.md` | 34,421 → 39,178 | Header + authority order/two-axis (§1.3); §5.1 Revision 2 note (ADR-SAAS-005 `OWNER-APPROVED`); §5.2 transition table + rule 2 — **suspension needs a second operator** (O-SaaS-14) and **closure needs two approvers** (O-SaaS-16); §5.4 scheduler labels `PROPOSED` → `SPECIFIED` (O-SaaS-14 caps automatic action at `read_only`); §10.2 rules 7–8 (audit-plane routing per O-SaaS-2, named-operator disclosure per O-SaaS-10); §11.3 precondition 5 + retain-by-default note; §14 self-check/traceability; §15.1/§15.2 |
| 4 | `AMSDP_Subscription_and_Entitlement_Management_Specification_V1.0.md` | 33,204 → 37,293 | Header + two-axis vocabulary; §1.1 authority chain extended with the decision packet; §1.2 Revision 2 note (ten keys `OWNER-APPROVED`, mechanisms `SPECIFIED`); §4.4 billing columns **explicitly not created in V1** (O-SaaS-6, `EQ-6`); resolver/gate snippets `PROPOSED` → `SPECIFIED`; **§9.3 rewritten** from "platform-audit caveat" to the settled option-A split with the dual-write obligation (`EQ-4`); §14 converted from open items to applied rulings; §14.1 residual risks re-anchored to `EQ-5`; §15 compliance + self-check; §16.1/§16.2 |
| 5 | `AMSDP_Hybrid_SaaS_Implementation_Roadmap_V1.0.md` | 35,588 → 43,005 | Header/status `SPECIFIED` (Revision 2); phase table updated (Phase 2 now lands multi-membership, Phase 3 proves four-eyes, Phase 5+ is P2/P3/introspection — operator MFA moved out of the deferred list into the production-launch gate §9.6 by the Revision 3 amendment, §M); §4.1/§5.1/§6.1 converted from "decisions required" to **"decisions applied — all now decided"** with the ruling and its consequence per row; **new 2.12–2.14** (membership migration, active-org transport, per-membership roles — `EQ-1…3`) and **2.15** (`platform_audit_events` + dual write); **new §5.2.1** explaining why membership moved from Phase 5+ to Phase 2; Phase 2 gate gained three membership checks; **new 3.11–3.12** (two-person primitive before the closure button) with `EQ-7` noted as an owner question; §6.4 bans single-operator suspension/closure and anonymisation; §6.5 gate proves retain-by-default, four-eyes, dual audit and no `grace` shortcut; §8 deferred list re-cut; K-9 re-anchored to O-SaaS-12; R-09/R-13/C-7 traceability updated; §15.1/§15.2 |
| 6 | `AMSDP_Hybrid_SaaS_Current_State_Audit_V1.0.md` | 41,705 → 46,232 | **Findings kept verbatim** (measured at `133ce83`). Added: a header **correction note** stating that every question the audit raised is now decided and that no evidence grade moved; a correction on the `PROPOSED` grade row (§1.3); a correction after §4.1's no-membership paragraph; C-1 (ADR-SAAS-002 → `OWNER-APPROVED` as A1); C-7 (ADR-SAAS-009 → option A settled); K-8 (risk inverted: a decision is not evidence); §13 entry-point note; §14.2 turned into a question table **with the rulings appended** |

Net: `926 insertions(+), 336 deletions(-)` across the six files. The deletions are stale status
sentences and superseded opening paragraphs, each replaced in place; no evidence finding, ruling or
business rule was removed.



## F. Conflicts found, and how each was handled

`.clinerules` §1 requires a conflict to be reported, never silently resolved. Six were found and are
recorded below with their disposition.

| # | Conflict | Disposition |
|---|---|---|
| F-1 | The set originally deferred **multi-membership** to Phase 5+, while O-SaaS-7 adopts it and `EQ-1` states it **blocks the Phase 2 migration** | **Ruling wins.** The roadmap moves membership into Phase 2 (2.12–2.14, §5.2.1). The concern behind the deferral — a second tenant key — is answered explicitly: `organization_memberships` is a join, `organization_id` stays the only tenant key (D-1) |
| F-2 | The original §14.3 registry listed decisions as open, and the sibling documents cited them as open items in their §13 / §14 / §14.2 | **Registry closed** with the rulings; every citing section converted into an applied-rulings table. Historical question wording is kept verbatim in §14.3 and in the audit §14.2 |
| F-3 | ADR-SAAS-013 (one organization per identity) contradicts O-SaaS-7 | ADR-013 marked `SUPERSEDED` **in place**, kept for traceability; ADR-014 added; architecture §12.1 explains what the old ADR got right and how the new model preserves it |
| F-4 | The audit recorded `PROPOSED` / `OPEN` statuses and an open-items table | The audit is a **record**, so its findings stay verbatim; the correction is a dated note plus the rulings appended to §14.2. Rewriting an audit to match a later decision would destroy its value as evidence |
| F-5 | BR §39's suspended reading versus an automatic scheduler | O-SaaS-3 caps the scheduler at `read_only`; tenant §5.4–§5.5 and roadmap §5.4 all state that automatic suspension is forbidden |
| F-6 | Two documents could each have owned the platform-audit shape (architecture §7.3, subscription §9.3) | One ruling (O-SaaS-2), one mechanism, two views: architecture owns the shape, subscription owns the commercial-event consequences and cites `EQ-4` for cross-store consistency |

No conflict required a business-rule change, and none was invented to make the documents agree. Where
the set lacked an answer (entitlement distribution mechanics, the membership cutover), the answer was
**not guessed** — it became an `EQ` question with a named owner and a stated blocking phase.

## G. Evidence status — what this task did and did not establish

| Claim | Status |
|---|---|
| The six documents now agree with O-SaaS-1…16 and A1–A4 | **IMPLEMENTED** (the text exists and is reachable) and **read** end to end — not `ACCEPTED` until the owner signs |
| The decisions are recorded once, canonically, with verbatim wording | `IMPLEMENTED` — architecture §14.3 |
| The engineering questions are tracked in one id space | `IMPLEMENTED` — architecture §14.3.1 |
| Anything in the specifications works | **Not claimed.** Every mechanism is `SPECIFIED` with evidence `NOT IMPLEMENTED` |
| Tests pass | **Not claimed.** No test was run; no executable file changed |
| Runtime behaviour | **Not claimed.** No service was started and no API was called |
| Documentation is registered | `IMPLEMENTED` — docs index Revision 29 |

This is deliberate under `.clinerules` §7: a green suite would not have made the design `VERIFIED`, and
the absence of one is not a gap because nothing executable changed. The next artefact that could earn
`VERIFIED` is the roadmap Phase 0 runtime verification, which is still unperformed.


## H. Residue scan (consistency checks actually run)

Checks were run with `grep` over the six files at the end of the task; results are reported as found.

| Check | Result |
|---|---|
| `PROPOSED` still used as a live status | **None.** Survives only in declared-synonym sentences, revision-history rows and the audit historical vocabulary row (annotated) |
| `OPEN` still describing a decided item | **None** live. Remaining occurrences are historical statements explicitly bracketed as such (audit §4.1, IAM §8.1 recording what V1.0 said) |
| `B1` / `B2` / `B3` tier labels | **None** as labels. One verbatim question row (O-SaaS-6) keeps the original wording and is marked verbatim |
| Dangling `O-SaaS` ids (above 16, or defined nowhere) | None — the only ids are 1…16, all defined in architecture §14.3 |
| `EQ` ids referenced but not defined | None — `EQ-1…8` are defined in §14.3.1 and every citing document uses the same ids |
| Cross-document references added by this revision | Verified by reading; each named section exists in the file it names: architecture §1.3, §1.5, §12, §12.1, §13, §14.3, §14.3.1; IAM §8.1, §8.1.1; tenant §5.2, §11.3; subscription §9.3; roadmap §5.2.1, 2.12–2.15, 3.11–3.12 |
| Stale decisions-required headings | None — all three converted (roadmap §4.1, §5.1, §6.1). The phrase survives only inside the roadmap revision-history row |
| Every document carries a revision history | Yes — architecture §15.1, IAM §15.1, tenant §15.1, subscription §16.1, roadmap §15.1. The audit carries a dated header correction note instead, because it was not rewritten |
| Pre-revision sizes recorded for the index | Yes — read from `git show 409a929:` for each file; they match the sizes the index recorded at Revision 27 |
| Index row count after this task | 81 → **82** registered rows (this report is new); nothing on disk was removed |
| Post-commit re-scan (amendment, §M) | Re-ran the MFA, A3 and commit-status scans over the six documents and this report: **no live statement now describes MFA as deferred past production, optional for production, permanently accepted as absent, or satisfied by the hackathon exception**; A3 appears only as the five approved profiles; no document claims the reconciliation is uncommitted. Details in §M |

## I. The engineering questions this leaves open

`EQ-1…8` are recorded once, in architecture specification §14.3.1. They are **not** owner decisions,
they may not be answered by weakening a ruling, and they gate specific phases.

| ID | Question, shortened | Blocks | Why it matters |
|---|---|---|---|
| `EQ-1` | Physical shape of multi-membership: retiring `staff_users.organization_id` into a join, backfill, cutover point | Phase 2 migration | touches every existing login; must be forward-only and idempotent; no data loss |
| `EQ-2` | Transport of the active organization: token claim plus a switch endpoint, versus per-request exchange | Phase 2 | a request must never name its own tenant; a revoked membership must fail on the next request |
| `EQ-3` | Membership lifecycle: invitation, revocation, suspension, and how per-membership role plus branch scope compose | Phase 2 | least privilege per tenant; the role of the named membership, never a union across memberships |
| `EQ-4` | Cross-store consistency of the second audit write (one transaction now, an outbox after A1) | Phase 2 / A1 split | **can become a silent security defect**: a tenant-affecting action without a tenant-side row |
| `EQ-5` | Entitlement distribution: version stamp, propagation, staleness bound, behaviour when stale | Phase 2 | **can become a silent security defect**: stale data must fail closed on optional modules only and can never switch off Core |
| `EQ-6` | Licence and renewal mechanism for P2/P3 | post-MVP | must not leak into P1 behaviour and must not make the platform a request-path dependency |
| `EQ-7` | Whether a single-operator emergency override should exist at all | nothing today | explicitly an **owner** question; any override weakens the control O-SaaS-14/16 exist to create |
| `EQ-8` | Retirement precondition for the transitional `organizations.status` column | Phase 2+ | a compatibility read surviving removal would resurrect the old vocabulary |

`EQ-4` and `EQ-5` are the two that can turn into security defects rather than clean-up debt if they are
still unanswered after Phase 2, because both decide what happens when the platform and the tenant
disagree. Neither may be answered by calling the platform synchronously — that is the design A4 forbids.

## J. Risks this reconciliation accepts

1. **Document weight.** The architecture specification grew from 57 KB to 98 KB. It is now the single
   place to look for a ruling, and the price is that a full read costs context. Mitigation: §14.3 is the
   lookup table, and the index points at sections rather than at the whole file.
2. **Two-tier truth.** An audit that keeps verbatim historical wording next to dated corrections can be
   misread if the correction note is skipped. Mitigation: that note is the first block after the header,
   and every corrected row is bracketed in place.
3. **Decisions mistaken for progress.** The most likely failure now is a reader treating
   `OWNER-APPROVED` as built. Mitigation: the two-axis rule is stated in every document and repeated
   here; no roadmap gate is satisfied by a ruling.
4. **Phase 2 grew.** Membership, the platform-audit table and the two-person primitive all land in the
   one phase allowed to break the demo. Mitigation: the intra-phase ordering (2.6/2.7 then 2.8/2.9 then
   2.10; 3.11 before 3.7) is written inside the phase, and the exit gate is the demo re-run itself.
5. **No review yet.** Nothing here is `ACCEPTED`. The owner has not signed this revision, and this
   report does not imply otherwise.

## K. Governance and skill compliance (`.clinerules` §6)

| Requirement | Compliance |
|---|---|
| §1 precedence | Owner decisions treated as binding (level 2); verified runtime state never contradicted — the audit's evidence grades were left untouched precisely because the tree still behaves as it did at `133ce83` |
| §2 automatic routing | Domains: documentation governance (primary), plus the backend, auth/RBAC, multi-tenant, migration, audit and observability rows whose requirements the revised text must keep satisfying. `docs/governance/AMSDP_Docs_Index_V1.0.md` read first, then the six documents and the product authorities they cite |
| §3 non-negotiables | `organization_id` remains the only tenant key (membership is a join, never a second key); cross-tenant reads still fail `404`; audit stays append-only with no nullable tenant column; denials audited; no secret quoted from any document; no capability claimed that is unbuilt; no migration invented — every schema change discussed is still `SPECIFIED` and forward-only |
| §4 domain table | Applied as adapted: `saas-multitenant-data.md` §4–§5 (tenant key, migration shape), `saas-application-security.md` (server-side enforcement), `saas-observability.md` (redaction, denial recording), `saas-auth-and-authorisation.md` (platform identity separation, four-eyes), `saas-cicd-workflow.md` (git safety, honest CI state) |
| §5 skills | **No skills installed.** Verified again this session: no `.clinerules/skills/`, no `.claude/skills/`, no repo `skills/`. None used, none claimed. Where a skill would normally guide a domain, the governance documents above were used instead |
| §6 compliance reporting | This section, plus the equivalent governance section inside each of the six documents |
| §7 evidence standard | §G above: `IMPLEMENTED` for text and registration only; nothing `TESTED` or `VERIFIED`; `ACCEPTED` explicitly withheld pending owner review |
| §8 LLM routing policy | Not exercised as a routing decision; no local model invocation was attempted or claimed |
| §9 execution boundaries | No destructive git operation (`reset --hard`, `clean -fd`, `stash`, `checkout .`); no service started; no suite run. The working tree was left modified and unstaged at the end of the task, and the owner then instructed the commit — `597d9b1`, pushed to `origin/hackathon-mvp` (§M). The later amendment follows the same boundary: documentation files only |
| §11 output location | This report in `docs/governance/`; the six revisions in place under `docs/architecture/saas/`; **no document moved, renamed, overwritten or deleted**, so no migration-manifest entry is required and none was written; no new top-level folder created |
| §12 reading and index policy | Index read before acting; documents cited by the section actually opened this session; index updated in the same task (Revision 29, plus a row for this report) |

## L. What the owner is asked to review

1. **Accept or reject this revision of the six documents** (`ACCEPTED` is the owner's signature, not the
   agent's). Nothing else in the set changes until that happens.
2. **Check the three rulings most likely to be misread:**
   - O-SaaS-9 — no legacy `inactive` row is auto-mapped; the backfill is reviewed, not automatic.
   - O-SaaS-16 — closure **retains** clinical data by default; anonymisation is a separate legal act.
   - O-SaaS-13 — `grace` tenants get **no** shortcut on support-grant consent.
3. **Decide `EQ-7`** (single-operator emergency override): the set records it as an owner question with
   no answer, deliberately. If the answer is yes, it needs time-boxing, a reason, and both identities
   in the audit trail.
4. **Note that `EQ-1…3` block the Phase 2 migration**, so the membership design work must be scheduled
   before Phase 2 starts, not inside it.
5. **The reconciliation is committed and pushed** — `597d9b1` on `hackathon-mvp`, pushed to
   `origin/hackathon-mvp`, working tree clean after the push (§M.1). Committing is not accepting: the
   set is still not `ACCEPTED`, and the amendment in §M changes no ruling.

---

## M. Post-commit correction record (2026-11-17)

Recorded **after** the reconciliation commit, so that this report never contradicts the repository it
describes. Nothing above was rewritten as though the original task had performed the commit; the two
rows that described the tree as unstaged (§B, §L) are corrected in place and the history is kept here.

### M.1 Where the reconciliation actually landed

| Item | Value |
|---|---|
| Reconciliation commit | `597d9b11cd782d57ea829a01ce275f297f5a72b3` (`597d9b1`) — `docs(saas): reconcile the six-document SaaS set with the owner decision packet` |
| Parent | `409a929` (the baseline recorded in §B) |
| Branch | `hackathon-mvp` |
| Push | **completed** to `origin/hackathon-mvp` (`409a929..597d9b1`); verified after the push — `git rev-parse HEAD` and `git rev-parse origin/hackathon-mvp` both returned the full SHA above, and the working tree was clean with no ahead/behind |
| Commit contents | 8 files changed, 1,220 insertions(+), 346 deletions(-): the six SaaS documents, this report and the docs index |
| Application code, schema, migration, service or test in that commit | **none** |

### M.2 What this amendment corrects (documentation only)

| # | Correction | Files |
|---|---|---|
| 1 | **O-SaaS-15 restated.** The set described operator MFA as `DEFERRED`, "risk accepted for MVP", "first post-launch hardening item" — wording that reads as optional, permanent acceptance, or a post-launch enhancement. It now separates three contexts: **hackathon MVP** (temporary exception, explicitly documented as a security risk, restricted to a limited authorised operator group), **production launch** (MFA **mandatory before any platform operator receives production access**) and **post-launch** (MFA already in place). No mechanism, provider, enrolment flow or implementation status is invented: MFA is `NOT IMPLEMENTED`, and the roadmap now carries the gate as §9.6 rather than a Phase 5+ entry | architecture §1.5, §9.3 rule 7 (new), §11 non-goal row, §14.3, §14.4, §15.1; IAM §13, §13.1, **§13.2 (new)**, §14, §14.1, §15.1; roadmap §2.1, §6.1, §8, §9.4, **§9.6 (new)**, §14.1, §15.1 |
| 2 | **A3 corrected.** This report described the profiles as "internal/dedicated". The owner-approved set is `private`, `government`, `ngo`, `community`, `outreach` — configurable presets, independent of deployment pattern, never a hard restriction, and never a discriminator for isolation, authorisation, lifecycle or audit. §C now matches architecture §2.2, which was already correct and was **not** rewritten. The same stale wording also survived in the roadmap's §8 P3 row and was corrected there | this report §C; roadmap §8, §15.1 |
| 3 | **Commit status corrected.** The report no longer states that the reconciliation is uncommitted, unpushed, or "sitting in the working tree for review" | this report header, §B, §E, §H, §K, §L, §M |

No ruling was changed, no `EQ` question was answered (`EQ-4`, `EQ-5` and `EQ-7` remain open), no
evidence grade moved, no phase or dependency was added outside §9.6, and no application file was
touched.

### M.3 Evidence status of this amendment

| Claim | Status |
|---|---|
| The three corrections are present in the files listed in §M.2 | `IMPLEMENTED` — the text is in the tree and was re-read after editing |
| The corrections are consistent | Checked by re-running the MFA / A3 / commit-status scans over the six documents and this report (§H, last row). Prose cannot be covered by a test suite, and none is claimed |
| Anything works | **Not claimed** — no code, schema, migration, service or test was touched |
| MFA is implemented | **No.** `NOT IMPLEMENTED`; every box in the roadmap gate §9.6 is unsatisfied |
| The set is `ACCEPTED` | **No.** `ACCEPTED` is the Product Owner's signature and has not been given |

**Self-reference, stated rather than fudged.** This report cannot contain the SHA of the commit that
adds this section — the commit is created after these words exist, so a SHA printed here would be
wrong or stale. Verify the amendment from the repository instead:

```text
git log --oneline -1 -- docs/governance/AMSDP_Hybrid_SaaS_Decision_Reconciliation_Report_V1.0.md
git rev-parse HEAD origin/hackathon-mvp
```

The only push verified *inside* this document is the reconciliation push in §M.1, which had already
completed when this text was written.

### M.4 Sizes after the amendment

`wc -c` on the files this amendment changed, read after the final edit. This report's own size is
recorded in the docs index (Revision 30) instead of here, because writing its size into itself would
change it again.

| File | Size after the amendment |
|---|---:|
| `docs/architecture/saas/AMSDP_Hybrid_SaaS_Architecture_Specification_V1.0.md` | 102,190 |
| `docs/architecture/saas/AMSDP_Identity_and_Access_Management_Specification_V1.0.md` | 51,470 |
| `docs/architecture/saas/AMSDP_Hybrid_SaaS_Implementation_Roadmap_V1.0.md` | 48,538 |

The sizes quoted in §E remain the **Revision 2** values, as recorded between `409a929` and the
reconciliation commit `597d9b1`; they are history, not a description of the current files.

---

*End of report. Written to `docs/governance/` per `.clinerules` §11; registered in
`docs/governance/AMSDP_Docs_Index_V1.0.md` per §12. No code, schema, migration, endpoint, component,
test or running stack was touched by this task, and no test result is claimed.*


