# AMSDP Release Readiness Review — Stage 1: Detailed Review V1.0

**Review date:** 4 November 2026  
**Stage 0 reference:** `AMSDP_Release_Readiness_Stage_0_Project_Inventory_V1.0.md`  
**Review mode:** Read-only inspection (no modifications)  
**Reviewer:** AILI (A01–A11 composite)

---

## Executive Summary

Stage 1 examines each Stage-0 finding at depth and assesses the project's true readiness for staging deployment. The review finds that the AMSDP project has **well-articulated specifications but no executable code**. The project is at a pre-implementation decision point: 10 documented architectural decisions remain unresolved, the architecture baseline is unapproved, and the Build Order is undefined.

**Stage 1 finding:** Staging deployment is **NOT POSSIBLE** with the current repository state. The AILI Factory is ready to begin implementation, but is waiting for human decisions on the architecture baseline, technology choices, and build order.

---

## 1. Document Consistency Analysis

### Source-of-truth hierarchy (AI Factory Architecture §2.2)

```
1. Project owner explicit decisions
2. Business Rules V1.0 (approved)
3. MVP Scope V1.0 (approved)
4. System Architecture V1.0 (proposed)
```

### Findings

| Comparison | Finding | Classification |
|---|---|---|
| BR V1.0 vs MVP Scope V1.0 | Internally consistent. Both define same scope boundaries. | ✅ **VERIFIED** |
| BR V1.0 vs System Architecture V1.0 | Consistent. Architecture implements all BR requirements. | ✅ **VERIFIED** |
| Architecture status | Labelled "proposed baseline" — requires formal approval. | ⚠️ **UNRESOLVED** |
| ADRs | 20 ADRs referenced. **None documented as independent records.** | ❌ **GAP** |

### Open decision points (from System Architecture)

| # | Decision | Document Reference | Impact if unresolved |
|---|---|---|---|
| D1 | Architecture baseline approval | §1 (status: proposed) | No implementation can begin |
| D2 | Event broker technology | §6.3 (not selected) | Outbox/async events blocked |
| D3 | API Gateway technology | §9 (proposed) | Frontend-to-service routing undefined |
| D4 | Authentication mechanism | §10 (implementation decision) | Identity design blocked |
| D5 | Password hashing algorithm | §10 (stated, not selected) | Identity design blocked |
| D6 | DB-per-service deployment model | §12.1 (proposed) | Infrastructure architecture |
| D7 | Deployment orchestration | §12.2 (candidate) | Infrastructure architecture |
| D8 | Cross-service auth mechanism | §10 (required, not selected) | Service communication |
| D9 | Platform Admin ownership | §5.10 (open) | Service boundary |
| D10 | Patient mobile uniqueness policy | BR §11 (configurable) | Patient Service default |
---

## 2. AILI Factory Readiness Assessment

### Service/AILI capability mapping

| AMSDP Service | Required WF | Key Tool | Readiness |
|---|---|---|---|
| Identity & Access | WF-01→WF-02 | secret_scan, static_analysis | ✅ Ready |
| Organization | WF-01→WF-02 | repo_read, artifact_write | ✅ Ready |
| Branch & Facility | WF-01→WF-02 | repo_read, artifact_write | ✅ Ready |
| Patient | WF-02 | secret_scan, static_analysis | ✅ Ready |
| Doctor | WF-02 | repo_read, artifact_write | ✅ Ready |
| Scheduling | WF-02 | openapi_validator, contract_test_tool | ✅ Ready |
| Appointment | WF-02 | contract_test_tool, test_runner | ✅ Ready |
| Queue | WF-02 | test_runner | ✅ Ready |
| Audit | WF-02 | contract_test_tool | ✅ Ready |

All 14 AILI tools are applicable. **AILI is FULLY READY** to build all 9 services. The gap is not in tooling.

---

## 3. Risk Assessment of Stage 0 Blockers

| # | Blocker | Risk Level | Mitigation |
|---|---|---|---|
| B1 | No backend services | **CRITICAL** | Sequential build starting with Identity. 5 sprints estimated. |
| B2 | No frontend code | **CRITICAL** | Next.js requires separate environment. API-first approach mitigates. |
| B3 | No database schemas | **HIGH** | AILI MigrationValidator exists. Schema design decisions needed. |
| B4 | No machine-readable API contracts | **HIGH** | OpenAPI generated per service. Contract tooling exists. |
| B5 | No auth/authorization code | **CRITICAL** | First service to build — Identity & Access. |
| B6 | No audit implementation | **HIGH** | Implement after Identity. Service events feed Audit. |
| B7 | No runtime test suite | **HIGH** | Generated alongside service code via run_tests. |
| B8 | No Dockerfiles | **MEDIUM** | Standard FastAPI+uvicorn pattern. One-time per service. |
| B9 | No CI/CD pipeline | **MEDIUM** | One-time setup. AILI ci_config_validator can validate. |
| B10 | No environment config | **MEDIUM** | Generated when first service is built. |

---

## 4. Service Dependency Graph and Build Order

```
Identity & Access  ──►  Organization  ──►  Branch & Facility
      │                                       │
      ▼                                       ▼
Patient ◄────── Doctor ◄────── Scheduling
  │                 │                 │
  ▼                 ▼                 ▼
Appointment ◄──────┘                  │
  │                                   │
  ▼                                   ▼
Queue ◄───────────────────────────────┘
  │
  ▼
Audit
```

| Priority | Service | Rationale | Est. sprints |
|---|---|---|---|
| 1 | **Identity & Access** | Foundation: auth, tokens, roles | 1 |
| 2 | **Organization** | Tenant boundary | 1 |
| 3 | **Branch & Facility** | Org sub-structure | 0.5 |
| 4 | Patient | Core entity | 1 |
| 5 | Doctor | Core entity | 0.5 |
| 6 | Scheduling | Doctor dependency | 1 |
| 7 | Appointment | Core workflow | 1 |
| 8 | Queue | Core workflow | 1 |
| 9 | Audit | Cross-cutting | 0.5 |

**Total:** 7.5 sprints. Frontend: parallel track beginning at Sprint 3.

---

## 5. Open Decisions — Human Resolution Required

| Dec | Decision | Recommended Default | Urgency |
|---|---|---|---|
| D1 | Approve architecture baseline | Accept System Architecture V1.0 | **Before Sprint 1** |
| D2 | Event broker | Start without broker; select by Sprint 5 | **Before Sprint 5** |
| D3 | API Gateway | Direct service calls in dev; add before staging | **Before Sprint 7** |
| D4 | Auth mechanism | Server-managed JWT | **Before Sprint 1** |
| D5 | Password hashing | bcrypt | **Before Sprint 1** |
| D6 | DB deployment model | Separate logical DBs, one server | **Before Sprint 1** |
| D7 | Orchestration | Docker Compose initially | **Before Sprint 8** |
| D8 | Service-to-service auth | Shared JWT secret for dev | **Before Sprint 5** |
| D9 | Platform Admin ownership | Merge into Org + Identity | **Before Sprint 2** |
| D10 | Mobile uniqueness policy | Allow duplicates (per BR §11) | **Before Sprint 4** |
---

## 6. Security Gap Detail (expanded from Stage 0)

| Requirement | Current State | Remediation Sprint |
|---|---|---|
| Password hashing | Not implemented (no credentials exist) | Sprint 1 |
| JWT secret management | Not implemented | Sprint 1 |
| Tenant isolation (server-side org scoping) | Not implemented | Sprints 1–9 |
| RBAC enforcement on endpoints | Not implemented | Sprints 1–9 |
| Input validation (Pydantic) | Not implemented | Sprints 1–9 |
| HTTPS/TLS | Not implemented | Sprint 8 |
| Service-to-service auth | Not implemented | Sprint 5 |
| Audit event security | Not implemented | Sprint 9 |
| CSRF protection | Not implemented | Sprint 7 |
| Session management | Not implemented | Sprint 1 |

---

## 7. Conclusion

### What is ready
1. **Product requirements** — approved, consistent, detailed (1,112-line BR, 835-line MVP Scope)
2. **System architecture proposal** — well-structured, internally consistent, awaiting approval
3. **AILI Factory** — fully capable of building all 9 services with existing tools and workflows

### What is not ready
1. **Architecture baseline approval** — required before implementation can begin with confidence
2. **10 open architectural decisions** — must be resolved per sprint schedule
3. **All runtime code** — 9 microservices plus frontend, database, infrastructure — at zero implementation

### Recommendation

Staging deployment is **not feasible** with the current repository state. Recommended action:

**Resolve D1 (approve architecture baseline), then begin Sprint 1 (Identity & Access Service).**

AILI is ready to execute when the baseline is approved.

---

**Stage 1 detailed review complete.** 10 open decisions identified. Build order defined. Risk levels assessed.

**Stop:** Awaiting human decision to resolve open decisions and begin implementation.