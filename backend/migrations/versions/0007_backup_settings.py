"""backup settings

Revision ID: 0007_backup_settings
Revises: 0006_system_settings
Create Date: 2026-10-06
"""
from alembic import op
import sqlalchemy as sa

revision="0007_backup_settings"
down_revision="0006_system_settings"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("system_settings",sa.Column("backup_enabled",sa.Boolean(),nullable=False,server_default=sa.false()))
    op.add_column("system_settings",sa.Column("backup_provider",sa.String(length=20),nullable=False,server_default="GDRIVE"))
    op.add_column("system_settings",sa.Column("backup_remote_name",sa.String(length=120),nullable=False,server_default=""))
    op.add_column("system_settings",sa.Column("backup_folder",sa.String(length=255),nullable=False,server_default="SGV-EPMVS/backups"))
    op.add_column("system_settings",sa.Column("backup_time",sa.String(length=5),nullable=False,server_default="02:00"))
    op.add_column("system_settings",sa.Column("backup_keep_last",sa.Integer(),nullable=False,server_default="2"))
    op.add_column("system_settings",sa.Column("backup_run_requested",sa.Boolean(),nullable=False,server_default=sa.false()))
    op.add_column("system_settings",sa.Column("backup_last_run",sa.DateTime(timezone=True),nullable=True))
    op.add_column("system_settings",sa.Column("backup_last_status",sa.String(length=20),nullable=False,server_default="NEVER"))
    op.add_column("system_settings",sa.Column("backup_last_filename",sa.String(length=255),nullable=True))
    op.add_column("system_settings",sa.Column("backup_last_error",sa.Text(),nullable=True))

def downgrade():
    for name in [
        "backup_last_error","backup_last_filename","backup_last_status","backup_last_run",
        "backup_run_requested","backup_keep_last","backup_time","backup_folder",
        "backup_remote_name","backup_provider","backup_enabled"
    ]:
        op.drop_column("system_settings",name)
