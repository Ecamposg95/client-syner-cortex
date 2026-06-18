"""add RACI matrix tables (interactive RACI module)

Revision ID: b7f3a9c1d2e4
Revises: 27fe7022dc62
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7f3a9c1d2e4'
down_revision: Union[str, Sequence[str], None] = '27fe7022dc62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'raci_matrices',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_raci_matrices_id'), 'raci_matrices', ['id'], unique=False)
    op.create_index(op.f('ix_raci_matrices_organization_id'), 'raci_matrices', ['organization_id'], unique=False)

    op.create_table(
        'raci_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('matrix_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('charter_decides', sa.Text(), nullable=True),
        sa.Column('charter_blocks', sa.Text(), nullable=True),
        sa.Column('charter_escalates', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['matrix_id'], ['raci_matrices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_raci_roles_id'), 'raci_roles', ['id'], unique=False)
    op.create_index(op.f('ix_raci_roles_matrix_id'), 'raci_roles', ['matrix_id'], unique=False)

    op.create_table(
        'raci_processes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('matrix_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('order', sa.Integer(), nullable=False),
        sa.Column('evidence_min', sa.Text(), nullable=True),
        sa.Column('handoff_owner', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['matrix_id'], ['raci_matrices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_raci_processes_id'), 'raci_processes', ['id'], unique=False)
    op.create_index(op.f('ix_raci_processes_matrix_id'), 'raci_processes', ['matrix_id'], unique=False)

    op.create_table(
        'raci_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('matrix_id', sa.Integer(), nullable=False),
        sa.Column('process_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.Enum('R', 'A', 'C', 'I', name='racivalue'), nullable=False),
        sa.ForeignKeyConstraint(['matrix_id'], ['raci_matrices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['process_id'], ['raci_processes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['raci_roles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('process_id', 'role_id', 'value', name='uq_raci_cell_value'),
    )
    op.create_index(op.f('ix_raci_assignments_id'), 'raci_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_raci_assignments_matrix_id'), 'raci_assignments', ['matrix_id'], unique=False)
    op.create_index(op.f('ix_raci_assignments_process_id'), 'raci_assignments', ['process_id'], unique=False)
    op.create_index(op.f('ix_raci_assignments_role_id'), 'raci_assignments', ['role_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('raci_assignments')
    op.drop_table('raci_processes')
    op.drop_table('raci_roles')
    op.drop_table('raci_matrices')
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute('DROP TYPE IF EXISTS racivalue')
