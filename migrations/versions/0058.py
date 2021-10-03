"""empty message

Revision ID: 0058 set all has_banner_text
Revises: 0057 add has_banner_text
Create Date: 2021-10-03 00:31:22.285217

"""

# revision identifiers, used by Alembic.
revision = '0058 set all has_banner_text'
down_revision = '0057 add has_banner_text'

from alembic import op


def upgrade():
    op.execute("UPDATE events SET has_banner_text = True")

def downgrade():
    pass
