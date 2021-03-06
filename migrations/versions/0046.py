"""empty message

Revision ID: 0046 remove long description
Revises: 0045 members email not null
Create Date: 2020-10-19 00:32:46.404248

"""

# revision identifiers, used by Alembic.
revision = '0046 remove long description'
down_revision = '0045 members email not null'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('books', 'long_description')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('books', sa.Column('long_description', sa.TEXT(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
