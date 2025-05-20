"""empty message

Revision ID: 0077 add competition event_type
Revises: 0076 add headline to events
Create Date: 2017-09-26 23:39:03.972735

"""

# revision identifiers, used by Alembic.
revision = '0077 add competition event_type'
down_revision = '0076 add headline to events'

import uuid

from alembic import op

def upgrade():
    event_type_id = str(uuid.uuid4())
    op.execute(
        "INSERT INTO event_types (id, event_type, event_filename, duration, repeat, repeat_interval) "
        "VALUES ('{id}', '{event_type}', {event_filename}, {duration}, {repeat}, {repeat_interval})".format(
            id=event_type_id,
            event_type="Competition", 
            event_filename="Null",
            duration="Null",
            repeat="Null",
            repeat_interval="Null"
        )
    )


def downgrade():
    op.execute("DELETE FROM event_types WHERE event_type = 'Competition'")
