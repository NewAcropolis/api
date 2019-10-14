import datetime
import uuid
import re

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.ext.hybrid import hybrid_property

from app import db


ANON_PROCESS = 'anon_process'
ANON_REMINDER = 'anon_reminder'
ANNOUNCEMENT = 'announcement'
EVENT = 'event'
MAGAZINE = 'magazine'
REPORT_MONTHLY = 'report_monthly'
REPORT_ANNUALLY = 'report_annually'
TICKET = 'ticket'
EMAIL_TYPES = [ANON_PROCESS, ANON_REMINDER, EVENT, MAGAZINE, ANNOUNCEMENT, REPORT_MONTHLY, REPORT_ANNUALLY, TICKET]
MANAGED_EMAIL_TYPES = [EVENT, MAGAZINE, ANNOUNCEMENT]

DRAFT = 'draft'
READY = 'ready'
APPROVED = 'approved'
REJECTED = 'rejected'

EMAIL_STATES = EVENT_STATES = [
    DRAFT, READY, APPROVED, REJECTED
]


class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer)
    title = db.Column(db.String(255))
    author = db.Column(db.String(255))
    content = db.Column(db.Text())
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def serialize(self):
        return {
            'id': str(self.id),
            'old_id': self.old_id,
            'title': self.title,
            'author': self.author,
            'content': self.content,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else None,
        }

    def serialize_summary(self):
        def get_short_content(num_words):
            html_tag_pattern = r'<.*?>'
            clean_content = re.sub(html_tag_pattern, '', self.content)

            content_arr = clean_content.split(' ')
            if len(content_arr) > num_words:
                find_words = " ".join([content_arr[num_words - 2], content_arr[num_words - 1], content_arr[num_words]])
                return clean_content[0:clean_content.index(find_words) + len(find_words)] + '...'
            else:
                return clean_content

        return {
            'id': str(self.id),
            'title': self.title,
            'author': self.author,
            'short_content': get_short_content(num_words=110),
            'very_short_content': get_short_content(num_words=30),
        }


class EmailToMember(db.Model):
    __tablename__ = 'email_to_member'
    __table_args__ = (
        PrimaryKeyConstraint('email_id', 'member_id'),
    )
    email_id = db.Column(UUID(as_uuid=True), db.ForeignKey('emails.id'))
    member_id = db.Column(UUID(as_uuid=True), db.ForeignKey('members.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status_code = db.Column(db.Integer)

    def serialize(self):
        return {
            'email_id': str(self.email_id),
            'member_id': str(self.member_id),
            'created_at': str(self.created_at),
        }


class Email(db.Model):
    __tablename__ = 'emails'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id'), nullable=True)
    old_id = db.Column(db.Integer)
    old_event_id = db.Column(db.Integer)
    details = db.Column(db.String)
    extra_txt = db.Column(db.String)
    replace_all = db.Column(db.Boolean)
    email_state = db.Column(
        db.String(255),
        db.ForeignKey('email_states.name'),
        default=DRAFT,
        nullable=True,
        index=True,
    )
    email_type = db.Column(
        db.String,
        db.ForeignKey('email_types.email_type'),
        default=EVENT,
        nullable=False,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    send_starts_at = db.Column(db.DateTime)
    send_after = db.Column(db.DateTime)
    expires = db.Column(db.DateTime)
    task_id = db.Column(db.String)
    members_sent_to = db.relationship(
        'Member',
        secondary='email_to_member',
        backref=db.backref('email_to_member', lazy='dynamic'),
    )

    def get_subject(self):
        if self.email_type == EVENT:
            from app.dao.events_dao import dao_get_event_by_id

            event = dao_get_event_by_id(str(self.event_id))
            return "{}: {}".format(event.event_type.event_type, event.title)
        return 'No email type'

    def get_expired_date(self):
        if self.email_type == EVENT:
            from app.dao.events_dao import dao_get_event_by_id

            event = dao_get_event_by_id(str(self.event_id))
            return event.get_last_event_date()

    def get_emails_sent_count(self):
        return EmailToMember.query.filter_by(email_id=self.id).count()

    def serialize(self):
        return {
            'id': str(self.id),
            'subject': self.get_subject(),
            'event_id': str(self.event_id) if self.event_id else None,
            'old_id': self.old_id,
            'old_event_id': self.old_event_id,
            'details': self.details,
            'extra_txt': self.extra_txt,
            'replace_all': self.replace_all,
            'email_type': self.email_type,
            'email_state': self.email_state,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'send_starts_at': self.send_starts_at.strftime('%Y-%m-%d') if self.send_starts_at else None,
            'expires': self.expires.strftime('%Y-%m-%d') if self.expires else self.get_expired_date(),
            'send_after': self.send_after.strftime('%Y-%m-%d %H:%M') if self.send_after else None,
            'emails_sent_count': self.get_emails_sent_count()
        }


class Marketing(db.Model):
    __tablename__ = 'marketings'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer, unique=True)
    description = db.Column(db.String, unique=True)  # marketingtext
    order_number = db.Column(db.Integer)
    active = db.Column(db.Boolean)  # visible

    def serialize(self):
        return {
            "id": str(self.id),
            "old_id": self.old_id,
            "description": self.description,
            "order_number": self.order_number,
            "acive": self.active
        }


class Member(db.Model):
    __tablename__ = 'members'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer)
    name = db.Column(db.String)
    email = db.Column(db.String, unique=True)
    active = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    marketing_id = db.Column(UUID(as_uuid=True), db.ForeignKey('marketings.id'), nullable=False)
    old_marketing_id = db.Column(db.Integer)
    is_course_member = db.Column(db.Boolean)
    last_updated = db.Column(db.DateTime)

    def serialize(self):
        return {
            'id': self.id,
            'old_id': self.old_id,
            'name': self.name,
            'email': self.email,
            'active': self.active,
            'created_at': self.created_at,
            'marketing_id': self.marketing_id,
            'old_marketing_id': self.old_marketing_id,
            'is_course_member': self.is_course_member,
            'last_updated': self.last_updated
        }


class EmailStates(db.Model):
    __tablename__ = 'email_states'

    name = db.Column(db.String(), primary_key=True)


class EmailType(db.Model):
    __tablename__ = 'email_types'

    email_type = db.Column(db.String, primary_key=True)
    template = db.Column(db.String)


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer)
    duration = db.Column(db.Integer, nullable=True)
    event_type_id = db.Column(UUID(as_uuid=True), db.ForeignKey('event_types.id'), nullable=False)
    event_type = db.relationship("EventType", backref=db.backref("event", uselist=False))
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
    event_dates = db.relationship("EventDate", backref=db.backref("events"), cascade="all,delete,delete-orphan")
    event_state = db.Column(
        db.String(255),
        db.ForeignKey('event_states.name'),
        default=DRAFT,
        nullable=True,
        index=True,
    )
    email = db.relationship("Email", backref=db.backref("event", uselist=False))
    reject_reasons = db.relationship("RejectReason", backref=db.backref("event", uselist=True))
    venue_id = db.Column(UUID(as_uuid=True), db.ForeignKey('venues.id'))
    venue = db.relationship("Venue", backref=db.backref("event", uselist=False))

    def serialize_event_dates(self):
        def serialize_speakers(speakers):
            _speakers = []
            for s in speakers:
                _speakers.append({
                    'speaker_id': s.id
                })

            return _speakers

        event_dates = []
        for e in self.event_dates:
            event_dates.append(
                {
                    'event_datetime': e.event_datetime.strftime('%Y-%m-%d %H:%M'),
                    'end_time': e.end_time,
                    'speakers': serialize_speakers(e.speakers)
                }
            )
        return event_dates

    def is_event_today(self, eventdate_id):
        for date in self.event_dates:
            if (
                date.id == eventdate_id and
                date.event_datetime.strftime('%Y-%m-%d') == datetime.datetime.today().strftime('%Y-%m-%d')
            ):
                return True
        return False

    def get_sorted_event_dates(self):
        if self.event_dates:
            dates = [e.serialize() for e in self.event_dates]
            dates.sort(key=lambda k: k['event_datetime'])
            return dates

    def get_first_event_date(self):
        dates = self.get_sorted_event_dates()
        if dates:
            return dates[0]['event_datetime'].split(' ')[0]

    def get_last_event_date(self):
        dates = self.get_sorted_event_dates()
        if dates:
            return dates[-1]['event_datetime'].split(' ')[0]

    def serialize(self):
        def sorted_event_dates():
            dates = [e.serialize() for e in self.event_dates]
            dates.sort(key=lambda k: k['event_datetime'])
            return dates

        def serlialized_reject_reasons():
            reject_reasons = [r.serialize() for r in self.reject_reasons]
            reject_reasons.sort(key=lambda k: k['resolved'])
            return reject_reasons

        return {
            'id': self.id,
            'old_id': self.old_id,
            'event_type': self.event_type.event_type,
            'event_type_id': self.event_type.id,
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
            'event_dates': sorted_event_dates(),
            'event_state': self.event_state,
            'reject_reasons': serlialized_reject_reasons()
        }

    def __repr__(self):
        return '<Event: id {}>'.format(self.id)


event_date_to_speaker = db.Table(
    'event_date_to_speaker',
    db.Model.metadata,
    db.Column('event_date_id', UUID(as_uuid=True), db.ForeignKey('event_dates.id')),
    db.Column('speaker_id', UUID(as_uuid=True), db.ForeignKey('speakers.id')),
    UniqueConstraint('event_date_id', 'speaker_id', name='uix_event_date_id_to_speaker_id')
)


class EventDate(db.Model):
    __tablename__ = 'event_dates'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    event_datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    end_time = db.Column(db.Time, nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    soldout = db.Column(db.Boolean, default=False)
    repeat = db.Column(db.Integer, nullable=True)
    repeat_interval = db.Column(db.Integer, nullable=True)
    fee = db.Column(db.Integer, nullable=True)
    conc_fee = db.Column(db.Integer, nullable=True)
    multi_day_fee = db.Column(db.Integer, nullable=True)
    multi_day_conc_fee = db.Column(db.Integer, nullable=True)

    venue_id = db.Column(UUID(as_uuid=True), db.ForeignKey('venues.id'))
    venue = db.relationship("Venue", backref=db.backref("event_date", uselist=False))
    speakers = db.relationship(
        'Speaker',
        secondary=event_date_to_speaker,
        backref=db.backref('event_date_to_speaker', lazy='dynamic'),
    )

    def serialize(self):
        return {
            'id': str(self.id),
            'event_id': str(self.event_id),
            'event_datetime': self.event_datetime.strftime('%Y-%m-%d %H:%M'),
            'end_time': self.end_time.strftime('%H:%M') if self.end_time else None,
            'speakers': [s.serialize() for s in self.speakers]
        }


class EventStates(db.Model):
    __tablename__ = 'event_states'

    name = db.Column(db.String(), primary_key=True)


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


class RejectReason(db.Model):
    __tablename__ = 'reject_reasons'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id'))
    reason = db.Column(db.String(255), nullable=False)
    resolved = db.Column(db.Boolean, default=False)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def serialize(self):
        return {
            'id': str(self.id),
            'reason': self.reason,
            'resolved': self.resolved,
            'created_by': self.created_by,
            'created_at': self.created_at
        }


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


ACCESS_AREAS = ['email', 'event', 'report', 'article']
USER_ADMIN = 'admin'


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=True)
    active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    last_login = db.Column(db.DateTime)
    access_area = db.Column(db.String())
    session_id = db.Column(db.String())
    ip = db.Column(db.String())

    def serialize(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'name': self.name,
            'active': self.active,
            'created_at': self.created_at,
            'last_login': self.last_login,
            'access_area': self.access_area,
            'session_id': self.session_id,
            'ip': self.ip
        }

    def is_admin(self):
        return USER_ADMIN in self.access_area


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


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer)
    member_id = db.Column(UUID(as_uuid=True), db.ForeignKey('members.id'))
    old_member_id = db.Column(db.Integer)
    email_address = db.Column(db.String)
    buyer_name = db.Column(db.String)
    txn_id = db.Column(db.String)
    txn_type = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    payment_status = db.Column(db.String)
    payment_total = db.Column(db.Numeric(precision=2))
    params = db.Column(db.String)


TICKET_FULL = 'Full'
TICKET_ALL_FULL = 'All_Full'
TICKET_CONC = 'Concession'
TICKET_ALL_CONC = 'All_Concession'
TICKET_MEMBER = 'Member'
TICKET_TYPES = [TICKET_FULL, TICKET_ALL_FULL, TICKET_CONC, TICKET_ALL_CONC, TICKET_MEMBER]


class TicketType(db.Model):
    __tablename__ = 'ticket_types'

    _type = db.Column(db.String(), primary_key=True)


TICKET_STATUS_USED = 'Used'
TICKET_STATUS_UNUSED = 'Unused'


class TicketStatus(db.Model):
    __tablename__ = 'ticket_statuses'

    status = db.Column(db.String(), primary_key=True)


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id'))
    old_id = db.Column(db.Integer)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id'))
    old_order_id = db.Column(db.Integer)
    ticket_type = db.Column(db.String, db.ForeignKey('ticket_types._type'))
    eventdate_id = db.Column(UUID(as_uuid=True), db.ForeignKey('event_dates.id'))
    name = db.Column(db.String)
    price = db.Column(db.Numeric(precision=2))
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String, db.ForeignKey('ticket_statuses.status'), default=TICKET_STATUS_UNUSED)
    ticket_number = db.Column(db.Integer)
    event = db.relationship("Event", backref=db.backref("tickets", uselist=False))
