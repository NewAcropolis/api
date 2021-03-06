"""empty message

Revision ID: 0047 add smtp
Revises: 0046 remove long description
Create Date: 2020-11-08 01:28:28.386704

"""

# revision identifiers, used by Alembic.
revision = '0047 add smtp'
down_revision = '0046 remove long description'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('email_providers', sa.Column('smtp_password', sa.String(), nullable=True))
    op.add_column('email_providers', sa.Column('smtp_server', sa.String(), nullable=True))
    op.add_column('email_providers', sa.Column('smtp_user', sa.String(), nullable=True))
    op.add_column('email_providers', sa.Column('available', sa.Boolean(), nullable=True))
    op.add_column('email_providers', sa.Column('created_at', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('email_providers', 'smtp_user')
    op.drop_column('email_providers', 'smtp_server')
    op.drop_column('email_providers', 'smtp_password')
    op.drop_column('email_providers', 'available')
    op.drop_column('email_providers', 'created_at')
    # ### end Alembic commands ###
