"""empty message

Revision ID: 0008 add event type id col
Revises: 0007 add event_dates
Create Date: 2018-03-21 22:44:21.843918

"""

# revision identifiers, used by Alembic.
revision = '0008 add event type id col'
down_revision = '0007 add event_dates'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('event_type_id', postgresql.UUID(as_uuid=True), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'event_type_id')
    # ### end Alembic commands ###
