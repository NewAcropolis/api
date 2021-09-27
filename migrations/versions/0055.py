"""empty message

Revision ID: 0055 update payment_total price
Revises: 0054 add reserved_places
Create Date: 2021-09-27 00:31:22.285217

"""

# revision identifiers, used by Alembic.
revision = '0055 update payment_total price'
down_revision = '0054 add reserved_places'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.alter_column('orders', 'payment_total',
               existing_type=sa.Numeric(precision=4),
               nullable=True)
    op.alter_column('tickets', 'price',
               existing_type=sa.Numeric(precision=3),
               nullable=True)

def downgrade():
    op.alter_column('orders', 'payment_total',
               existing_type=sa.Numeric(precision=2),
               nullable=True)
    op.alter_column('tickets', 'price',
               existing_type=sa.Numeric(precision=2),
               nullable=True)
