"""empty message

Revision ID: 0078 Update book price
Revises: 0077 add competition event_type
Create Date: 2025-09-20 01:37:03.972735

"""

# revision identifiers, used by Alembic.
revision = '0078 Update book price'
down_revision = '0077 add competition event_type'

import uuid

from alembic import op

def upgrade():
    event_type_id = str(uuid.uuid4())
    op.execute(
        "UPDATE books SET price = '7.99';"
        "UPDATE books SET price = '0.01' WHERE title = 'TEST BOOK';"
        "UPDATE books SET price = '6.99' WHERE author = 'Pierre Poulain';"
        "UPDATE books SET price = '8.99' WHERE author = 'Sabine Leitner';"
    )


def downgrade():
    pass
