"""The ten approved workflows (AI Development Workflow V1.0 sections 6-15)."""

from __future__ import annotations

from amsdp_ai_factory.workflows.definitions.wf01_requirement_to_design import WF01
from amsdp_ai_factory.workflows.definitions.wf02_service_implementation import WF02
from amsdp_ai_factory.workflows.definitions.wf03_frontend_delivery import WF03
from amsdp_ai_factory.workflows.definitions.wf04_defect_resolution import WF04
from amsdp_ai_factory.workflows.definitions.wf05_architecture_decision import WF05
from amsdp_ai_factory.workflows.definitions.wf06_database_change import WF06
from amsdp_ai_factory.workflows.definitions.wf07_security_review import WF07
from amsdp_ai_factory.workflows.definitions.wf08_cross_service_integration import WF08
from amsdp_ai_factory.workflows.definitions.wf09_release_readiness import WF09
from amsdp_ai_factory.workflows.definitions.wf10_documentation_update import WF10
from amsdp_ai_factory.workflows.models import WorkflowDefinition

DEFAULT_WORKFLOWS: tuple[WorkflowDefinition, ...] = (
    WF01,
    WF02,
    WF03,
    WF04,
    WF05,
    WF06,
    WF07,
    WF08,
    WF09,
    WF10,
)

WORKFLOW_INDEX: dict[str, WorkflowDefinition] = {
    workflow.workflow_id: workflow for workflow in DEFAULT_WORKFLOWS
}