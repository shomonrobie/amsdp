"""Structured output contract tests."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from amsdp_ai_factory.contracts.outputs import (
    ARTIFACT_MODELS,
    ArtifactKind,
    CodeChangeSummary,
    DocumentationUpdateReport,
    EvidenceRef,
    FileChange,
    RequirementAnalysis,
    SecurityFinding,
    SecurityReview,
    TestRunResult,
    validate_output,
)
from amsdp_ai_factory.tasks.models import now_utc


class ArtifactTypeTests(unittest.TestCase):
    def test_all_twelve_kinds_registered(self):
        self.assertEqual(len(ARTIFACT_MODELS), 12)
        expected = [
            "requirement_analysis",
            "architecture_proposal",
            "service_implementation_plan",
            "database_change_proposal",
            "api_contract",
            "code_change_summary",
            "test_plan",
            "test_report",
            "security_review",
            "release_readiness_report",
            "documentation_update_report",
            "architecture_decision_request",
        ]
        self.assertEqual(
            sorted(kind.value for kind in ARTIFACT_MODELS), sorted(expected)
        )

    def test_literal_artifact_type_is_enforced(self):
        with self.assertRaises(ValidationError):
            RequirementAnalysis(
                task_id="AMSDP-000001",
                title="x",
                summary="y",
                artifact_type="something_else",
            )


class ValidationTests(unittest.TestCase):
    def _base(self, **kwargs):
        kwargs.setdefault("task_id", "AMSDP-000001")
        kwargs.setdefault("title", "Synthetic requirement analysis")
        kwargs.setdefault("summary", "Synthetic evidence only.")
        return kwargs

    def test_valid_requirement_analysis_passes(self):
        artifact = RequirementAnalysis(
            **self._base(user_stories=["As a receptionist..."]),
        )
        check = validate_output(artifact)
        self.assertTrue(check.ok)
        self.assertEqual(check.name, "output_contract")

    def test_evidence_missing_path_fails(self):
        artifact = RequirementAnalysis(
            **self._base(evidence=[EvidenceRef(kind="artifact", path="")]),
        )
        check = validate_output(artifact)
        self.assertFalse(check.ok)
        self.assertTrue(
            any(i.code == "evidence_missing_path" for i in check.issues)
        )

    def test_empty_title_fails_model_validation(self):
        with self.assertRaises(ValidationError):
            RequirementAnalysis(task_id="AMSDP-000001", title="  ", summary="x")

    def test_wrong_model_class_detected(self):
        artifact = SecurityReview(
            task_id="AMSDP-000001", title="t", summary="s", artifact_type="security_review"
        )
        artifact.artifact_type = "requirement_analysis"  # force mismatch
        check = validate_output(artifact)
        self.assertFalse(check.ok)
        self.assertTrue(any(i.code == "artifact_type_mismatch" for i in check.issues))

    def test_security_review_structure(self):
        artifact = SecurityReview(
            task_id="AMSDP-000001",
            title="Auth review",
            summary="Synthetic findings.",
            tenant_isolation_assessed=True,
            findings=[
                SecurityFinding(
                    finding_id="SEC-001",
                    severity="high",
                    component="patient-service",
                    description="cross-tenant read suspected",
                    impact="data exposure",
                    recommended_remediation="scope queries by org_id",
                    status="open",
                )
            ],
        )
        check = validate_output(artifact)
        self.assertTrue(check.ok)
        self.assertEqual(artifact.findings[0].severity, "high")

    def test_code_change_summary_structure(self):
        artifact = CodeChangeSummary(
            task_id="AMSDP-000001",
            title="Queue reorder handler",
            summary="Synthetic summary.",
            files_changed=[
                FileChange(
                    path="app/queue/reorder.py", change_type="modified", lines_changed=41
                )
            ],
            test_results=[
                TestRunResult(
                    command="python -m unittest queue_tests",
                    exit_code=0,
                    outcome="passed",
                    summary="12 passed",
                )
            ],
            tenant_and_auth_checked=True,
            docs_updated=True,
        )
        check = validate_output(artifact)
        self.assertTrue(check.ok)
        self.assertEqual(artifact.files_changed[0].lines_changed, 41)

    def test_unknown_field_rejected(self):
        with self.assertRaises(ValidationError):
            DocumentationUpdateReport(
                task_id="AMSDP-000001",
                title="t",
                summary="s",
                not_a_field="nope",
            )


if __name__ == "__main__":
    unittest.main()