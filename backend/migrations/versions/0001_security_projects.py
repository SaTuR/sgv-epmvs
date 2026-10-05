"""security and project base

Revision ID: 0001_security_projects
Revises:
Create Date: 2026-10-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_security_projects"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(120), nullable=False), sa.Column("name", sa.String(160), nullable=False),
        sa.UniqueConstraint("code"))
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)
    op.create_table("roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("name", sa.String(80), nullable=False),
        sa.Column("description", sa.String(255)), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("name"))
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
    op.create_table("users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("identification", sa.String(30)),
        sa.Column("first_name", sa.String(120), nullable=False), sa.Column("last_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(180), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("identification"), sa.UniqueConstraint("email"))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("user_roles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("role_permissions",
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("permission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("name"))
    op.create_index("ix_projects_name", "projects", ["name"], unique=True)
    op.create_table("project_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False), sa.Column("description", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_index("ix_project_stages_project_id", "project_stages", ["project_id"])

def downgrade():
    op.drop_table("project_stages"); op.drop_table("projects"); op.drop_table("role_permissions"); op.drop_table("user_roles")
    op.drop_table("users"); op.drop_table("roles"); op.drop_table("permissions")
