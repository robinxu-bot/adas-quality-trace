"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# Use String columns for all enum-like fields.
# PostgreSQL native enums are intentionally avoided here because SQLAlchemy's
# Alembic integration creates them both in e.create() AND in create_table(),
# causing DuplicateObjectError on any retry. String columns are simpler and
# equally functional for our read patterns.
STR = sa.String(64)


def upgrade() -> None:
    # --- Common model tables (read-only after seed) ---
    op.create_table(
        "common_characteristics",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
    )

    op.create_table(
        "common_subcharacteristics",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("characteristic_id", sa.String(64),
                  sa.ForeignKey("common_characteristics.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("architecture_element", sa.String(128)),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("idx_subchar_characteristic", "common_subcharacteristics", ["characteristic_id"])

    op.create_table(
        "common_aspect_mappings",
        sa.Column("subchar_id", sa.String(64),
                  sa.ForeignKey("common_subcharacteristics.id"), primary_key=True),
        sa.Column("aspect", STR, primary_key=True),
    )

    op.create_table(
        "product_line_recommendations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("product_line", STR, nullable=False),
        sa.Column("subchar_id", sa.String(64),
                  sa.ForeignKey("common_subcharacteristics.id"), nullable=False),
        sa.Column("recommended_applicability", STR, nullable=False),
        sa.Column("default_rationale", sa.Text),
        sa.UniqueConstraint("product_line", "subchar_id", name="uq_plrec_line_subchar"),
    )
    op.create_index("idx_plrec_product_line", "product_line_recommendations", ["product_line"])

    op.create_table(
        "product_line_recommendation_aspects",
        sa.Column("recommendation_id", sa.String(64),
                  sa.ForeignKey("product_line_recommendations.id"), primary_key=True),
        sa.Column("aspect", STR, primary_key=True),
    )

    # --- Projects ---
    op.create_table(
        "projects",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("product_type", sa.String(128), nullable=False),
        sa.Column("product_line", STR, nullable=False),
        sa.Column("phase", STR, nullable=False),
        sa.Column("system_boundary", sa.Text, nullable=False),
        sa.Column("assessment_target", sa.Text),
        sa.Column("customer", sa.String(256)),
        sa.Column("selected_aspects", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_projects_project_id", "projects", ["project_id"])

    op.create_table(
        "project_scope_decisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subchar_id", sa.String(64),
                  sa.ForeignKey("common_subcharacteristics.id"), nullable=False),
        sa.Column("applicability", STR, nullable=False),
        sa.Column("rationale", sa.Text),
        sa.Column("recommended_applicability", STR),
        sa.Column("recommendation_reason", sa.Text),
        sa.Column("selected_quality_aspects", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("manual_override", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("decision_owner", sa.String(128)),
        sa.Column("decision_date", sa.Date),
        sa.Column("review_status", STR, nullable=False, server_default="'Draft'"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "subchar_id", name="uq_scope_project_subchar"),
    )
    op.create_index("idx_scope_project", "project_scope_decisions", ["project_id"])

    op.create_table(
        "architecture_elements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("element_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_arch_project", "architecture_elements", ["project_id"])

    op.create_table(
        "software_modules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("architecture_element_id", sa.String(36),
                  sa.ForeignKey("architecture_elements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module_id", sa.String(64), nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_module_arch", "software_modules", ["architecture_element_id"])

    op.create_table(
        "quality_goals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("scope_decision_id", sa.String(36),
                  sa.ForeignKey("project_scope_decisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goal_id", sa.String(64), nullable=False),
        sa.Column("goal_text", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_goal_scope", "quality_goals", ["scope_decision_id"])

    op.create_table(
        "quality_requirements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("goal_id", sa.String(36),
                  sa.ForeignKey("quality_goals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("req_id", sa.String(64), nullable=False),
        sa.Column("requirement_text", sa.Text, nullable=False),
        sa.Column("scenario", sa.Text),
        sa.Column("applicable_aspects", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("architecture_element_id", sa.String(36)),
        sa.Column("risk_level", STR, nullable=False, server_default="'Low'"),
        sa.Column("evidence_status", STR, nullable=False, server_default="'Missing'"),
        sa.Column("owner", sa.String(128)),
        sa.Column("assessment_status", STR, nullable=False, server_default="'Draft'"),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_qreq_goal", "quality_requirements", ["goal_id"])

    op.create_table(
        "sub_quality_requirements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("req_id", sa.String(36),
                  sa.ForeignKey("quality_requirements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sub_req_id", sa.String(64), nullable=False),
        sa.Column("acceptance_criterion", sa.Text),
        sa.Column("verification_condition", sa.Text),
        sa.Column("input_condition", sa.Text),
        sa.Column("expected_output", sa.Text),
        sa.Column("measured_value", sa.String(256)),
        sa.Column("pass_fail_criterion", sa.Text),
        sa.Column("architecture_element_id", sa.String(36)),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_subreq_req", "sub_quality_requirements", ["req_id"])

    op.create_table(
        "test_cases",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("software_module_id", sa.String(36),
                  sa.ForeignKey("software_modules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sub_req_id", sa.String(36),
                  sa.ForeignKey("sub_quality_requirements.id")),
        sa.Column("tc_id", sa.String(64), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("test_objective", sa.Text),
        sa.Column("test_method", sa.String(128)),
        sa.Column("input_data", sa.Text),
        sa.Column("precondition", sa.Text),
        sa.Column("expected_result", sa.Text),
        sa.Column("pass_fail_criterion", sa.Text),
        sa.Column("evidence_link", sa.Text),
        sa.Column("automated", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("display_order", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_tc_module", "test_cases", ["software_module_id"])

    op.create_table(
        "test_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tc_id", sa.String(36),
                  sa.ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("result", STR, nullable=False, server_default="'Not run'"),
        sa.Column("actual_result", sa.Text),
        sa.Column("measured_value", sa.String(256)),
        sa.Column("deviation", sa.Text),
        sa.Column("conclusion", sa.Text),
        sa.Column("evidence_file", sa.Text),
        sa.Column("evidence_link", sa.Text),
        sa.Column("executed_at", sa.DateTime(timezone=True)),
        sa.Column("tester", sa.String(128)),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Forward-reference FKs
    op.create_foreign_key(
        "fk_qreq_arch", "quality_requirements",
        "architecture_elements", ["architecture_element_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_subreq_arch", "sub_quality_requirements",
        "architecture_elements", ["architecture_element_id"], ["id"]
    )

    # --- Risk, Evidence, Findings, Actions ---
    op.create_table(
        "risk_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("risk_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("quality_aspects", ARRAY(sa.String), nullable=False, server_default="{}"),
        sa.Column("severity", STR, nullable=False),
        sa.Column("likelihood", STR, nullable=False),
        sa.Column("risk_level", STR, nullable=False),
        sa.Column("status", STR, nullable=False, server_default="'Open'"),
        sa.Column("risk_reason", sa.Text),
        sa.Column("impact", sa.Text),
        sa.Column("mitigation_action", sa.Text),
        sa.Column("owner", sa.String(128)),
        sa.Column("due_date", sa.Date),
        sa.Column("target_milestone", sa.String(128)),
        sa.Column("related_subchar_id", sa.String(64),
                  sa.ForeignKey("common_subcharacteristics.id")),
        sa.Column("related_req_id", sa.String(36),
                  sa.ForeignKey("quality_requirements.id")),
        sa.Column("related_test_result_id", sa.String(36),
                  sa.ForeignKey("test_results.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "risk_id", name="uq_risk_project_risk_id"),
    )
    op.create_index("idx_risk_project", "risk_items", ["project_id"])
    op.create_index("idx_risk_status", "risk_items", ["project_id", "status"])

    op.create_table(
        "evidence_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("evidence_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("evidence_type", sa.String(128)),
        sa.Column("status", STR, nullable=False, server_default="'Missing'"),
        sa.Column("source_link", sa.Text),
        sa.Column("related_req_id", sa.String(36),
                  sa.ForeignKey("quality_requirements.id")),
        sa.Column("related_test_result_id", sa.String(36),
                  sa.ForeignKey("test_results.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_evidence_project", "evidence_items", ["project_id"])

    op.create_table(
        "assessment_findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("finding_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("finding_type", sa.String(128)),
        sa.Column("severity", STR, nullable=False, server_default="'Low'"),
        sa.Column("status", STR, nullable=False, server_default="'Open'"),
        sa.Column("related_subchar_id", sa.String(64),
                  sa.ForeignKey("common_subcharacteristics.id")),
        sa.Column("related_req_id", sa.String(36),
                  sa.ForeignKey("quality_requirements.id")),
        sa.Column("owner", sa.String(128)),
        sa.Column("due_date", sa.Date),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_finding_project", "assessment_findings", ["project_id"])

    op.create_table(
        "action_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_id", sa.String(64), nullable=False),
        sa.Column("title", sa.String(256), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("status", STR, nullable=False, server_default="'Open'"),
        sa.Column("priority", STR, nullable=False, server_default="'Medium'"),
        sa.Column("owner", sa.String(128)),
        sa.Column("due_date", sa.Date),
        sa.Column("target_milestone", sa.String(128)),
        sa.Column("related_finding_id", sa.String(36),
                  sa.ForeignKey("assessment_findings.id")),
        sa.Column("related_risk_id", sa.String(36),
                  sa.ForeignKey("risk_items.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_action_project", "action_items", ["project_id"])


def downgrade() -> None:
    for table in [
        "action_items", "assessment_findings", "evidence_items", "risk_items",
        "test_results", "test_cases", "sub_quality_requirements", "quality_requirements",
        "quality_goals", "software_modules", "architecture_elements",
        "project_scope_decisions", "projects",
        "product_line_recommendation_aspects", "product_line_recommendations",
        "common_aspect_mappings", "common_subcharacteristics", "common_characteristics",
    ]:
        op.drop_table(table)
