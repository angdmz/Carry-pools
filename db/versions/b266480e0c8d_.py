"""empty message

Revision ID: b266480e0c8d
Revises: 659c35d2cf6c
Create Date: 2023-04-08 13:00:23.969588

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b266480e0c8d'
down_revision = '659c35d2cf6c'
branch_labels = None
depends_on = None

enum_participant_type = sa.Enum('NATURAL_PERSON', 'GOVERNMENT_ORGANISM', 'COMPANY', 'ACADEMIC', name='enum_participant_type')

def upgrade() -> None:
    op.execute(f"CREATE TYPE {enum_participant_type.name} AS ENUM ('NATURAL_PERSON', 'GOVERNMENT_ORGANISM', 'COMPANY', 'ACADEMIC')")
    op.add_column('participants', sa.Column('type', enum_participant_type, nullable=True))

def downgrade() -> None:
    op.drop_column('participants', 'type')
    op.execute(f'DROP TYPE {enum_participant_type.name}')
