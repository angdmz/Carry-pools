"""empty message

Revision ID: a51f98dea466
Revises: 
Create Date: 2023-12-02 02:25:38.711604

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a51f98dea466'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:

    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public')

    op.create_table('carry_pools',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('basis_points', sa.DECIMAL(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('funds',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('milestones',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('participants',
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.Column('date_of_verification', sa.TIMESTAMP(timezone=True), nullable=True),
    sa.Column('type', sa.Enum('NATURAL_PERSON', 'GOVERNMENT_ORGANISM', 'COMPANY', 'ACADEMIC', name='enum_participant_type'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('time_based_vesting_schedules',
    sa.Column('period_duration', postgresql.DATERANGE(), nullable=False),
    sa.Column('period_vesting_percentage', sa.DECIMAL(), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('academics',
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('education_level', sa.Enum('SCHOOL', 'HIGHSCHOOL', 'UNIVERSITY', name='enum_academic_type'), nullable=False),
    sa.Column('participant_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('companies',
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('cuit', sa.String(), nullable=False),
    sa.Column('participant_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('deals',
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('fund_id', sa.UUID(), nullable=False),
    sa.Column('capital_deployed', sa.DECIMAL(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['fund_id'], ['funds.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('fund_carry_plans',
    sa.Column('fund_id', sa.UUID(), nullable=False),
    sa.Column('carry_pool_id', sa.UUID(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['carry_pool_id'], ['carry_pools.id'], ),
    sa.ForeignKeyConstraint(['fund_id'], ['funds.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('fund_id', 'carry_pool_id', name='fund_id_carry_pool_id_uc')
    )
    op.create_table('government_organisms',
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('sector', sa.String(), nullable=False),
    sa.Column('participant_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('natural_persons',
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('first_name', sa.String(), nullable=False),
    sa.Column('last_name', sa.String(), nullable=False),
    sa.Column('participant_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['participant_id'], ['participants.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('identifications',
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('type', sa.Enum('DNI', 'CUIT', 'LE', name='enum_identification_type'), nullable=False),
    sa.Column('value', sa.String(), nullable=False),
    sa.Column('person_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['person_id'], ['natural_persons.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('vesting_schedules',
    sa.Column('company_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('milestone_vesting_schedules',
    sa.Column('vesting_schedule_id', sa.UUID(), nullable=False),
    sa.Column('milestone_id', sa.UUID(), nullable=False),
    sa.Column('milestone_vesting_percentage', sa.DECIMAL(), nullable=False),
    sa.Column('id', sa.UUID(), server_default=sa.text('uuid_generate_v4()'), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
    sa.ForeignKeyConstraint(['milestone_id'], ['milestones.id'], ),
    sa.ForeignKeyConstraint(['vesting_schedule_id'], ['vesting_schedules.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('vesting_schedule_id', 'milestone_id', name='vesting_schedule_id_milestone_id_uc')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('milestone_vesting_schedules')
    op.drop_table('vesting_schedules')
    op.drop_table('identifications')
    op.drop_table('natural_persons')
    op.drop_table('government_organisms')
    op.drop_table('fund_carry_plans')
    op.drop_table('deals')
    op.drop_table('companies')
    op.drop_table('academics')
    op.drop_table('time_based_vesting_schedules')
    op.drop_table('participants')
    op.drop_table('milestones')
    op.drop_table('funds')
    op.drop_table('carry_pools')
    # ### end Alembic commands ###
