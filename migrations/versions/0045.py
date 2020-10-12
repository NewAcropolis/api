"""empty message

Revision ID: 0045 members email not null
Revises: 0044 add books
Create Date: 2020-10-09 12:52:26.599932

"""

# revision identifiers, used by Alembic.
revision = '0045 members email not null'
down_revision = '0044 add books'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    res = conn.execute("SELECT * FROM members WHERE email is null")
    null_members = res.fetchall()

    for i in range(len(null_members)):
        op.execute(
            f"UPDATE members SET email={i} WHERE id = '{str(null_members[i]['id'])}'"
        )
        op.execute(
            f"UPDATE members SET active=false WHERE id = '{str(null_members[i]['id'])}'"
        )

    op.alter_column('members', 'email',
               existing_type=sa.VARCHAR(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('members', 'email',
               existing_type=sa.VARCHAR(),
               nullable=True)
    # ### end Alembic commands ###
