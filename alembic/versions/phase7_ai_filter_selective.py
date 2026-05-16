"""phase7_ai_filter_selective

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-16 00:00:00.000000

Adds two columns to strategy_configs:
  ai_validation_required  BOOLEAN NOT NULL DEFAULT TRUE
  confidence_threshold    FLOAT   NOT NULL DEFAULT 0.75

No data migration needed — defaults are safe for all existing rows.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'strategy_configs',
        sa.Column(
            'ai_validation_required',
            sa.Boolean(),
            nullable=False,
            server_default='true',
        )
    )
    op.add_column(
        'strategy_configs',
        sa.Column(
            'confidence_threshold',
            sa.Float(),
            nullable=False,
            server_default='0.75',
        )
    )


def downgrade() -> None:
    op.drop_column('strategy_configs', 'confidence_threshold')
    op.drop_column('strategy_configs', 'ai_validation_required')
