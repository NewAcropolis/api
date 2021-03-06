"""empty message

Revision ID: 0021 allow access_area nullable
Revises: 0020 add users
Create Date: 2019-02-02 13:42:31.511289

"""

# revision identifiers, used by Alembic.
revision = '0021 allow access_area nullable'
down_revision = '0020 add users'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'access_area',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'access_area',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###
