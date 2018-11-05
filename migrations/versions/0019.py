"""empty message

Revision ID: 0019 add duration to events
Revises: 0018 null event_dates.venue_id
Create Date: 2018-11-04 23:56:05.336353

"""

# revision identifiers, used by Alembic.
revision = '0019 add duration to events'
down_revision = '0018 null event_dates.venue_id'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('duration', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'duration')
    # ### end Alembic commands ###
