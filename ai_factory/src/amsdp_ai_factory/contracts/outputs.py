"""Structured output contracts for agent handoffs.

Every inter-agent workflow handoff uses a typed, validated artifact model
(AI Factory Implementation Prompt section 6.6). A model's presence is
necessary but not sufficient: ``validate_output`` performs field-level
checks, and the workflow engine additionally verifies evidence/artifact
paths before accepting a stage as successful.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from amsdp_ai_factory.tasks.models import now_utc


class ArtifactKind(str, Enum):
    """The artifact kinds recognized byFactory workflows."""

    REQUIREMENT_ANALYSIS = "requirement_analysis"
    ARCHITECTURE_PROPOSAL = "architecture_proposal"
    SERVICE_IMPLEMENTATION_PLAN = "service_implementation_plan"
    DATABASE_CHANGE_PROPOSAL = "database_change_proposal"
    API_CONTRACT = "api_contract"
    CODE_CHANGE_SUMMARY = "code_change_summary"
    TEST_PLAN = "test_plan"
    TEST_REPORT = "test_report"
    SECURITY_REVIEW = "security_review"
    RELEASE_READINESS_REPORT = "release_readiness_report"
    DOCUMENTATION_UPDATE_REPORT = "documentation_update_report"
    ARCHITECTURE_DECISION_REQUEST = "architecture_decision_request"


class EvidenceRef(BaseModel):
    """Reference to evidence backing an agent's claims."""

    model_config = ConfigDict(extra="forbid")

    kind: str = "artifact"
    path: str
    sha256: str | None = None
    verified: bool | None = None   # set by the workflow engine, not the agent


class AcceptanceVerdict(BaseModel):
    """How one acceptance criterion was disposed of."""

    model_config = ConfigDict(extra="forbid")

    criterion: str
    met: bool = False
    evidence: str = ""


class TestRunResult(BaseModel):
    """One executed test command's outcome."""

    model_config = ConfigDict(extra="forbid")

    command: str
    exit_code: int | None = None
    outcome: str = "not_run"  # passed | failed | blocked | not_run
    summary: str = ""
    report_path: str | None = None


class FileChange(BaseModel):
    """One changed file in a code change summary."""

    model_config = ConfigDict(extra="forbid")

    path: str
    change_type: str = "modified"  # added | modified | deleted | renamed
    lines_changed: int | None = None


class AgentOutput(BaseModel):
    """Common envelope for every agent handoff artifact."""

    model_config = ConfigDict(extra="forbid")

    artifact_type: str
    task_id: str
    workflow_id: str | None = None
    stage_id: str | None = None
    agent_id: str | None = None
    produced_at: datetime = Field(default_factory=now_utc)
    title: str
    summary: str
    source_document_refs: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)

    @field_validator("title", "summary")
    @classmethod
    def _non_empty(cls, value: str, info) -> str:
        if not value.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return value.strip()

    @field_validator("task_id")
    @classmethod
    def _task_id_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("task_id must not be empty")
        return value.strip()
class RequirementAnalysis(AgentOutput):
    """WF-01 stage output: user stories, acceptance criteria, traceability."""

    artifact_type: Literal["requirement_analysis"] = "requirement_analysis"
    user_stories: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    business_rule_refs: list[str] = Field(default_factory=list)
    scope_classification: str = ""
    exception_cases: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    traceability: list[AcceptanceVerdict] = Field(default_factory=list)


class ArchitectureProposal(AgentOutput):
    """WF-01/WF-05 stage output: system-level design proposal."""

    artifact_type: Literal["architecture_proposal"] = "architecture_proposal"
    affected_services: list[str] = Field(default_factory=list)
    decision_required: bool = False
    alternatives: list[str] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    adr_required: bool = False
    consistency_notes: list[str] = Field(default_factory=list)


class ServiceImplementationPlan(AgentOutput):
    """WF-02 input: bounded service work package."""

    artifact_type: Literal["service_implementation_plan"] = "service_implementation_plan"
    service_name: str = ""
    capabilities_in_scope: list[str] = Field(default_factory=list)
    capabilities_out_of_scope: list[str] = Field(default_factory=list)
    apis_consumed: list[str] = Field(default_factory=list)
    apis_provided: list[str] = Field(default_factory=list)
    data_owned: list[str] = Field(default_factory=list)
    tests_planned: list[str] = Field(default_factory=list)


class DatabaseChangeProposal(AgentOutput):
    """WF-06 output: schema/migration proposal with recovery plan."""

    artifact_type: Literal["database_change_proposal"] = "database_change_proposal"
    service_name: str = ""
    change_type: str = ""
    tenant_isolation_preserved: bool = True
    migration_plan: list[str] = Field(default_factory=list)
    recovery_plan: list[str] = Field(default_factory=list)
    data_risk: str = "none"  # none | low | high
    approvals_required: list[str] = Field(default_factory=list)


class EndpointSpec(BaseModel):
    """One endpoint of an API contract."""

    model_config = ConfigDict(extra="forbid")

    method: str = ""
    path: str = ""
    auth_required: bool = True
    idempotent: bool = False
    request_schema_ref: str | None = None
    response_schema_ref: str | None = None
    error_codes: list[str] = Field(default_factory=list)


class ApiContract(AgentOutput):
    """WF-01/WF-08 output: versioned service interface contract."""

    artifact_type: Literal["api_contract"] = "api_contract"
    service_name: str = ""
    contract_version: str = "1.0"
    endpoints: list[EndpointSpec] = Field(default_factory=list)
    event_schemas: list[str] = Field(default_factory=list)
    breaking: bool = False


class CodeChangeSummary(AgentOutput):
    """WF-02/WF-03 output: exactly what was changed and verified."""

    artifact_type: Literal["code_change_summary"] = "code_change_summary"
    files_changed: list[FileChange] = Field(default_factory=list)
    test_results: list[TestRunResult] = Field(default_factory=list)
    tenant_and_auth_checked: bool = False
    docs_updated: bool = False


class TestPlan(AgentOutput):
    """WF-01/WF-02 input: planned verification coverage."""

    artifact_type: Literal["test_plan"] = "test_plan"
    test_scope: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(default_factory=list)
    acceptance_to_test: list[AcceptanceVerdict] = Field(default_factory=list)


class TestReport(AgentOutput):
    """WF-02/WF-03 output: actual evidence from executed tests."""

    artifact_type: Literal["test_report"] = "test_report"
    test_runs: list[TestRunResult] = Field(default_factory=list)
    passed: int = 0
    failed: int = 0
    blocked: int = 0
    not_run: int = 0
    defect_ids: list[str] = Field(default_factory=list)
    residual_risk: str = ""
    stage_id: str | None = None
    agent_id: str | None = None
    produced_at: datetime = Field(default_factory=now_utc)
    title: str
    summary: str
    source_document_refs: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)

    @field_validator("title", "summary")
    @classmethod
    def _non_empty(cls, value: str, info) -> str:
        if not value.strip():
            raise ValueError(f"{info.field_name} must not be empty")
        return value.strip()

    @field_validator("task_id")
    @classmethod
    def _task_id_non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("task_id must not be empty")
        return value.strip()
class SecurityFinding(BaseModel):
    """One structured security finding (Workflow V1.0 section 12)."""

    model_config = ConfigDict(extra="forbid")

    finding_id: str = ""
    severity: str = "medium"  # critical | high | medium | low | info
    component: str = ""
    description: str = ""
    impact: str = ""
    evidence: str = ""
    recommended_remediation: str = ""
    owner: str = ""
    status: str = "open"
    retest_result: str | None = None


class SecurityReview(AgentOutput):
    """WF-07 output: independent security and privacy assessment."""

    artifact_type: Literal["security_review"] = "security_review"
    scope: list[str] = Field(default_factory=list)
    findings: list[SecurityFinding] = Field(default_factory=list)
    tenant_isolation_assessed: bool = False
    authz_assessed: bool = False
    secrets_assessed: bool = False
    residual_risk: list[str] = Field(default_factory=list)


class ReleaseReadinessReport(AgentOutput):
    """WF-09 output: the release package and evidence set."""

    artifact_type: Literal["release_readiness_report"] = "release_readiness_report"
    target_version: str = ""
    commits_included: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)
    approvals_obtained: list[str] = Field(default_factory=list)
    rollback_plan: list[str] = Field(default_factory=list)
    deployment_checklist: list[str] = Field(default_factory=list)
    release_notes: str = ""
    deployment_authorized: bool = False  # stays False until human approval


class DocumentationUpdateReport(AgentOutput):
    """WF-10 output: documentation change summary."""

    artifact_type: Literal["documentation_update_report"] = "documentation_update_report"
    updated_docs: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    links_validated: bool = False
    gaps_found: list[str] = Field(default_factory=list)


class ArchitectureDecisionRequest(AgentOutput):
    """WF-05 output: a decision request for the human project owner."""

    artifact_type: Literal["architecture_decision_request"] = "architecture_decision_request"
    problem_statement: str = ""
    constraints: list[str] = Field(default_factory=list)
    options_analysis: list[str] = Field(default_factory=list)
    recommended_option: str = ""
    affected_services: list[str] = Field(default_factory=list)
    requires_approval: bool = True


# Mapping of artifact kind -> model, used for strict validation and routing.
ARTIFACT_MODELS: dict[ArtifactKind, type[AgentOutput]] = {
    ArtifactKind.REQUIREMENT_ANALYSIS: RequirementAnalysis,
    ArtifactKind.ARCHITECTURE_PROPOSAL: ArchitectureProposal,
    ArtifactKind.SERVICE_IMPLEMENTATION_PLAN: ServiceImplementationPlan,
    ArtifactKind.DATABASE_CHANGE_PROPOSAL: DatabaseChangeProposal,
    ArtifactKind.API_CONTRACT: ApiContract,
    ArtifactKind.CODE_CHANGE_SUMMARY: CodeChangeSummary,
    ArtifactKind.TEST_PLAN: TestPlan,
    ArtifactKind.TEST_REPORT: TestReport,
    ArtifactKind.SECURITY_REVIEW: SecurityReview,
    ArtifactKind.RELEASE_READINESS_REPORT: ReleaseReadinessReport,
    ArtifactKind.DOCUMENTATION_UPDATE_REPORT: DocumentationUpdateReport,
    ArtifactKind.ARCHITECTURE_DECISION_REQUEST: ArchitectureDecisionRequest,
}


def validate_output(artifact: AgentOutput) -> CheckResult:
    """Validate an agent output against its declared contract.

    A passing check means the *structure* is credible; the workflow engine
    still verifies evidence paths and runs tests before accepting a stage.
    """
    from amsdp_ai_factory.contracts.common import (
        CheckResult,
        Severity,
        ValidationIssue,
    )

    issues: list[ValidationIssue] = []
    if not isinstance(artifact, AgentOutput):
        return CheckResult(
            name="output_contract",
            ok=False,
            issues=[
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="not_an_agent_output",
                    message=f"expected an AgentOutput instance, got {type(artifact).__name__}",
                    source="contracts.outputs",
                )
            ],
        )
    expected = ARTIFACT_MODELS.get(ArtifactKind(artifact.artifact_type))
    if expected is None:
        issues.append(
            ValidationIssue(
                severity=Severity.ERROR,
                code="unknown_artifact_type",
                message=f"unknown artifact type {artifact.artifact_type!r}",
                source="contracts.outputs",
            )
        )
    elif type(artifact) is not expected:
        issues.append(
            ValidationIssue(
                severity=Severity.ERROR,
                code="artifact_type_mismatch",
                message=(
                    f"instance {type(artifact).__name__} does not match declared "
                    f"artifact type {artifact.artifact_type!r}"
                ),
                source="contracts.outputs",
            )
        )
    if not artifact.title or not artifact.summary:
        issues.append(
            ValidationIssue(
                severity=Severity.ERROR,
                code="missing_title_or_summary",
                message="artifact title and summary are required",
                source="contracts.outputs",
            )
        )
    for evidence in artifact.evidence:
        if not evidence.path.strip():
            issues.append(
                ValidationIssue(
                    severity=Severity.ERROR,
                    code="evidence_missing_path",
                    message="every evidence reference must carry a path",
                    source="contracts.outputs",
                )
            )
    return CheckResult(name="output_contract", ok=not issues, issues=issues)