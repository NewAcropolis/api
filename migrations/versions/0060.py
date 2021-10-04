"""empty message

Revision ID: 0060 set all show_banner_text
Revises: 0059 add show_banner_text
Create Date: 2021-10-03 00:31:22.285217

"""

# revision identifiers, used by Alembic.
revision = '0060 set all show_banner_text'
down_revision = '0059 add show_banner_text'

from alembic import op


def upgrade():
    op.execute("UPDATE events SET show_banner_text = True")

def downgrade():
    pass
