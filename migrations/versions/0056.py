"""empty message

Revision ID: 0056 update numeric precision
Revises: 0055 update payment_total price
Create Date: 2021-09-27 00:31:22.285217

"""

# revision identifiers, used by Alembic.
revision = '0056 update numeric precision'
down_revision = '0055 update payment_total price'

from alembic import op


def upgrade():
    op.execute("ALTER TABLE tickets ALTER COLUMN price TYPE numeric(5,2);")
    op.execute("ALTER TABLE orders ALTER COLUMN payment_total TYPE numeric(6,2);")

def downgrade():
    op.execute("ALTER TABLE tickets ALTER COLUMN price TYPE numeric(2,0);")
    op.execute("ALTER TABLE orders ALTER COLUMN payment_total TYPE numeric(2,0);")
