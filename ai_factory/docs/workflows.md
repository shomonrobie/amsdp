# AI Factory Workflows

The ten approved workflows from AI Development Workflow V1.0 are registered
in `workflows/registry.py` and executed by `workflows/engine.py`.

## Workflow statuses (honest capability labels)

| Workflow | Name | Status | Executable |
|---|---|---|---|
| WF-01 | Requirement-to-Design | executable | yes |
| WF-02 | Service Implementation | executable | yes |
| WF-03 | Frontend Delivery | executable | yes |
| WF-04 | Defect Resolution | executable | yes |
| WF-05 | Architecture Decision | executable | yes |
| WF-06 | Database Change | executable | yes |
| WF-07 | Security Review | executable | yes |
| WF-08 | Cross-Service Integration | executable | yes |
| WF-09 | Release Readiness | executable | yes |
| WF-10 | Documentation Update | executable | yes |

The engine refuses `run()` for anything not `executable`. Partial/planned
workflows are fully defined (purpose, stages, agents, artifacts, gates) but
are not claimed as working.

## WF-01 Requirement-to-Design

Stages: product analysis (A01) → architecture impact (A02) → service design
(A03) → database design (A04) → API contract design (A05) → test planning
(A08) → security planning (A09) → **human design approval gate**.

Exit: task moves to `READY_FOR_IMPLEMENTATION` only after a human
`approved` decision via the ApprovalService.

## WF-10 Documentation Update

Stages: identify source (A11) → draft changes (A11) → **doc-link validation
(tool stage, engine-run)** → **human review gate**.

## Gates

- WF-01/WF-05: `HUMAN_DESIGN_APPROVAL`.
- WF-02/WF-03/WF-04/WF-06/WF-07/WF-08/WF-10: `HUMAN_REVIEW`.
- WF-09: `AWAITING_DEPLOYMENT_APPROVAL` (the factory never deploys).

Agents can never approve their own work: gates are decided exclusively
through `ApprovalService.decide`, which enforces the lifecycle.

## Failure, retry, resume

- Bounded retries per stage (default 2); transient/correctable failures retry.
- Repeated failure → task `FAILED`/`BLOCKED`, run `FAILED`, escalation note.
- Paused runs (`AWAITING_APPROVAL`) resume after the human decides; a
  terminal task can never be resumed.