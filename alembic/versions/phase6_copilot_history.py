"""phase6_copilot_history

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-16 00:00:00.000000

Optional table for persisting copilot conversation history.
The copilot works without this table — history is passed from the
frontend on each request. This table enables future session replay
and audit features.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'copilot_sessions',
        sa.Column('id',         sa.Integer(),     autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(64),    nullable=False),
        sa.Column('role',       sa.String(20),    nullable=False),   # user | assistant
        sa.Column('content',    sa.Text(),        nullable=False),
        sa.Column('actions',    sa.JSON(),         nullable=True),
        sa.Column('created_at', sa.DateTime(),    nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_copilot_sessions_session_id', 'copilot_sessions', ['session_id'], unique=False)
    op.create_index('ix_copilot_sessions_created_at', 'copilot_sessions', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_copilot_sessions_created_at', table_name='copilot_sessions')
    op.drop_index('ix_copilot_sessions_session_id',  table_name='copilot_sessions')
    op.drop_table('copilot_sessions')
