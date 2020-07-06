"""empty message

Revision ID: 0041 update email providers
Revises: 0040 add email providers
Create Date: 2020-06-29 18:56:05.135216

"""

# revision identifiers, used by Alembic.
revision = '0041 update email providers'
down_revision = '0040 add email providers'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('email_providers', sa.Column('hourly_limit', sa.Integer(), nullable=True))
    op.add_column('email_providers', sa.Column('data_map', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('email_providers', sa.Column('headers', sa.Boolean(), nullable=True))
    op.add_column('email_providers', sa.Column('as_json', sa.Boolean(), nullable=True))
    op.drop_column('email_providers', 'data_struct')
    op.add_column('email_to_member', sa.Column('email_provider_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'email_to_member', 'email_providers', ['email_provider_id'], ['id'])
    op.drop_column('email_to_member', 'emailed_by')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_constraint(None, 'email_to_member', type_='foreignkey')
    op.drop_column('email_to_member', 'email_provider_id')
    op.add_column('email_providers', sa.Column('data_struct', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_column('email_providers', 'hourly_limit')
    op.drop_column('email_providers', 'data_map')
    op.drop_column('email_providers', 'headers')
    op.drop_column('email_providers', 'as_json')
    op.add_column('email_to_member', sa.Column('emailed_by', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
