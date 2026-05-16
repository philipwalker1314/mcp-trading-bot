"""phase5_strategy_configs

Revision ID: a1b2c3d4e5f6
Revises: 5b740c8edfd8
Create Date: 2026-05-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5b740c8edfd8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'strategy_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='false'),

        # Execution config
        sa.Column('timeframe', sa.String(length=10), nullable=False, server_default='1m'),
        sa.Column('symbols', sa.JSON(), nullable=False),          # list[str]

        # Risk config
        sa.Column('stop_loss_pct', sa.Float(), nullable=False, server_default='0.02'),
        sa.Column('take_profit_pct', sa.Float(), nullable=False, server_default='0.04'),
        sa.Column('trailing_stop_pct', sa.Float(), nullable=True),

        # Signal logic — stored as JSON rule tree
        sa.Column('entry_rules', sa.JSON(), nullable=False),      # list[Rule]
        sa.Column('exit_rules', sa.JSON(), nullable=True),        # list[Rule] | null

        # Indicator config — which indicators to compute and with what params
        sa.Column('indicators', sa.JSON(), nullable=False),       # list[IndicatorConfig]

        # Audit
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_by', sa.String(length=120), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_strategy_configs_name'),
    )
    op.create_index('ix_strategy_configs_name', 'strategy_configs', ['name'], unique=False)
    op.create_index('ix_strategy_configs_enabled', 'strategy_configs', ['enabled'], unique=False)

    # Version history table — immutable append-only log
    op.create_table(
        'strategy_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('strategy_id', sa.Integer(), sa.ForeignKey('strategy_configs.id'), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('snapshot', sa.JSON(), nullable=False),         # full strategy config at this version
        sa.Column('change_summary', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_strategy_versions_strategy_id', 'strategy_versions', ['strategy_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_strategy_versions_strategy_id', table_name='strategy_versions')
    op.drop_table('strategy_versions')
    op.drop_index('ix_strategy_configs_enabled', table_name='strategy_configs')
    op.drop_index('ix_strategy_configs_name', table_name='strategy_configs')
    op.drop_table('strategy_configs')
