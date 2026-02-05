"""initial
Revision ID: 0001_initial
Revises:
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("name_ar", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("student_id", sa.String(length=50), nullable=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("student_id"),
    )

    op.create_table(
        "skill",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name_ar", sa.String(length=200), nullable=False),
        sa.Column("name_en", sa.String(length=200), nullable=True),
        sa.Column("description_ar", sa.Text(), nullable=True),
        sa.Column("description_en", sa.Text(), nullable=True),
        sa.Column("order", sa.Integer(), nullable=True),
        sa.Column("pass_threshold", sa.Integer(), nullable=True),
        sa.Column("time_limit_min", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "student_skill_status",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skill.id"), nullable=False),
        sa.Column("unlocked", sa.Boolean(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=True),
        sa.Column("extra_attempt_week", sa.String(length=12), nullable=True),
        sa.UniqueConstraint("student_id", "skill_id", name="uq_student_skill"),
    )

    op.create_table(
        "media",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("mime", sa.String(length=100), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("uploaded_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "question",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skill.id"), nullable=False),
        sa.Column("qtype", sa.String(length=50), nullable=False),
        sa.Column("prompt_ar", sa.Text(), nullable=False),
        sa.Column("prompt_en", sa.Text(), nullable=True),
        sa.Column("options_json", sa.JSON(), nullable=True),
        sa.Column("correct_json", sa.JSON(), nullable=True),
        sa.Column("media_json", sa.JSON(), nullable=True),
        sa.Column("meta_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "attempt",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skill.id"), nullable=False),
        sa.Column("week_key", sa.String(length=12), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("time_seconds", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("answers_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("student_id", "skill_id", "week_key", name="uq_attempt_week"),
    )

    op.create_table(
        "report",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("attempt_id", sa.Integer(), sa.ForeignKey("attempt.id"), nullable=False, unique=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "remediation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skill.id"), nullable=False),
        sa.Column("notes_ar", sa.Text(), nullable=True),
        sa.Column("notes_en", sa.Text(), nullable=True),
        sa.Column("file_media_id", sa.Integer(), sa.ForeignKey("media.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "import_batch",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skill.id"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "import_item",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("batch_id", sa.Integer(), sa.ForeignKey("import_batch.id"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("suggested_type", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

def downgrade():
    op.drop_table("import_item")
    op.drop_table("import_batch")
    op.drop_table("remediation")
    op.drop_table("report")
    op.drop_table("attempt")
    op.drop_table("question")
    op.drop_table("media")
    op.drop_table("student_skill_status")
    op.drop_table("skill")
    op.drop_table("user")
