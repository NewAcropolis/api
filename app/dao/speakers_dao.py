from app import db
from app.dao.decorators import transactional
from app.models import Speaker


@transactional
def dao_create_speaker(speaker):
    db.session.add(speaker)


@transactional
def dao_update_speaker(speaker_obj, **kwargs):
    for key, value in kwargs.items():
        setattr(speaker_obj, key, value)
    db.session.add(speaker_obj)


def dao_get_speakers():
    speakers = Speaker.query.all()

    speakers.sort(key=lambda speaker: speaker.name.split(' ')[-1])
    return speakers


def dao_get_speaker_by_id(speaker_id):
    return Speaker.query.filter_by(id=speaker_id).one()
