"""empty message

Revision ID: 0066 add is_donation
Revises: 0065 add auth_type
Create Date: 2022-02-11 01:26:27.338453

"""

# revision identifiers, used by Alembic.
revision = '0066 add is_donation'
down_revision = '0065 add auth_type'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('is_donation', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders', 'is_donation')
    # ### end Alembic commands ###
