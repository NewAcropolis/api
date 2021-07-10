"""empty message

Revision ID: 0002 Insert event_types and fees
Revises: 0001 Add event_types,events,fees
Create Date: 2017-09-26 23:39:03.972735

"""

# revision identifiers, used by Alembic.
revision = '0002 Insert event_types and fees'
down_revision = '0001 Add event_types,events,fees'

import uuid

from alembic import op

def upgrade():
    for event_type in old_event_types:
        event_type_id = str(uuid.uuid4())
        op.execute(
            "INSERT INTO event_types (id, old_id, event_type, event_filename, duration, repeat, repeat_interval) "
            "VALUES ('{id}', {old_id}, '{event_type}', {event_filename}, {duration}, {repeat}, {repeat_interval})".format(
                id=event_type_id,
                old_id=event_type['id'],
                event_type=event_type['EventType'], 
                event_filename="'{}'".format(event_type['EventFilename']) if 'EventFilename' in event_type.keys() else 'Null',
                duration=event_type['Duration'] if 'Duration' in event_type.keys() else 'Null',
                repeat=event_type['Repeat'] if 'Repeat' in event_type.keys() else 'Null',
                repeat_interval=event_type['RepeatInterval']  if 'RepeatInterval' in event_type.keys() else 'Null'
            )
        )

        event_type_fees = [fee for fee in old_default_fees if fee['id'] == event_type['id']]

        for event_fee in event_type_fees:
            op.execute(
                "INSERT INTO fees (id, fee, conc_fee, valid_from, event_type_id)"
                "VALUES ('{id}', {fee}, {conc_fee}, '{valid_from}', '{event_type_id}')".format(
                    id=str(uuid.uuid4()),
                    fee=event_fee['Fee'],
                    conc_fee=event_fee['ConcFee'],
                    valid_from=event_fee['StartDate'],
                    event_type_id=event_type_id
                )
            )


def downgrade():
    op.execute('DELETE FROM fees')
    op.execute('DELETE FROM event_types')


## old data as json block
old_event_types = [
    {
        "id": 1,
        "EventType": "Talk",
        "Duration": 45
    },
    {
        "id": 2,
        "EventType": "Introductory Course",
        "Duration": 120,
        "Repeat": 16,
        "RepeatInterval": 7
    },
    {
        "id": 3,
        "EventType": "Seminar",
    },
    {
        "id": 4,
        "EventType": "Ecological event",
    },
    {
        "id": 5,
        "EventType": "Excursion",
        "EventFilename": "TextExcursion.gif"
    },
    {
        "id": 6,
        "EventType": "Exhibition",
    },
    {
        "id": 7,
        "EventType": "Meeting",
    },
    {
        "id": 8,
        "EventType": "Cultural Event",
        "EventFilename": "TextCultural.gif"
    },
    {
        "id": 9,
        "EventType": "Short Course",
    },
    {
        "id": 10,
        "EventType": "Workshop",
    }
]

old_default_fees = [
    {"id": 1, "Fee":4, "ConcFee": 2, "StartDate": "2004-09-20 19:30:00" },
    {"id": 1, "Fee":5, "ConcFee": 3, "StartDate": "2005-09-28 19:30:00" },
    {"id": 2, "Fee":96, "ConcFee": 64, "StartDate":	"2004-09-29 19:30:00" },
    {"id": 2, "Fee":120, "ConcFee": 85, "StartDate": "2006-10-09 19:30:00" },
    {"id": 2, "Fee":130, "ConcFee": 90, "StartDate": "2012-09-27 19:00:00" },
    {"id": 2, "Fee":140, "ConcFee": 105, "StartDate": "2014-02-27 19:00:00" },
    {"id": 2, "Fee":160, "ConcFee": 120, "StartDate": "2017-10-04 19:00:00" },
    {"id": 3, "Fee":25,	"ConcFee": 18, "StartDate":	"2004-11-27 16:00:00" },
    {"id": 3, "Fee":45,	"ConcFee": 30, "StartDate":	"2008-10-18 10:00:00" },
    {"id": 9, "Fee":45,	"ConcFee": 35, "StartDate":	"2013-01-29 19:30:00" },
    {"id": 9, "Fee":40,	"ConcFee": 30, "StartDate":	"2013-09-17 19:00:00" },
    {"id": 9, "Fee":40,	"ConcFee": 35, "StartDate":	"2014-10-27 19:30:00" },
    {"id": 10, "Fee":20, "ConcFee": 15, "StartDate": "2014-06-20 18:30:00" },
    {"id": 10, "Fee":18, "ConcFee": 12, "StartDate": "2016-04-23 15:00:00" }
]