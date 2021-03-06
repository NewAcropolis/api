"""empty message

Revision ID: 0009 add venues table/upd ev dt
Revises: 0008 add event type id col
Create Date: 2018-05-02 01:04:35.504158

"""

# revision identifiers, used by Alembic.
revision = '0009 add venues table/upd ev dt'
down_revision = '0008 add event type id col'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('venues',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('address', sa.String(length=255), nullable=True),
    sa.Column('directions', sa.String(length=255), nullable=True),
    sa.Column('default', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'event_dates', sa.Column('venue_id', postgresql.UUID(as_uuid=True), nullable=False))
    op.create_foreign_key(None, 'event_dates', 'venues', ['venue_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'event_dates', type_='foreignkey')
    op.drop_column(u'event_dates', 'venue_id')
    op.drop_table('venues')
    # ### end Alembic commands ###
