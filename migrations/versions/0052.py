"""empty message

Revision ID: 0052 add remote login
Revises: 0051 add delivery_sent, notes
Create Date: 2021-08-17 00:30:00.903475

"""

# revision identifiers, used by Alembic.
revision = '0052 add remote login'
down_revision = '0051 add delivery_sent, notes'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('events', sa.Column('remote_access', sa.String(), nullable=True))
    op.add_column('events', sa.Column('remote_pw', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'remote_pw')
    op.drop_column('events', 'remote_access')
    # ### end Alembic commands ###
