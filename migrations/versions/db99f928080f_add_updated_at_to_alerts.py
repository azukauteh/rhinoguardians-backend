"""add updated_at to alerts

Revision ID: db99f928080f
Revises: 1a4c566c4e37
Create Date: 2025-11-20 14:24:59.399929

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'db99f928080f'
down_revision = '1a4c566c4e37'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.add_column(
            sa.Column("updated_at", sa.DateTime(), nullable=True,
                      comment="When the alert was last updated")
        )


def downgrade():
    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_column("updated_at")
