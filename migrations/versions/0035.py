"""empty message

Revision ID: 0035 add basic email template
Revises: 0034 add send_after to emails
Create Date: 2019-10-30 00:01:13.441215

"""

# revision identifiers, used by Alembic.
revision = '0035 add basic email template'
down_revision = '0034 add send_after to emails'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from app.models import EmailType, EMAIL_TYPES


def upgrade():
    conn = op.get_bind()
    res = conn.execute("SELECT email_type FROM email_types")
    email_types = res.fetchall()

    # as 0025 adds in all EMAIL_TYPES we need to only add in missing email types
    for email_type in EMAIL_TYPES:
        if email_type not in [e[0] for e in email_types]:
            op.execute(
                "INSERT INTO email_types (email_type) VALUES ('{}')".format(email_type)
            )


def downgrade():
    pass
