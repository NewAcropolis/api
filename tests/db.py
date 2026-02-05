from datetime import datetime
import json
from app import db

from app.dao import dao_create_record, dao_update_record
from app.dao.articles_dao import dao_create_article
from app.dao.books_dao import dao_create_book, dao_update_book_to_order_quantity
from app.dao.blacklist_dao import store_token
from app.dao.emails_dao import dao_create_email, dao_create_email_to_member
from app.dao.email_providers_dao import dao_create_email_provider
from app.dao.events_dao import dao_create_event, dao_get_event_by_old_id
from app.dao.event_dates_dao import dao_create_event_date
from app.dao.event_types_dao import dao_create_event_type
from app.dao.fees_dao import dao_create_fee
from app.dao.marketings_dao import dao_create_marketing
from app.dao.members_dao import dao_create_member
from app.dao.reject_reasons_dao import dao_create_reject_reason
from app.dao.speakers_dao import dao_create_speaker
from app.dao.users_dao import dao_create_user
from app.dao.venues_dao import dao_create_venue
from app.models import (
    Article, Book, BookToOrder, Email, EmailToMember, EmailProvider, Event, EventDate, EventType, Fee,
    Magazine, Marketing, Member, Order, RejectReason, Speaker, Ticket, User, Venue,
    BASIC, EVENT, TICKET_STATUS_UNUSED, DRAFT, API_AUTH
)


def create_event(
    title='test title',
    description='test description',
    event_type_id=None,
    fee=5,
    conc_fee=3,
    multi_day_fee=12,
    multi_day_conc_fee=10,
    old_id=1,
    event_dates=None,
    venue_id=None
):
    if not event_type_id:
        event_type = EventType.query.filter_by(event_type='workshop').first()
        if not event_type:
            event_type = create_event_type(event_type='workshop')
        event_type_id = str(event_type.id)

    if not venue_id:
        venue = Venue.query.first()
        if not venue:
            venue = create_venue()
        venue_id = str(venue.id)

    data = {
        'old_id': old_id,
        'event_type_id': event_type_id,
        'title': title,
        'description': description,
        'fee': fee,
        'conc_fee': conc_fee,
        'multi_day_fee': multi_day_fee,
        'multi_day_conc_fee': multi_day_conc_fee,
        'venue_id': venue_id,
    }
    event = Event(**data)

    if event_dates:
        event.event_dates.extend(event_dates)

    dao_create_event(event)

    return event


def create_event_type(
        old_id=1,
        event_type='talk',
        event_desc='test talk',
        event_filename=None,
        duration=45,
        repeat=1,
        repeat_interval=0
):
    data = {
        'old_id': old_id,
        'event_type': event_type,
        'event_desc': event_desc,
        'event_filename': event_filename,
        'duration': duration,
        'repeat': repeat,
        'repeat_interval': repeat_interval
    }
    event_type = EventType(**data)

    dao_create_event_type(event_type)
    return event_type


def create_event_date(
    event_id=None,
    event_datetime='2018-01-01 19:00',
    duration=90,
    soldout=False,
    repeat=3,
    repeat_interval=7,
    fee=5,
    conc_fee=3,
    multi_day_fee=12,
    multi_day_conc_fee=10,
    speakers=None,
):
    venue = create_venue()

    data = {
        'event_id': event_id,
        'event_datetime': event_datetime,
        'duration': duration,
        'soldout': soldout,
        'repeat': repeat,
        'repeat_interval': repeat_interval,
        'fee': fee,
        'conc_fee': conc_fee,
        'multi_day_fee': multi_day_fee,
        'multi_day_conc_fee': multi_day_conc_fee,
        'venue_id': venue.id,
    }

    event_date = EventDate(**data)

    if speakers:
        for s in speakers:
            event_date.speakers.append(s)

    dao_create_event_date(event_date)
    return event_date


def create_fee(event_type_id=None, fee=5, conc_fee=3, multi_day_fee=0, multi_day_conc_fee=0, valid_from=None):
    if not event_type_id:
        event_type = create_event_type(event_type='seminar')
        event_type_id = event_type.id

    data = {
        'event_type_id': event_type_id,
        'fee': fee,
        'conc_fee': conc_fee,
        'multi_day_fee': multi_day_fee,
        'multi_day_conc_fee': multi_day_conc_fee,
        'valid_from': valid_from
    }
    fee = Fee(**data)

    dao_create_fee(fee)
    return fee


def create_token_blacklist(sample_decoded_token):
    store_token(sample_decoded_token)
    return sample_decoded_token


def create_speaker(title='Mr', name='First Mid Last-name', parent_id=None):
    data = {
        'title': title,
        'name': name,
        'parent_id': parent_id
    }

    speaker = Speaker(**data)

    dao_create_speaker(speaker)
    return speaker


def create_venue(
    old_id='1',
    name='Head office',
    address='10 London Street, N1 1NN',
    directions='By bus: 100, 111, 123',
    default=True
):
    data = {
        'old_id': old_id,
        'name': name,
        'address': address,
        'directions': directions,
        'default': default
    }

    venue = Venue(**data)

    dao_create_venue(venue)
    return venue


def create_article(
        old_id=1,
        title='Egyptians',
        author='Mrs Black',
        content='Some info about Egypt\r\n\"Something in quotes\"',
        image_filename='article.jpg',
        article_state=None,
        tags='test'
):
    data = {
        'old_id': old_id,
        'title': title,
        'author': author,
        'content': content,
        'image_filename': image_filename,
        'article_state': article_state,
        'tags': tags
    }
    article = Article(**data)

    dao_create_article(article)
    return article


def create_book(
        old_id=1,
        price='7.00',
        buy_code='112233XXYYZZ',
        title='Alchemist',
        author='Mrs Blue',
        description='Some info about Alchemy\r\n\"Something in quotes\"',
        image_filename='alchemist.jpg'
):
    data = {
        'old_id': old_id,
        'price': price,
        'buy_code': buy_code,
        'title': title,
        'author': author,
        'description': description,
        'image_filename': image_filename
    }
    book = Book(**data)

    dao_create_book(book)
    return book


def create_email(
        old_id=1,
        old_event_id=None,
        event_id=None,
        magazine_id=None,
        parent_email_id=None,
        details='test event details',
        extra_txt='test extra text',
        replace_all=False,
        email_type=EVENT,
        email_state=DRAFT,
        created_at=None,
        send_starts_at=None,
        expires=None,
        send_after=None,
        admin_email_sent_at=None,
        subject=None,
):
    if magazine_id or email_type == BASIC:
        old_event_id = None
    elif old_event_id:
        event = dao_get_event_by_old_id(old_event_id)
        if not event:
            event = create_event(old_id=old_event_id)
            create_event_date(event_id=str(event.id), event_datetime='2019-06-21 19:00')
        event_id = str(event.id)
    elif not event_id:
        event = create_event(title='test title')
        create_event_date(event_id=str(event.id), event_datetime='2019-06-21 19:00')
        event_id = str(event.id)

    data = {
        'event_id': event_id,
        'magazine_id': magazine_id,
        'parent_email_id': parent_email_id,
        'old_id': old_id,
        'old_event_id': old_event_id,
        'details': details,
        'extra_txt': extra_txt,
        'replace_all': replace_all,
        'email_type': email_type,
        'email_state': email_state,
        'created_at': created_at,
        'send_starts_at': send_starts_at,
        'expires': expires,
        'send_after': send_after,
        'admin_email_sent_at': admin_email_sent_at,
        'subject': subject
    }
    email = Email(**data)

    dao_create_email(email)
    return email


def create_magazine(
    old_id=None,
    title='title',
    old_filename=None,
    filename='new filename',
    tags='',
    topics=''
):
    data = {
        'old_id': old_id,
        'title': title,
        'old_filename': old_filename,
        'filename': filename,
        'tags': tags,
        'topics': topics
    }

    magazine = Magazine(**data)

    dao_create_record(magazine)

    return magazine


def create_marketing(
    old_id=None,
    description='Poster',
    order_number=0,
    active=True,
):
    data = {
        'old_id': old_id,
        'description': description,
        'order_number': order_number,
        'active': active,
    }

    marketing = Marketing(**data)

    dao_create_marketing(marketing)

    return marketing


def create_member(
    old_id=1,
    name='Joe Blue',
    email='test@example.com',
    active=True,
    old_marketing_id=1,
    is_course_member=False,
    created_at='2019-06-09T19:00:00',
    last_updated=None,
    marketing_id=None
):
    if not marketing_id:
        search_marketing = Marketing.query.filter_by(description='Search').first()
        if not search_marketing:
            marketing = create_marketing(description='Search')
            marketing_id = str(marketing.id)
        else:
            marketing_id = str(search_marketing.id)

    data = {
        'old_id': old_id,
        'name': name,
        'email': email,
        'active': active,
        'old_marketing_id': old_marketing_id,
        'is_course_member': is_course_member,
        'created_at': created_at,
        'last_updated': last_updated,
        'marketing_id': marketing_id
    }

    member = Member(**data)

    dao_create_member(member)

    return member


def create_email_to_member(email_id=None, member_id=None, status_code=200, email_provider_id=None, created_at=None):
    if not email_id:
        email = create_email()
        email_id = email.id
    if not member_id:
        member = create_member()
        member_id = member.id
    if not email_provider_id:
        email_provider = EmailProvider.query.first()
        if not email_provider:
            email_provider = create_email_provider()
        email_provider_id = email_provider.id
    if not created_at:
        created_at = datetime.now()

    data = {
        'created_at': created_at,
        'email_id': email_id,
        'member_id': member_id,
        'status_code': status_code,
        'email_provider_id': email_provider_id
    }

    member_to_email = EmailToMember(**data)

    dao_create_email_to_member(member_to_email)

    return member_to_email


def create_user(email='test@example.com', name='First Mid Last-name', access_area=',email,event,report,article,'):
    data = {
        'email': email,
        'name': name,
        'active': True,
        'access_area': access_area,
    }

    user = User(**data)

    dao_create_user(user)
    return user


def create_reject_reason(event_id=None, reason='Test reason', resolved=False, created_by=None):
    if not created_by:
        created_by = create_user(email='test_reject@example.com')

    data = {
        'event_id': event_id,
        'reason': reason,
        'resolved': resolved,
        'created_by': str(created_by.id)
    }

    reject_reason = RejectReason(**data)

    dao_create_reject_reason(reject_reason)

    return reject_reason


def create_order(
    old_id=1,
    created_at=None,
    member_id=None,
    old_member_id=1,
    email_address='test@example.com',
    buyer_name='Test buyer',
    txn_id='1122334455',
    txn_type='cart',
    payment_status='completed',
    payment_total=10.0,
    params='some_test_params&test_param2',
    address_street='1 Test Steeet',
    address_city='Test City',
    address_postal_code='T11 2TS',
    address_state='London',
    address_country='UK',
    address_country_code='GB',
    delivery_zone='UK',
    delivery_status='completed',
    delivery_balance=0.0,
    books=[],
    tickets=[],
    errors=[],
    linked_txn_id=None,
    email_status=None
):
    data = {
        'old_id': old_id,
        'created_at': created_at,
        'member_id': member_id,
        'old_member_id': old_member_id,
        'email_address': email_address,
        'buyer_name': buyer_name,
        'txn_id': txn_id,
        'txn_type': txn_type,
        'payment_status': payment_status,
        'payment_total': payment_total,
        'params': params,
        'address_street': address_street,
        'address_city': address_city,
        'address_postal_code': address_postal_code,
        'address_state': address_state,
        'address_country': address_country,
        'address_country_code': address_country_code,
        'delivery_zone': delivery_zone,
        'delivery_status': delivery_status,
        'delivery_balance': delivery_balance,
        'books': books,
        'tickets': tickets,
        'errors': errors,
        'email_status': email_status
    }
    if linked_txn_id:
        data.update(linked_txn_id=linked_txn_id)

    order = Order(**data)
    dao_create_record(order)

    if books:
        for book in books:
            dao_update_book_to_order_quantity(book.id, order.id, 1)

    return order


def create_ticket(
    old_id=None, event_id=None, order_id=None, eventdate_id=None,
    ticket_type=None, name=None, price=None, status=None, ticket_number=None
):
    data = {
        'old_id': old_id,
        'event_id': event_id,
        'order_id': order_id,
        'ticket_type': ticket_type,
        'eventdate_id': eventdate_id,
        'name': name,
        'price': price,
        'status': status,
        'ticket_number': ticket_number,
    }

    ticket = Ticket(**data)

    dao_create_record(ticket)

    return ticket


DATA_MAP = {
    "from": "from",
    "to": "to",
    "subject": "subject",
    "message": "text"
}


def create_email_provider(
    name='Test Email Provider', monthly_limit=None, daily_limit=25, hourly_limit=5, minute_limit=0,
    api_key='apikey', api_url='http://alt-api-url.com', pos=1,
    headers=True, auth_type=API_AUTH, as_json=False, data_map=DATA_MAP,
    smtp_server=None, smtp_user=None, smtp_password=None,
    available=False
):
    data = {
        'name': name,
        'monthly_limit': monthly_limit,
        'daily_limit': daily_limit,
        'hourly_limit': hourly_limit,
        'minute_limit': minute_limit,
        'api_key': api_key,
        'api_url': api_url,
        'data_map': json.dumps(data_map),
        'headers': headers,
        'as_json': as_json,
        'auth_type': auth_type,
        'pos': pos,
        'smtp_server': smtp_server,
        'smtp_user': smtp_user,
        'smtp_password': smtp_password,
        'available': available
    }

    email_provider = EmailProvider(**data)
    dao_create_email_provider(email_provider)
    return email_provider
