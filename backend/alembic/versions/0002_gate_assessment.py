"""gate assessment tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-01
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

STR = sa.String(64)


def upgrade() -> None:
    # Add current_gate to projects
    op.add_column("projects", sa.Column("current_gate", sa.String(8), server_default="QG0"))

    # Gate check definitions (seeded from Excel, read-only at runtime)
    op.create_table(
        "assessment_gate_definitions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("gate_id", sa.String(8), nullable=False),
        sa.Column("gate_name", sa.String(128), nullable=False),
        sa.Column("lifecycle_phase", sa.String(128), nullable=False),
        sa.Column("expected_maturity", sa.String(128), nullable=False),
        sa.Column("characteristic", sa.String(128), nullable=False),
        sa.Column("subcharacteristic", sa.String(128), nullable=False),
        sa.Column("subchar_id", sa.String(64),
                  sa.ForeignKey("common_subcharacteristics.id"), nullable=True),
        sa.Column("what_to_check", sa.Text, nullable=False),
        sa.Column("pass_criteria", sa.Text, nullable=False),
        sa.Column("required_evidence", sa.Text),
        sa.Column("review_method", sa.String(256)),
        sa.Column("blocking_level", sa.String(4), nullable=False),
        sa.Column("responsible_role", sa.String(128)),
        sa.Column("display_order", sa.Integer, server_default="0"),
    )
    op.create_index("idx_agd_gate", "assessment_gate_definitions", ["gate_id"])
    op.create_index("idx_agd_subchar_name", "assessment_gate_definitions", ["subcharacteristic"])

    # Assessment runs (one per gate execution)
    op.create_table(
        "assessment_runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("project_id", sa.String(36),
                  sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("gate_id", sa.String(8), nullable=False),
        sa.Column("gate_name", sa.String(128), nullable=False),
        sa.Column("run_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="'In Progress'"),
        sa.Column("source", sa.String(32), nullable=False, server_default="'manual'"),
        sa.Column("ai_agent_version", sa.String(64)),
        sa.Column("overall_result", sa.String(32)),
        sa.Column("p0_fail_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("p1_fail_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("p2_fail_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("executed_by", sa.String(128)),
        sa.Column("executed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("project_id", "gate_id", "run_number",
                            name="uq_run_project_gate_number"),
    )
    op.create_index("idx_ar_project_gate", "assessment_runs", ["project_id", "gate_id"])

    # Individual check results within a run
    op.create_table(
        "assessment_check_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36),
                  sa.ForeignKey("assessment_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("definition_id", sa.String(36),
                  sa.ForeignKey("assessment_gate_definitions.id"), nullable=False),
        sa.Column("result", sa.String(32), nullable=False, server_default="'Open'"),
        sa.Column("findings", sa.Text),
        sa.Column("evidence_ref", sa.Text),
        sa.Column("ai_confidence", sa.Float),
        sa.Column("ai_rationale", sa.Text),
        sa.Column("reviewed_by", sa.String(128)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("run_id", "definition_id", name="uq_result_run_def"),
    )
    op.create_index("idx_acr_run", "assessment_check_results", ["run_id"])
    op.create_index("idx_acr_result", "assessment_check_results", ["run_id", "result"])


def downgrade() -> None:
    op.drop_table("assessment_check_results")
    op.drop_table("assessment_runs")
    op.drop_table("assessment_gate_definitions")
    op.drop_column("projects", "current_gate")
