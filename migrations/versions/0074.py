"""empty message

Revision ID: 0074 add shipping_cost
Revises: 0072 add source_filename
Create Date: 2024-03-23 02:26:52.299512

"""

# revision identifiers, used by Alembic.
revision = '0074 add shipping_cost'
down_revision = '0072 add source_filename'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('orders', sa.Column('shipping_cost', sa.Numeric(precision=4, scale=2), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('orders', 'shipping_cost')
    # ### end Alembic commands ###