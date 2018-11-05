import datetime
import enum
import uuid
from app import db

from sqlalchemy.dialects.postgresql import (
    UUID,
    JSON
)
from sqlalchemy import UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property


class TokenBlacklist(db.Model):
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    jti = db.Column(db.String(36), nullable=False)
    token_type = db.Column(db.String(10), nullable=False)
    user_identity = db.Column(db.String(50), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    expires = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def serialize(self):
        return {
            'token_id': self.id,
            'jti': self.jti,
            'token_type': self.token_type,
            'user_identity': self.user_identity,
            'revoked': self.revoked,
            'expires': self.expires
        }


class EventType(db.Model):
    __tablename__ = 'event_types'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer)
    event_type = db.Column(db.String(255), unique=True, nullable=False)
    event_desc = db.Column(db.String())
    event_filename = db.Column(db.String(255))
    duration = db.Column(db.Integer)
    repeat = db.Column(db.Integer)
    repeat_interval = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def serialize(self):
        def fees():
            _fees = []
            for fee in self.fees:
                _fees.append({
                    'fee': fee.fee,
                    'conc_fee': fee.conc_fee,
                    'valid_from': fee.valid_from.isoformat()
                })

            _fees = sorted(_fees, key=lambda f: f['valid_from'], reverse=True)
            return _fees

        return {
            'id': str(self.id),
            'old_id': self.old_id,
            'event_type': self.event_type,
            'event_desc': self.event_desc,
            'event_filename': self.event_filename,
            'duration': self.duration,
            'repeat': self.repeat,
            'repeat_interval': self.repeat_interval,
            'fees': fees(),
            'created_at': self.created_at
        }


class Fee(db.Model):
    __tablename__ = 'fees'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fee = db.Column(db.Integer, nullable=False)
    conc_fee = db.Column(db.Integer, nullable=False)
    multi_day_fee = db.Column(db.Integer, nullable=True)
    multi_day_conc_fee = db.Column(db.Integer, nullable=True)
    valid_from = db.Column(db.DateTime, nullable=False, default=datetime.datetime.utcnow)
    event_type_id = db.Column(UUID(as_uuid=True), db.ForeignKey('event_types.id'), nullable=False)
    event_type = db.relationship(EventType, backref=db.backref("fees", order_by=valid_from.desc()))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def serialize(self):
        return {
            'id': str(self.id),
            'event_type_id': str(self.event_type_id),
            'fee': self.fee,
            'conc_fee': self.conc_fee,
            'multi_day_fee': self.multi_day_fee,
            'multi_day_conc_fee': self.multi_day_conc_fee,
            'valid_from': self.valid_from.isoformat()
        }


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer)
    duration = db.Column(db.Integer, nullable=True)
    event_type_id = db.Column(UUID(as_uuid=True), db.ForeignKey('event_types.id'), nullable=False)
    title = db.Column(db.String(255))
    sub_title = db.Column(db.String(255))
    description = db.Column(db.String())
    booking_code = db.Column(db.String(20))
    image_filename = db.Column(db.String(255))
    fee = db.Column(db.Integer, nullable=True)
    conc_fee = db.Column(db.Integer, nullable=True)
    multi_day_fee = db.Column(db.Integer, nullable=True)
    multi_day_conc_fee = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    event_dates = db.relationship("EventDate", backref=db.backref("events"))
    venue_id = db.Column(UUID(as_uuid=True), db.ForeignKey('venues.id'))
    venue = db.relationship("Venue", backref=db.backref("event", uselist=False))

    def serialize(self):
        return {
            'id': self.id,
            'old_id': self.old_id,
            'title': self.title,
            'sub_title': self.sub_title,
            'description': self.description,
            'booking_code': self.booking_code,
            'image_filename': self.image_filename,
            'fee': self.fee,
            'conc_fee': self.conc_fee,
            'multi_day_fee': self.multi_day_fee,
            'multi_day_conc_fee': self.multi_day_conc_fee,
            'venue': self.venue.serialize() if self.venue else None,
            'event_dates': [e.serialize() for e in self.event_dates]
        }

    def __repr__(self):
        return '<Event: id {}>'.format(self.id)


class Speaker(db.Model):
    __tablename__ = 'speakers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(100))
    name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    # should only expect 1 parent at most, so a parent cannot be a parent
    parent_id = db.Column(UUID(as_uuid=True), primary_key=False, default=None, nullable=True)

    def serialize(self):
        return {
            'id': str(self.id),
            'title': self.title,
            'name': self.name,
            'parent_id': str(self.parent_id) if self.parent_id else None
        }

    @hybrid_property
    def last_name(self):
        return str(self.name).split(' ')[-1]


event_date_to_speaker = db.Table(
    'event_date_to_speaker',
    db.Model.metadata,
    db.Column('event_date_id', UUID(as_uuid=True), db.ForeignKey('event_dates.id')),
    db.Column('speaker_id', UUID(as_uuid=True), db.ForeignKey('speakers.id')),
    UniqueConstraint('event_date_id', 'speaker_id', name='uix_event_date_id_to_speaker_id')
)


class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer)
    name = db.Column(db.String(255))
    address = db.Column(db.String(255))
    directions = db.Column(db.String(255))
    default = db.Column(db.Boolean)

    def serialize(self):
        return {
            'id': str(self.id),
            'old_id': self.old_id,
            'name': str(self.name),
            'address': self.address,
            'directions': self.directions,
            'default': self.default,
        }


class EventDate(db.Model):
    __tablename__ = 'event_dates'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    event_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    duration = db.Column(db.Integer, nullable=True)
    soldout = db.Column(db.Boolean, default=False)
    repeat = db.Column(db.Integer, nullable=True)
    repeat_interval = db.Column(db.Integer, nullable=True)
    fee = db.Column(db.Integer, nullable=True)
    conc_fee = db.Column(db.Integer, nullable=True)
    multi_day_fee = db.Column(db.Integer, nullable=True)
    multi_day_conc_fee = db.Column(db.Integer, nullable=True)
    venue_id = db.Column(UUID(as_uuid=True), db.ForeignKey('venues.id'))
    venue = db.relationship(Venue, backref=db.backref("event_date", uselist=False))
    speakers = db.relationship(
        'Speaker',
        secondary=event_date_to_speaker,
        backref=db.backref('event_date_to_speaker', lazy='dynamic')
    )

    def serialize(self):
        return {
            'id': str(self.id),
            'event_id': str(self.event_id),
            'event_datetime': self.event_datetime.strftime('%Y-%m-%d %H:%M'),
            'speakers': [s.serialize() for s in self.speakers],
            'fee': self.fee,
            'conc_fee': self.conc_fee,
            'multi_day_fee': self.multi_day_fee,
            'multi_day_conc_fee': self.multi_day_conc_fee,
            'venue': self.venue.serialize() if self.venue else None
        }
