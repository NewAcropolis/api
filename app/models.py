import datetime
from flask import current_app
import uuid
import re

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import PrimaryKeyConstraint, UniqueConstraint, and_, or_
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.hybrid import hybrid_property

from app import db
from app.utils.time import get_local_time, make_ordinal

ANON_PROCESS = 'anon_process'
ANON_REMINDER = 'anon_reminder'
ANNOUNCEMENT = 'announcement'
BASIC = 'basic'
EVENT = 'event'
MAGAZINE = 'magazine'
REPORT_MONTHLY = 'report_monthly'
REPORT_ANNUALLY = 'report_annually'
TICKET = 'ticket'
EMAIL_TYPES = [
    ANON_PROCESS, ANON_REMINDER, EVENT, MAGAZINE, ANNOUNCEMENT, REPORT_MONTHLY, REPORT_ANNUALLY, TICKET, BASIC
]
MANAGED_EMAIL_TYPES = [EVENT, MAGAZINE, ANNOUNCEMENT]

DRAFT = 'draft'
READY = 'ready'
APPROVED = 'approved'
REJECTED = 'rejected'

EMAIL_STATES = EVENT_STATES = ARTICLE_STATES = [
    DRAFT, READY, APPROVED, REJECTED
]


class Article(db.Model):
    __tablename__ = 'articles'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer)
    title = db.Column(db.String(255))
    author = db.Column(db.String(255))
    image_filename = db.Column(db.String(255))
    content = db.Column(db.Text())
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    article_state = db.Column(
        db.String(255),
        db.ForeignKey('article_states.name'),
        default=DRAFT,
        nullable=True,
        index=True,
    )
    tags = db.Column(db.String())
    magazine_id = db.Column(UUID(as_uuid=True), db.ForeignKey('magazines.id'), nullable=True)

    def serialize(self):
        return {
            'id': str(self.id),
            'old_id': self.old_id,
            'title': self.title,
            'author': self.author,
            'content': self.content,
            'image_filename': self.image_filename,
            'article_state': self.article_state,
            'tags': self.tags,
            'magazine_id': self.magazine_id,
            'created_at': get_local_time(self.created_at).strftime('%Y-%m-%d') if self.created_at else None,
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
            'image_filename': self.image_filename,
        }


class ArticleStates(db.Model):
    __tablename__ = 'article_states'

    name = db.Column(db.String(), primary_key=True)


BOOK = 'book'
GIFT = 'gift'
PRODUCT_TYPES = [BOOK, GIFT]


class Product:
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    price = db.Column(db.Numeric(5, 2), nullable=True)
    buy_code = db.Column(db.String(50))
    image_filename = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def serialize(self):
        return {
            'id': str(self.id),
            'price': str(self.price),
            'buy_code': str(self.buy_code),
            'image_filename': self.image_filename,
            'created_at': get_local_time(self.created_at).strftime('%Y-%m-%d') if self.created_at else None,
        }


class Book(Product, db.Model):
    __tablename__ = 'books'

    old_id = db.Column(db.Integer)
    title = db.Column(db.String(255))
    author = db.Column(db.String(255))
    description = db.Column(db.Text())

    def serialize(self):
        book = super().serialize()
        book.update(
            old_id=self.old_id,
            title=self.title,
            author=self.author,
            description=self.description,
        )
        return book


class EmailToMember(db.Model):
    __tablename__ = 'email_to_member'
    __table_args__ = (
        PrimaryKeyConstraint('email_id', 'member_id'),
    )
    email_id = db.Column(UUID(as_uuid=True), db.ForeignKey('emails.id'))
    member_id = db.Column(UUID(as_uuid=True), db.ForeignKey('members.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status_code = db.Column(db.Integer)
    email_provider_id = db.Column(UUID(as_uuid=True), db.ForeignKey('email_providers.id'))

    def serialize(self):
        return {
            'email_id': str(self.email_id),
            'member_id': str(self.member_id),
            'created_at': str(self.created_at),
            'status_code': self.status_code,
            'email_provider_id': str(self.email_provider_id)
        }


BEARER_AUTH = 'bearer'
API_AUTH = 'api'


class EmailProvider(db.Model):
    __tablename__ = 'email_providers'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String, unique=True)
    daily_limit = db.Column(db.Integer, default=0)
    hourly_limit = db.Column(db.Integer, default=0)
    minute_limit = db.Column(db.Integer, default=0)
    monthly_limit = db.Column(db.Integer, default=0)
    api_key = db.Column(db.String)
    api_url = db.Column(db.String)
    data_map = db.Column(JSONB)
    pos = db.Column(db.Integer, unique=True)
    headers = db.Column(db.Boolean)
    auth_type = db.Column(db.String)
    as_json = db.Column(db.Boolean)
    smtp_server = db.Column(db.String)
    smtp_user = db.Column(db.String)
    smtp_password = db.Column(db.String)
    available = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def serialize(self):
        return {
            'id': str(self.id),
            'name': self.name,
            'daily_limit': self.daily_limit,
            'hourly_limit': self.hourly_limit,
            'minute_limit': self.minute_limit,
            'monthly_limit': self.monthly_limit,
            'api_key': self.api_key,
            'api_url': self.api_url,
            'data_map': self.data_map,
            'pos': self.pos,
            'headers': self.headers,
            'auth_type': self.auth_type,
            'as_json': self.as_json,
            'smtp_server': self.smtp_server,
            'smtp_user': self.smtp_user,
            'smtp_password': self.smtp_password,
            'available': self.available,
            'created_at': str(self.created_at)
        }


class Email(db.Model):
    __tablename__ = 'emails'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = db.Column(UUID(as_uuid=True), db.ForeignKey('events.id'), nullable=True)
    magazine_id = db.Column(UUID(as_uuid=True), db.ForeignKey('magazines.id'), nullable=True)
    old_id = db.Column(db.Integer)
    old_event_id = db.Column(db.Integer)
    subject = db.Column(db.String)
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
            return u"{}: {}".format(event.event_type.event_type, event.title)
        elif self.email_type == MAGAZINE:
            if self.magazine_id:
                from app.dao.magazines_dao import dao_get_magazine_by_id
                magazine = dao_get_magazine_by_id(str(self.magazine_id))
            else:
                from app.dao.magazines_dao import dao_get_magazine_by_title
                issue_no = self.details.split(' ')[-1]
                magazine = dao_get_magazine_by_title('Issue ' + issue_no)

            if magazine:
                current_app.logger.info('magazine found %s' % magazine.title)
                return u"New Acropolis bi-monthly magazine: {}".format(magazine.title)

            current_app.logger.error('No magazine found')
            return "Magazine not found"

        return 'No email type'

    def get_expired_date(self):
        if self.email_type == EVENT:
            from app.dao.events_dao import dao_get_event_by_id

            event = dao_get_event_by_id(str(self.event_id))
            return event.get_last_event_date()
        elif self.email_type == MAGAZINE:
            from app.dao.emails_dao import _get_nearest_bi_monthly_send_date

            send_start = _get_nearest_bi_monthly_send_date(created_at=self.created_at)
            return (send_start + datetime.timedelta(weeks=2)).strftime('%Y-%m-%d')

    def get_emails_sent_counts(self):
        return {
            'success': EmailToMember.query.filter(
                EmailToMember.email_id == self.id,
                EmailToMember.status_code.in_([200, 201, 202])).count(),
            'failed': EmailToMember.query.filter(
                EmailToMember.email_id == self.id,
                EmailToMember.status_code.notin_([200, 201, 202])
            ).count(),
            'total_active_members': Member.query.filter(
                or_(
                    and_(
                        Member.active,
                        Email.id == self.id,
                        Member.created_at < Email.expires
                    ),
                    and_(
                        Member.active.is_(False),
                        Email.id == self.id,
                        Member.last_updated > Email.created_at,
                        Member.last_updated < Email.expires
                    ),
                )
            ).count()
        }

    def serialize(self):
        return {
            'id': str(self.id),
            'subject': self.subject or self.get_subject(),
            'event_id': str(self.event_id) if self.event_id else None,
            'magazine_id': str(self.magazine_id) if self.magazine_id else None,
            'old_id': self.old_id,
            'old_event_id': self.old_event_id,
            'details': self.details,
            'extra_txt': self.extra_txt,
            'replace_all': self.replace_all,
            'email_type': self.email_type,
            'email_state': self.email_state,
            'created_at': get_local_time(self.created_at).strftime('%Y-%m-%d %H:%M'),
            'send_starts_at': self.send_starts_at.strftime('%Y-%m-%d') if self.send_starts_at else None,
            'expires': self.expires.strftime('%Y-%m-%d') if self.expires else self.get_expired_date(),
            'send_after': get_local_time(self.send_after).strftime('%Y-%m-%d %H:%M') if self.send_after else None,
            'emails_sent_counts': self.get_emails_sent_counts()
        }


class Magazine(db.Model):
    __tablename__ = 'magazines'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer, unique=True)
    title = db.Column(db.String, unique=True)
    topics = db.Column(db.String)
    filename = db.Column(db.String, unique=True)
    old_filename = db.Column(db.String, unique=True)
    tags = db.Column(db.String())
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def serialize(self):
        return {
            "id": str(self.id),
            "old_id": self.old_id,
            "title": self.title,
            "topics": self.topics,
            "filename": self.filename,
            "old_filename": self.old_filename,
            "tags": self.tags
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
    email = db.Column(db.String, unique=True, nullable=False)
    active = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    marketing_id = db.Column(UUID(as_uuid=True), db.ForeignKey('marketings.id'), nullable=False)
    old_marketing_id = db.Column(db.Integer)
    is_course_member = db.Column(db.Boolean, default=False)
    last_updated = db.Column(db.DateTime)

    def serialize(self):
        return {
            'id': str(self.id),
            'old_id': self.old_id,
            'name': self.name,
            'email': self.email,
            'active': self.active,
            'created_at': self.created_at,
            'marketing_id': str(self.marketing_id),
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
    booking_code = db.Column(db.String(50))
    image_filename = db.Column(db.String(255))
    fee = db.Column(db.Integer, nullable=True)
    conc_fee = db.Column(db.Integer, nullable=True)
    multi_day_fee = db.Column(db.Integer, nullable=True)
    multi_day_conc_fee = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    event_dates = db.relationship(
        "EventDate",
        backref=db.backref("event"),
        cascade="all,delete,delete-orphan",
        order_by='EventDate.event_datetime'
    )
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
    remote_access = db.Column(db.String())
    remote_pw = db.Column(db.String())
    show_banner_text = db.Column(db.Boolean, default=True)

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

    def serialize(self, with_dates=True):
        def sorted_event_dates():
            dates = [e.serialize() for e in self.event_dates]
            dates.sort(key=lambda k: k['event_datetime'])
            return dates

        def serlialized_reject_reasons():
            reject_reasons = [r.serialize() for r in self.reject_reasons]
            reject_reasons.sort(key=lambda k: k['resolved'])
            return reject_reasons

        def has_expired(_sorted_event_dates):
            return datetime.date.today().strftime(
                '%Y-%m-%d %H:%M') > _sorted_event_dates[-1]['event_datetime']

        _sorted_event_dates = sorted_event_dates()

        _event_json = {
            'id': str(self.id),
            'old_id': self.old_id,
            'event_type': self.event_type.event_type,
            'event_type_id': str(self.event_type.id),
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
            'event_state': self.event_state,
            'reject_reasons': serlialized_reject_reasons(),
            'has_expired': has_expired(_sorted_event_dates),
            'show_banner_text': self.show_banner_text,
        }

        if with_dates:
            _event_json.update({'event_dates': sorted_event_dates()})

        if self.remote_access:
            _event_json.update(
                {
                    'remote_access': self.remote_access,
                    'remote_pw': self.remote_pw
                })

        return _event_json

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


ACCESS_AREAS = ['email', 'event', 'article', 'cache', 'magazine', 'order']
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


# UK = 2, EU = 4.50, ROW = 6
DELIVERY_FEE_UK_EU = 'uk-eu', 2.50
DELIVERY_FEE_UK_ROW = 'uk-row', 4
DELIVERY_FEE_EU_ROW = 'eu-row', 1.50
DELIVERY_REFUND_EU_UK = 'eu-uk', 2.50
DELIVERY_REFUND_ROW_UK = 'row-uk', 4
DELIVERY_REFUND_ROW_EU = 'row-eu', 1.5


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    old_id = db.Column(db.Integer)
    member_id = db.Column(UUID(as_uuid=True), db.ForeignKey('members.id'))
    old_member_id = db.Column(db.Integer)
    email_address = db.Column(db.String)
    buyer_name = db.Column(db.String)
    txn_id = db.Column(db.String, unique=True)
    linked_txn_id = db.Column(db.String)
    txn_type = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow())
    payment_status = db.Column(db.String)
    payment_total = db.Column(db.Numeric(6, 2))
    is_donation = db.Column(db.Boolean)
    is_giftaid = db.Column(db.Boolean)
    params = db.Column(db.String)
    address_street = db.Column(db.String)
    address_city = db.Column(db.String)
    address_postal_code = db.Column(db.String)
    address_state = db.Column(db.String)
    address_country = db.Column(db.String)
    address_country_code = db.Column(db.String)
    delivery_zone = db.Column(db.String)
    delivery_status = db.Column(db.String(20))
    delivery_balance = db.Column(db.Numeric(4, 2), default=0)
    delivery_sent = db.Column(db.Boolean)
    refund_issued = db.Column(db.Boolean)
    books = db.relationship(
        "Book", secondary="book_to_order", order_by='Book.title', cascade="all,delete")
    tickets = db.relationship(
        "Ticket", back_populates="order", cascade="all,delete,delete-orphan")
    errors = db.relationship(
        "OrderError",
        backref=db.backref("order"),
        cascade="all,delete,delete-orphan",
        order_by='OrderError.error'
    )
    notes = db.Column(db.String)

    def serialize(self):
        def get_serialized_list(array, delete_created_at=True):
            _list = []
            for item in array:
                _json = item.serialize()
                if 'created_at' in _json and delete_created_at:
                    del(_json['created_at'])
                _list.append(_json)
            return _list

        _json = self.short_serialize()

        books_json = get_serialized_list(self.books)
        for book in books_json:
            book_to_order = BookToOrder.query.filter_by(book_id=book['id'], order_id=self.id).one()
            book['quantity'] = book_to_order.quantity

        _json.update(
            books=books_json,
            tickets=get_serialized_list(self.tickets, delete_created_at=False),
            errors=get_serialized_list(self.errors, delete_created_at=False)
        )
        if self.linked_txn_id:
            _json.update(linked_txn_id=self.linked_txn_id)
        return _json

    def short_serialize(self):
        return {
            'id': str(self.id),
            'txn_id': self.txn_id,
            'txn_type': self.txn_type,
            'created_at': get_local_time(self.created_at).strftime('%Y-%m-%d %H:%M'),
            'buyer_name': self.buyer_name,
            'payment_status': self.payment_status,
            'payment_total': f"{self.payment_total:.2f}",  # not possible to json serialize a decimal
            'is_donation': self.is_donation,
            'address_country_code': self.address_country_code,
            'address_street': self.address_street,
            'address_city': self.address_city,
            'address_postal_code': self.address_postal_code,
            'address_state': self.address_state,
            'address_country': self.address_country,
            'delivery_zone': self.delivery_zone,
            'delivery_status': self.delivery_status,
            'delivery_balance': f"{self.delivery_balance:.2f}",
            'delivery_sent': self.delivery_sent,
            'refund_issued': self.refund_issued,
            'notes': self.notes,
        }


class OrderError(db.Model):
    __tablename__ = 'order_errors'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id'))
    error = db.Column(db.String)

    def serialize(self):
        return {
            'id': str(self.id),
            'error': self.error
        }


class BookToOrder(db.Model):
    __tablename__ = 'book_to_order'
    __table_args__ = (
        PrimaryKeyConstraint('book_id', 'order_id'),
    )
    book_id = db.Column(UUID(as_uuid=True), db.ForeignKey('books.id'))
    order_id = db.Column(UUID(as_uuid=True), db.ForeignKey('orders.id'))
    quantity = db.Column(db.Integer)


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
    order = db.relationship("Order", back_populates="tickets")
    old_order_id = db.Column(db.Integer)
    ticket_type = db.Column(db.String, db.ForeignKey('ticket_types._type'))
    eventdate_id = db.Column(UUID(as_uuid=True), db.ForeignKey('event_dates.id'))
    name = db.Column(db.String)
    price = db.Column(db.Numeric(5, 2))
    last_updated = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    status = db.Column(db.String, db.ForeignKey('ticket_statuses.status'), default=TICKET_STATUS_UNUSED)
    ticket_number = db.Column(db.Integer)
    event = db.relationship("Event", backref=db.backref("tickets", uselist=False))
    event_date = db.relationship("EventDate", backref=db.backref("tickets", uselist=False))

    def serialize(self):
        if not self.eventdate_id:  # pragma: no cover
            current_app.logger.info(f'ticket event date missing {self.id}')
        return {
            'id': str(self.id),
            'event_id': str(self.event_id),
            'event': self.event.serialize(with_dates=False),
            'old_id': self.old_id,
            'ticket_type': self.ticket_type,
            'eventdate_id': str(self.eventdate_id),
            'event_date': self.event_date.serialize() if self.event_date else None,
            'name': self.name if self.name else self.order.buyer_name,
            'price': str(self.price) if self.price else None,
            'last_updated': get_local_time(self.last_updated).strftime('%Y-%m-%d %H:%M'),
            'created_at': get_local_time(self.created_at).strftime('%Y-%m-%d %H:%M'),
            'status': self.status,
            'ticket_number': self.ticket_number
        }


class ReservedPlace(db.Model):
    __tablename__ = "reserved_places"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eventdate_id = db.Column(UUID(as_uuid=True), db.ForeignKey('event_dates.id'))
    name = db.Column(db.String)
    email = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    def serialize(self):
        event_date = EventDate.query.filter_by(id=self.eventdate_id).one()
        event_title = Event.query.filter_by(id=event_date.event_id).one()

        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'event_date': event_date.event_datetime.strftime('%Y-%m-%d %H:%M'),
            'nice_event_date': "{day}, {day_number} of {month} at {time}".format(
                day=event_date.event_datetime.strftime('%A'),
                day_number=make_ordinal(event_date.event_datetime.strftime('%-d')),
                month=event_date.event_datetime.strftime('%B'),
                time=event_date.event_datetime.strftime(
                    "%-I:%M %p" if event_date.event_datetime.strftime("%M") != '00' else "%-I %p"
                )
            ),
            'event_title': event_title.title
        }
