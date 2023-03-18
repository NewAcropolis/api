"""empty message

Revision ID: 0071 articles state to approved
Revises: 0070 add email details to order
Create Date: 2023-03-14 01:00:00

"""

# revision identifiers, used by Alembic.
revision = '0071 articles state to approved'
down_revision = '0070 add email details to order'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    res = conn.execute(
        "UPDATE articles SET article_state = 'approved' WHERE created_at < '2023-03-14'"
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    res = conn.execute(
        "UPDATE articles SET article_state = 'new' WHERE created_at < '2023-03-14'"
    )
    # ### end Alembic commands ###