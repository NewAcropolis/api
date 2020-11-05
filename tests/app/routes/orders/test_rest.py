from flask import current_app, url_for
from freezegun import freeze_time
import pytest
import requests_mock
from mock import call

from app.dao.orders_dao import dao_get_orders
from app.dao.tickets_dao import dao_get_tickets_for_order
from app.models import Order, Ticket, TICKET_STATUS_USED, TICKET_STATUS_UNUSED
from tests.conftest import create_authorization_header
from tests.db import create_ticket

sample_ipns = [
    # single ticket
    "mc_gross=0.01&protection_eligibility=Ineligible&item_number1={id}&tax=0.00&payer_id=XXYYZZ1&payment_date="
    "10%3A00%3A00+Jan+01%2C+2018+PST&option_name2_1=Date&option_selection1_1=Concession&payment_status=Completed&"
    "charset=windows-1252&mc_shipping=0.00&mc_handling=0.00&first_name=Test&mc_fee=0.01&notify_version=3.8&custom=&"
    "payer_status=verified&business=receiver%40example.com&num_cart_items=1&mc_handling1=0.00&verify_sign=XXYYZZ1"
    ".t.sign&payer_email=test1%40example.com&mc_shipping1=0.00&tax1=0.00&btn_id1="
    "XXYYZZ1&option_name1_1=Type&txn_id={txn_id}&payment_type=instant&option_selection2_1=1&last_name=User&"
    "item_name1=Get+Inspired+-+Discover+Philosophy&receiver_email=receiver%40example.com&payment_fee=&quantity1=1&"
    "receiver_id=AABBCC1&txn_type={txn_type}&mc_gross_1=0.01&mc_currency=GBP&residence_country=GB&transaction_subject=&"
    "payment_gross=&ipn_track_id=112233",
    # multiple tickets
    "cmd=_notify-validate&mc_gross=10.00&protection_eligibility=Eligible&address_status=confirmed&item_number1={id}&"
    "item_number2={id}&payer_id=XXYYZZ2&address_street=Flat+1%2C+70+Angel+Place&payment_date=14%3A45%3A55+Jan+"
    "01%2C+2018+PDT&option_name2_1=Course+Member+name&option_name2_2=Course+Member+name&option_selection1_1=Full&"
    "payment_status=Completed&option_selection1_2=Full&charset=windows-1252&address_zip=n1+1xx&mc_shipping=0.00&"
    "first_name=Test&mc_fee=0.54&address_country_code=GB&address_name=Test+User&notify_version=3.9&custom=&"
    "payer_status=unverified&business=receiver%40example.com&address_country=United+Kingdom&num_cart_items=2&"
    "mc_handling1=0.00&mc_handling2=0.00&address_city=London&verify_sign="
    "AUl-112233&payer_email=test2%40example.com&btn_id1=XXYYZZ1&"
    "btn_id2=XXYYZZ2&option_name1_1=Type&option_name1_2=Type&txn_id={txn_id}&payment_type=instant&"
    "option_selection2_1=-&last_name=User&address_state=&option_selection2_2=-&item_name1=Philosophy+of+World&"
    "receiver_email=receiver%40example.com&item_name2=The+Mystery+Behind+the+Brain&payment_fee=&"
    "shipping_discount=0.00&quantity1=1&insurance_amount=0.00&quantity2=1&receiver_id=112233&txn_type={txn_type}&"
    "discount=0.00&mc_gross_1=5.00&mc_currency=GBP&mc_gross_2=5.00&residence_country=GB&receipt_id=112233"
    "&shipping_method=Default&transaction_subject=&payment_gross=&ipn_track_id=112233",
    # paypal card reader
    "cmd=_notify-validate&mc_gross=24.00&protection_eligibility=Ineligible&payer_id=XXYYZZ3&tax=0.00&"
    "payment_date=19%3A27%3A52+Jan+02%2C+2018+PST&payment_status=Completed&payment_method=credit_card&"
    "invoice_id=INV2-XXYYZZ&charset=windows-1252&first_name=&mc_fee=0.66&notify_version=3.9&"
    "custom=%5BCONTACTLESS_CHIP%28V%2C7102%29%40%2851.112233%2C-0."
    "112233%29%2C%2819290223020%29%5D&payer_status=unverified&"
    "business=receiver%40example.com&quantity=0&verify_sign=A3FjLTRaq2J.pY.112233-"
    "AABBCC&discount_amount=0.00&txn_id={txn_id}&payment_type=instant&last_name=&"
    "receiver_email=receiver%40example.com&payment_fee=&receiver_id=XXYYYZZ&txn_type={txn_type}&"
    "item_name=&buyer_signature=no&mc_currency=GBP&item_number=&residence_country=GB&receipt_id=112233&"
    "handling_amount=0.00&transaction_subject=&invoice_number=0001&payment_gross=&shipping=0.00&ipn_track_id="
    "112233",
    # no dates
    "mc_gross=0.01&protection_eligibility=Ineligible&item_number1={id}&tax=0.00&payer_id=XXYYZZ1&payment_date="
    "10%3A00%3A00+Oct+01%2C+2018+PST&option_selection1_1=Concession&payment_status=Completed&"
    "charset=windows-1252&mc_shipping=0.00&mc_handling=0.00&first_name=Test&mc_fee=0.01&notify_version=3.8&custom=&"
    "payer_status=verified&business=receiver%40example.com&num_cart_items=1&mc_handling1=0.00&verify_sign=XXYYZZ1"
    ".t.sign&payer_email=test1%40example.com&mc_shipping1=0.00&tax1=0.00&btn_id1="
    "XXYYZZ1&option_name1_1=Type&txn_id={txn_id}&payment_type=instant&last_name=User&"
    "item_name1=Get+Inspired+-+Discover+Philosophy&receiver_email=receiver%40example.com&payment_fee=&quantity1=1&"
    "receiver_id=AABBCC1&txn_type={txn_type}&mc_gross_1=0.01&mc_currency=GBP&residence_country=GB&transaction_subject=&"
    "payment_gross=&ipn_track_id=112233"
]


sample_incomplete_ipn = (
    "mc_gross=0.01&protection_eligibility=Ineligible&item_number1={id}&tax=0.00&payer_id=XXYYZZ1&payment_date="
    "10%3A00%3A00+Jan+01%2C+2019+PST&option_name2_1=Date&option_selection1_1=Concession&payment_status=Incomplete&"
    "charset=windows-1252&mc_shipping=0.00&mc_handling=0.00&first_name=Test&mc_fee=0.01&notify_version=3.8&custom=&"
    "payer_status=verified&business=receiver%40example.com&num_cart_items=1&mc_handling1=0.00&verify_sign=XXYYZZ1"
    ".t.sign&payer_email=test1%40example.com&mc_shipping1=0.00&tax1=0.00&btn_id1="
    "XXYYZZ1&option_name1_1=Type&txn_id=112233&payment_type=instant&option_selection2_1=1&last_name=User&"
    "item_name1=Get+Inspired+-+Discover+Philosophy&receiver_email=receiver%40example.com&payment_fee=&quantity1=1&"
    "receiver_id=AABBCC1&txn_type={txn_type}&mc_gross_1=0.01&mc_currency=GBP&residence_country=GB&transaction_subject=&"
    "payment_gross=&ipn_track_id=112233"
)


sample_wrong_receiver = (
    "mc_gross=0.01&protection_eligibility=Ineligible&item_number1={id}&tax=0.00&payer_id=XXYYZZ1&payment_date="
    "10%3A00%3A00+Jan+01%2C+2018+PST&option_name2_1=Date&option_selection1_1=Concession&payment_status=Completed&"
    "charset=windows-1252&mc_shipping=0.00&mc_handling=0.00&first_name=Test&mc_fee=0.01&notify_version=3.8&custom=&"
    "payer_status=verified&business=receiver%40example.com&num_cart_items=1&mc_handling1=0.00&verify_sign=XXYYZZ1"
    ".t.sign&payer_email=test1%40example.com&mc_shipping1=0.00&tax1=0.00&btn_id1="
    "XXYYZZ1&option_name1_1=Type&txn_id=112233&payment_type=instant&option_selection2_1=1&last_name=User&"
    "item_name1=Get+Inspired+-+Discover+Philosophy&receiver_email=another%40example.com&payment_fee=&quantity1=1&"
    "receiver_id=AABBCC1&txn_type=Cart&mc_gross_1=0.01&mc_currency=GBP&residence_country=GB&transaction_subject=&"
    "payment_gross=&ipn_track_id=112233"
)


sample_invalid_date = (
    "mc_gross=0.01&protection_eligibility=Ineligible&item_number1={id}&tax=0.00&payer_id=XXYYZZ1&payment_date="
    "10%3A00%3A00+Jan+01%2C+2018+PST&option_name2_1=Date&option_selection1_1=Concession&payment_status=Completed&"
    "charset=windows-1252&mc_shipping=0.00&mc_handling=0.00&first_name=Test&mc_fee=0.01&notify_version=3.8&custom=&"
    "payer_status=verified&business=receiver%40example.com&num_cart_items=1&mc_handling1=0.00&verify_sign=XXYYZZ1"
    ".t.sign&payer_email=test1%40example.com&mc_shipping1=0.00&tax1=0.00&btn_id1="
    "XXYYZZ1&option_name1_1=Type&txn_id=112233&payment_type=instant&option_selection2_1=3&last_name=User&"
    "item_name1=Get+Inspired+-+Discover+Philosophy&receiver_email=receiver%40example.com&payment_fee=&quantity1=1&"
    "receiver_id=AABBCC1&txn_type=Cart&mc_gross_1=0.01&mc_currency=GBP&residence_country=GB&transaction_subject=&"
    "payment_gross=&ipn_track_id=112233"
)


class WhenHandlingPaypalIPN:
    def it_creates_orders_and_event_tickets(self, mocker, client, db_session, sample_event_with_dates):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
        txn_ids = ['112233', '112244', '112255', '112266']
        txn_types = ['cart', 'cart', 'paypal_here', 'cart']
        num_tickets = [1, 2, 1, 1]

        for i in range(len(txn_ids)):
            _sample_ipn = sample_ipns[i].format(
                id=sample_event_with_dates.id, txn_id=txn_ids[i], txn_type=txn_types[i])

            with requests_mock.mock() as r:
                r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

                client.post(
                    url_for('orders.paypal_ipn'),
                    data=_sample_ipn,
                    content_type="application/x-www-form-urlencoded"
                )

        orders = dao_get_orders()
        assert len(orders) == 4
        for i in range(len(sample_ipns)):
            assert orders[i].txn_id == txn_ids[i]
            assert orders[i].txn_type == txn_types[i]

            tickets = dao_get_tickets_for_order(orders[i].id)
            assert len(tickets) == num_tickets[i]

            for n in range(num_tickets[i]):
                assert 'http://test/images/qr_codes/{}'.format(
                    str(tickets[n].id)) in mock_send_email.call_args_list[i][0][2]

    def it_creates_a_book_order(self, mocker, client, db_session, sample_event_with_dates):
        # mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
        # txn_ids = ['112233', '112244', '112255', '112266']
        # txn_types = ['cart', 'cart', 'paypal_here', 'cart']
        # num_tickets = [1, 2, 1, 1]
        pass

    def it_creates_a_mixed_order(self, mocker, client, db_session):
        pass

    def it_does_not_create_an_order_if_payment_not_complete(self, mocker, client, db_session):
        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=sample_incomplete_ipn,
                content_type="application/x-www-form-urlencoded"
            )
        orders = dao_get_orders()
        assert not orders

    @pytest.mark.parametrize('resp', ['INVALID', 'UNKNOWN'])
    def it_does_not_create_an_order_if_not_verified(self, mocker, client, db_session, sample_event_with_dates, resp):
        sample_ipn = sample_ipns[0].format(
            id=sample_event_with_dates.id, txn_id='112233', txn_type='Cart')

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text=resp)

            client.post(
                url_for('orders.paypal_ipn'),
                data=sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )
        orders = dao_get_orders()
        assert not orders

    def it_does_not_create_an_order_if_wrong_receiver(self, mocker, client, db_session, sample_event):
        mock_logger = mocker.patch('app.routes.orders.rest.current_app.logger.error')
        sample_ipn = sample_wrong_receiver.format(id=sample_event.id)
        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )
        orders = dao_get_orders()
        assert not orders
        assert mock_logger.call_args == call('Paypal receiver not valid: %s for %s', u'another@example.com', u'112233')

    def it_does_not_create_an_order_if_no_event_matched(self, mocker, client, db_session, sample_uuid):
        mock_logger = mocker.patch('app.routes.orders.rest.current_app.logger.error')
        sample_ipn = sample_ipns[0].format(
            id=sample_uuid, txn_id='112233', txn_type='Cart')

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )
        orders = dao_get_orders()
        assert mock_logger.call_args == call('No valid tickets, no order created: %s', u'112233')
        assert not orders

    def it_does_not_create_an_order_if_invalid_event_date(self, mocker, client, db_session, sample_event_with_dates):
        sample_ipn = sample_invalid_date.format(id=sample_event_with_dates.id)

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )
        orders = dao_get_orders()
        assert not orders

    def it_does_not_create_orders_with_duplicate_txn_ids(self, mocker, client, db_session, sample_event_with_dates):
        txn_ids = ['112233', '112233']
        txn_types = ['cart', 'cart']

        for i in range(len(txn_ids)):
            _sample_ipn = sample_ipns[i].format(
                id=sample_event_with_dates.id, txn_id=txn_ids[i], txn_type=txn_types[i])

            with requests_mock.mock() as r:
                r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

                client.post(
                    url_for('orders.paypal_ipn'),
                    data=_sample_ipn,
                    content_type="application/x-www-form-urlencoded"
                )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert orders[0].txn_id == txn_ids[0]
        assert orders[0].txn_type == txn_types[0]

        tickets = dao_get_tickets_for_order(orders[0].id)
        assert len(tickets) == 1


class WhenProcessingTicket:

    @pytest.fixture(scope='function')
    def sample_ticket(self, db_session, sample_event_with_dates):
        return create_ticket(
            event_id=sample_event_with_dates.id,
            old_id=1,
            eventdate_id=sample_event_with_dates.get_sorted_event_dates()[0]['id']
        )

    @freeze_time("2018-01-01T19:00:00")
    def it_updates_ticket_to_used(self, client, sample_ticket):
        response = client.get(
            url_for('orders.use_ticket', ticket_id=sample_ticket.id),
            content_type="application/x-www-form-urlencoded",
        )

        assert sample_ticket.status == TICKET_STATUS_USED
        assert response.json == {
            'ticket_id': str(sample_ticket.id),
            'title': sample_ticket.event.title,
            'update_response': 'Ticket updated to used'
        }

    @freeze_time("2018-01-01T19:00:00")
    def it_updates_ticket_to_used_with_old_id(self, client, sample_ticket):
        response = client.get(
            url_for('orders.use_ticket', ticket_id=str(sample_ticket.old_id)),
            content_type="application/x-www-form-urlencoded",
        )

        assert sample_ticket.status == TICKET_STATUS_USED
        assert response.json == {
            'ticket_id': str(sample_ticket.old_id),
            'title': sample_ticket.event.title,
            'update_response': 'Ticket updated to used'
        }

    def it_does_not_update_ticket_if_not_event_date(self, client, sample_ticket):
        response = client.get(
            url_for('orders.use_ticket', ticket_id=sample_ticket.id),
            content_type="application/x-www-form-urlencoded",
        )

        assert sample_ticket.status == TICKET_STATUS_UNUSED
        assert response.json == {
            'ticket_id': str(sample_ticket.id),
            'title': sample_ticket.event.title,
            'update_response': 'Event is not today'
        }

    @freeze_time("2018-01-01T19:00:00")
    def it_does_not_update_ticket_to_used_if_used(self, db_session, client, sample_event_with_dates):
        event_dates = sample_event_with_dates.get_sorted_event_dates()
        ticket = create_ticket(
            status=TICKET_STATUS_USED,
            event_id=sample_event_with_dates.id,
            eventdate_id=event_dates[0]['id']
        )
        response = client.get(
            url_for('orders.use_ticket', ticket_id=ticket.id),
            content_type="application/x-www-form-urlencoded",
        )

        assert response.json == {
            'ticket_id': str(ticket.id),
            'title': ticket.event.title,
            'update_response': 'Ticket already used'
        }
