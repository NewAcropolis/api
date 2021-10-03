from freezegun import freeze_time

from app.dao import dao_create_record
from app.models import MAGAZINE, TICKET_STATUS_UNUSED, OrderError
from app.utils.time import get_local_time
from tests.db import (
    create_article,
    create_book,
    create_event,
    create_email,
    create_fee,
    create_order,
    create_speaker,
    create_ticket
)


class WhenUsingEventModel(object):

    def it_shows_event_info_id_on_str(self, db, db_session):
        event = create_event()

        assert str(event) == '<Event: id {}>'.format(event.id)


class WhenUsingFeeModel(object):

    def it_shows_fee_json_on_serialize(self, db, db_session):
        fee = create_fee(fee=5, conc_fee=3)

        assert fee.serialize() == {
            'id': str(fee.id),
            'event_type_id': str(fee.event_type_id),
            'fee': fee.fee,
            'conc_fee': fee.conc_fee,
            'multi_day_fee': fee.multi_day_fee,
            'multi_day_conc_fee': fee.multi_day_conc_fee,
            'valid_from': fee.valid_from.isoformat()
        }


class WhenUsingSpeakerModel(object):

    def it_shows_speaker_json_on_serialize(self, db, db_session):
        speaker = create_speaker()

        assert speaker.serialize() == {
            'id': str(speaker.id),
            'title': speaker.title,
            'name': speaker.name,
            'parent_id': None
        }

    def it_gets_last_name_correctly(self, db, db_session):
        speaker = create_speaker(name='John Smith')

        assert speaker.last_name == 'Smith'


class WhenUsingArticleModel(object):

    def it_shows_article_summary_json_on_serialize(self, db, db_session):
        article = create_article()

        assert article.serialize_summary() == {
            'id': str(article.id),
            'author': article.author,
            'title': article.title,
            'short_content': article.content,
            'very_short_content': article.content,
            'image_filename': 'article.jpg'
        }

    def it_shows_shortened_content_article_summary_json_on_serialize_long_content(self, db_session):
        long_content = ''
        short_content_length = 0
        very_short_content_length = 0
        for i in range(120):
            long_content += '{}some-text '.format(i)
            if i == 30:
                very_short_content_length = len(long_content) - 1
            if i == 110:
                short_content_length = len(long_content) - 1

        article = create_article(content=long_content)

        assert article.serialize_summary() == {
            'id': str(article.id),
            'author': article.author,
            'title': article.title,
            'short_content': long_content[:short_content_length] + '...',
            'very_short_content': long_content[:very_short_content_length] + '...',
            'image_filename': 'article.jpg'
        }

    def it_removes_html_tags_on_article_summary(self, db_session):
        long_content_with_tags = '<h1>'
        clean_long_content = ''
        clean_very_short_content_length = 0
        clean_short_content_length = 0
        for i in range(120):
            long_content_with_tags += '{}<div>text</div> '.format(i)
            clean_long_content += '{}text '.format(i)
            if i == 30:
                clean_very_short_content_length = len(clean_long_content) - 1
            if i == 110:
                clean_short_content_length = len(clean_long_content) - 1

        article = create_article(content=long_content_with_tags)

        assert article.serialize_summary() == {
            'id': str(article.id),
            'author': article.author,
            'title': article.title,
            'short_content': clean_long_content[:clean_short_content_length] + '...',
            'very_short_content': clean_long_content[:clean_very_short_content_length] + '...',
            'image_filename': 'article.jpg'
        }


class WhenUsingBookModel(object):

    def it_shows_book_json_on_serialize(self, db_session):
        book = create_book()

        assert book.serialize() == {
            'id': str(book.id),
            'old_id': book.old_id,
            'price': str(book.price),
            'buy_code': book.buy_code,
            'author': book.author,
            'title': book.title,
            'description': book.description,
            'image_filename': book.image_filename,
            'created_at': get_local_time(book.created_at).strftime('%Y-%m-%d')
        }


class WhenUsingEmailModel:
    def it_shows_email_json_on_serialize(self, db, db_session):
        email = create_email(
            created_at='2019-06-01T10:00:00', send_starts_at='2019-06-02T11:00:00', send_after='2019-06-02T12:00:00')

        assert email.serialize() == {
            'id': str(email.id),
            'subject': 'workshop: test title',
            'event_id': str(email.event_id),
            'magazine_id': None,
            'old_id': email.old_id,
            'old_event_id': email.old_event_id,
            'created_at': get_local_time(email.created_at).strftime('%Y-%m-%d %H:%M'),
            'extra_txt': u'test extra text',
            'details': u'test event details',
            'replace_all': False,
            'email_type': u'event',
            'email_state': u'draft',
            'send_starts_at': '2019-06-02',
            'expires': '2019-06-21',
            'send_after': get_local_time(email.send_after).strftime('%Y-%m-%d %H:%M'),
            'emails_sent_counts': {
                'success': 0,
                'failed': 0,
                'total_active_members': 0
            }
        }

    def it_shows_magazine_email_json_on_serialize(self, db, db_session, sample_magazine):
        email = create_email(
            email_type=MAGAZINE, magazine_id=sample_magazine.id,
            old_event_id=None,
            created_at='2019-06-30T10:00:00', send_starts_at='2019-07-01T11:00:00')

        assert email.serialize() == {
            'id': str(email.id),
            'subject': u'New Acropolis bi-monthly magazine: Test magazine',
            'event_id': None,
            'magazine_id': str(sample_magazine.id),
            'old_id': email.old_id,
            'old_event_id': None,
            'created_at': get_local_time(email.created_at).strftime('%Y-%m-%d %H:%M'),
            'extra_txt': u'test extra text',
            'details': u'test event details',
            'replace_all': False,
            'email_type': u'magazine',
            'email_state': u'draft',
            'send_starts_at': '2019-07-01',
            'expires': '2019-07-15',
            'send_after': None,
            'emails_sent_counts': {
                'success': 0,
                'failed': 0,
                'total_active_members': 0
            }
        }


class WhenUsingOrderModel:
    @freeze_time("2021-06-07T23:00:00")
    def it_shows_order_serialized(self, db_session, sample_book, sample_event_with_dates):
        book = create_book(
            old_id=None,
            price='7.00',
            buy_code='112233AABBCC',
            title='Nature',
            author='Mr White',
            description='Some info about Nature\r\n\"Something in quotes\"',
            image_filename='nature.jpg'
        )

        event_dates = sample_event_with_dates.get_sorted_event_dates()
        ticket = create_ticket(
            status=TICKET_STATUS_UNUSED,
            event_id=sample_event_with_dates.id,
            eventdate_id=event_dates[0]['id']
        )

        order = create_order(books=[sample_book, book], tickets=[ticket])

        error = OrderError(error='Test error', order_id=order.id)
        dao_create_record(error)

        assert order.serialize() == {
            'id': str(order.id),
            'txn_id': order.txn_id,
            'txn_type': order.txn_type,
            'buyer_name': order.buyer_name,
            'created_at': get_local_time(order.created_at).strftime('%Y-%m-%d %H:%M'),
            'payment_status': order.payment_status,
            'payment_total': str(order.payment_total),
            'address_country_code': order.address_country_code,
            'address_street': order.address_street,
            'address_city': order.address_city,
            'address_postal_code': order.address_postal_code,
            'address_state': order.address_state,
            'address_country': order.address_country,
            'delivery_zone': order.delivery_zone,
            'delivery_status': order.delivery_status,
            'delivery_sent': order.delivery_sent,
            'refund_issued': order.refund_issued,
            'delivery_balance': str(order.delivery_balance),
            'notes': order.notes,
            'books': [
                {
                    'id': str(book.id),
                    'price': str(book.price),
                    'buy_code': book.buy_code,
                    'image_filename': book.image_filename,
                    'old_id': book.old_id,
                    'title': book.title,
                    'author': book.author,
                    'description': book.description,
                    'quantity': 1
                },
                {
                    'id': str(sample_book.id),
                    'price': str(sample_book.price),
                    'buy_code': sample_book.buy_code,
                    'image_filename': sample_book.image_filename,
                    'old_id': sample_book.old_id,
                    'title': sample_book.title,
                    'author': sample_book.author,
                    'description': sample_book.description,
                    'quantity': 1
                },
            ],
            'tickets': [
                {
                    'id': str(ticket.id),
                    'event_id': str(ticket.event_id),
                    'old_id': ticket.old_id,
                    'ticket_type': ticket.ticket_type,
                    'eventdate_id': str(ticket.eventdate_id),
                    'name': order.buyer_name,
                    'price': ticket.price,
                    'last_updated': get_local_time(ticket.last_updated).strftime('%Y-%m-%d %H:%M'),
                    'created_at': get_local_time(ticket.created_at).strftime('%Y-%m-%d %H:%M'),
                    'status': ticket.status,
                    'ticket_number': ticket.ticket_number,
                    'event': {
                        'booking_code': None,
                        'conc_fee': 3,
                        'description': 'test description',
                        'event_state': 'draft',
                        'event_type': 'workshop',
                        'event_type_id': str(sample_event_with_dates.event_type_id),
                        'fee': 5,
                        'has_expired': True,
                        'show_banner_text': True,
                        'id': str(sample_event_with_dates.id),
                        'image_filename': None,
                        'multi_day_conc_fee': 10,
                        'multi_day_fee': 12,
                        'old_id': 1,
                        'reject_reasons': [],
                        'sub_title': None,
                        'title': 'test_title',
                        'venue': {'address': '10 London Street, N1 1NN',
                                  'default': True,
                                  'directions': 'By bus: 100, 111, 123',
                                  'id': str(sample_event_with_dates.venue.id),
                                  'name': 'Head office',
                                  'old_id': 1}
                    },
                    'event_date': {
                        'end_time': None,
                        'event_datetime': '2018-01-01 19:00',
                        'event_id': str(ticket.event_id),
                        'id': str(ticket.event_date.id),
                        'speakers': []
                    },
                }
            ],
            'errors': [
                {
                    'error': 'Test error',
                    'id': str(error.id)
                }
            ]
        }
