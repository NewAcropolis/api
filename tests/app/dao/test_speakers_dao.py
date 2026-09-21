
from app.dao.speakers_dao import (
    dao_update_speaker,
    dao_get_speakers,
    dao_get_speaker_by_id,
    dao_get_speaker_by_name
)
from app.models import Speaker

from tests.db import create_speaker


class WhenUsingSpeakersDAO(object):

    def it_creates_a_speaker(self, db):
        speaker = create_speaker()
        assert Speaker.query.count() == 1

        speaker_from_db = Speaker.query.filter(Speaker.id == speaker.id).first()

        assert speaker == speaker_from_db

    def it_updates_a_speaker_dao(self, db, db_session, sample_speaker):
        dao_update_speaker(sample_speaker.id, name='Gary Green')

        speaker_from_db = Speaker.query.filter(Speaker.id == sample_speaker.id).first()

        assert sample_speaker.name == speaker_from_db.name

    def it_gets_all_speakers_in_last_name_alphabetical_order(self, db, db_session, sample_speaker):
        speakers = [create_speaker(name='Bob Blue'), create_speaker(name='Sid Green'), sample_speaker]

        speakers_from_db = dao_get_speakers()
        assert speakers == speakers_from_db

    def it_gets_a_speaker_by_id(self, db, db_session, sample_speaker):
        speaker = create_speaker(name='Sam Black')

        fetched_speaker = dao_get_speaker_by_id(speaker.id)
        assert fetched_speaker == speaker

    def it_gets_a_speaker_by_name(self, db, db_session, sample_speaker):
        speaker = create_speaker(name='Sam Black')

        fetched_speaker = dao_get_speaker_by_name(speaker.name)
        assert fetched_speaker == speaker
