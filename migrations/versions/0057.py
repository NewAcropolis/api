"""empty message

Revision ID: 0057 add has_banner_text
Revises: 0056 update numeric precision
Create Date: 2021-10-02 01:55:20.884537

"""

# revision identifiers, used by Alembic.
revision = '0057 add has_banner_text'
down_revision = '0056 update numeric precision'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('books', 'price',
               existing_type=sa.NUMERIC(precision=3, scale=2),
               type_=sa.Numeric(precision=5, scale=2),
               existing_nullable=True)
    op.add_column('events', sa.Column('has_banner_text', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('events', 'has_banner_text')
    op.alter_column('books', 'price',
               existing_type=sa.Numeric(precision=5, scale=2),
               type_=sa.NUMERIC(precision=3, scale=2),
               existing_nullable=True)
    # ### end Alembic commands ###
