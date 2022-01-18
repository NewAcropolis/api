from flask import current_app, url_for
from freezegun import freeze_time
import json
import pytest
import requests_mock
from mock import call
from urllib.parse import parse_qs

from app.dao.orders_dao import dao_get_orders
from app.dao.tickets_dao import dao_get_tickets_for_order
from app.models import Order, OrderError, Ticket, TICKET_STATUS_USED, TICKET_STATUS_UNUSED
from na_common.delivery import statuses as delivery_statuses
from tests.conftest import create_authorization_header
from tests.db import create_ticket, create_order

sample_ipns = [
    # single ticket
    "mc_gross=190.00&protection_eligibility=Ineligible&item_number1={id}&tax=0.00&payer_id=XXYYZZ1&payment_date="
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

sample_all_dates = (
    "mc_gross=0.01&protection_eligibility=Ineligible&item_number1={id}&tax=0.00&payer_id=XXYYZZ1&payment_date="
    "10%3A00%3A00+Jan+01%2C+2018+PST&option_name2_1=Date&option_selection1_1=Concession&payment_status=Completed&"
    "charset=windows-1252&mc_shipping=0.00&mc_handling=0.00&first_name=Test&mc_fee=0.01&notify_version=3.8&custom=&"
    "payer_status=verified&business=receiver%40example.com&num_cart_items=1&mc_handling1=0.00&verify_sign=XXYYZZ1"
    ".t.sign&payer_email=test1%40example.com&mc_shipping1=0.00&tax1=0.00&btn_id1="
    "XXYYZZ1&option_name1_1=Type&txn_id=112233&payment_type=instant&option_selection2_1=all&last_name=User&"
    "item_name1=Get+Inspired+-+Discover+Philosophy&receiver_email=receiver%40example.com&payment_fee=&quantity1=1&"
    "receiver_id=AABBCC1&txn_type=Cart&mc_gross_1=0.01&mc_currency=GBP&residence_country=GB&transaction_subject=&"
    "payment_gross=&ipn_track_id=112233"
)

sample_book_order_ipn = (
    "_notify-validate&mc_gross=10.00&protection_eligibility=Eligible&address_status=confirmed&"
    "item_number1={book_id}&item_number2={delivery_id}&payer_id=XXYYZZ&address_street=Flat+1%2C+1+Test+Place&"
    "payment_date=14%3A45%3A55+Jan+10%2C+2021+PDT&option_name2_1=Course+Member+name&option_name2_2=Course+Member+name&"
    "option_selection1_1=Full&payment_status=Completed&option_selection1_2={delivery_zone}&charset=windows-1252&"
    "address_zip=n1+1aa&mc_shipping=0.00&first_name=TestName&mc_fee=0.54&"
    "address_country_code={country_code}&address_name=Test+Name"
    "&notify_version=3.9&custom=&payer_status=unverified&business=test%40test.com&address_country=United+Kingdom"
    "&um_cart_items=2&mc_handling1=0.00&nmc_handling2=0.00&address_city=London&verify_sign=AXl-"
    "x13NMy7f84hsUb1AfdPySBVSAn5cuQjLRnnBnlH2cpx64XuK5l34&payer_email={payer_email}&btn_id1=123456789&"
    "btn_id2=012345678&option_name1_1=Type&option_name1_2=Type&txn_id=1122334455&payment_type=instant&"
    "option_selection2_1=-&last_name=Test&address_state=&option_selection2_2=-&item_name1=Philosophy+Test"
    "&receiver_email=receiver%40example.com&item_name2=Postage&payment_fee=&shipping_discount=0.00&quantity1=1&"
    "insurance_amount=0.00&quantity2=1&receiver_id=11223344&txn_type=cart&discount=0.00&mc_gross_1=5.00&mc_currency=GBP"
    "&mc_gross_2=5.00&residence_country=GB&receipt_id=0000-1111-2222-3333&shipping_method=Default&"
    "transaction_subject=&payment_gross=&ipn_track_id=1122334455aa"
)

sample_double_book_order_ipn = (
    "_notify-validate&mc_gross=10.00&protection_eligibility=Eligible&address_status=confirmed&"
    "item_number1={book_id}&item_number2={delivery_id}&payer_id=XXYYZZ&address_street=Flat+1%2C+1+Test+Place&"
    "payment_date=14%3A45%3A55+Jan+10%2C+2021+PDT&option_name2_1=Course+Member+name&option_name2_2=Course+Member+name&"
    "option_selection1_1=Full&payment_status=Completed&option_selection1_2={delivery_zone}&charset=windows-1252&"
    "address_zip=n1+1aa&mc_shipping=0.00&first_name=TestName&mc_fee=0.54&"
    "address_country_code={country_code}&address_name=Test+Name"
    "&notify_version=3.9&custom=&payer_status=unverified&business=test%40test.com&address_country=United+Kingdom"
    "&um_cart_items=3&mc_handling1=0.00&nmc_handling2=0.00&address_city=London&verify_sign=AXl-"
    "x13NMy7f84hsUb1AfdPySBVSAn5cuQjLRnnBnlH2cpx64XuK5l34&payer_email={payer_email}&btn_id1=123456789&"
    "btn_id2=012345678&option_name1_1=Type&option_name1_2=Type&txn_id=1122334455&payment_type=instant&"
    "option_selection2_1=-&last_name=Test&address_state=&option_selection2_2=-&item_name1=Philosophy+Test"
    "&receiver_email=receiver%40example.com&item_name2=Postage&payment_fee=&shipping_discount=0.00&quantity1=1&"
    "insurance_amount=0.00&quantity2=1&receiver_id=11223344&txn_type=cart&discount=0.00&mc_gross_1=5.00&mc_currency=GBP"
    "&mc_gross_2=5.00&residence_country=GB&receipt_id=0000-1111-2222-3333&shipping_method=Default&"
    "transaction_subject=&payment_gross=&ipn_track_id=1122334455aa&item_number3={book_id}&item_name3=Philosophy+Test2"
    "&mc_gross_3=5.00&quantity3=1"
)

sample_book_order_without_delivery_ipn = (
    "_notify-validate&mc_gross=10.00&protection_eligibility=Eligible&address_status=confirmed&"
    "item_number1={book_id}&payer_id=XXYYZZ&address_street=Flat+1%2C+1+Test+Place&"
    "payment_date=14%3A45%3A55+Jan+10%2C+2021+PDT&option_name2_1=Course+Member+name&option_name2_2=Course+Member+name&"
    "option_selection1_1=Full&payment_status=Completed&option_selection1_2=Full&charset=windows-1252&"
    "address_zip=n1+1aa&mc_shipping=0.00&first_name=TestName&mc_fee=0.54&"
    "address_country_code={country_code}&address_name=Test+Name"
    "&notify_version=3.9&custom=&payer_status=unverified&business=test%40test.com&address_country=United+Kingdom"
    "&um_cart_items=1&mc_handling1=0.00&nmc_handling2=0.00&address_city=London&verify_sign=AXl-"
    "x13NMy7f84hsUb1AfdPySBVSAn5cuQjLRnnBnlH2cpx64XuK5l34&payer_email={payer_email}&btn_id1=123456789&"
    "option_name1_1=Type&txn_id=1122334455&payment_type=instant&"
    "option_selection2_1=-&last_name=Test&address_state=&item_name1=Philosophy+Test"
    "&receiver_email=receiver%40example.com&payment_fee=&shipping_discount=0.00&quantity1=1&"
    "insurance_amount=0.00&receiver_id=11223344&txn_type=cart&discount=0.00&mc_gross_1=5.00&mc_currency=GBP"
    "&residence_country=GB&receipt_id=0000-1111-2222-3333&shipping_method=Default&"
    "transaction_subject=&payment_gross=&ipn_track_id=1122334455aa"
)

sample_book_order_multiple_delivery_ipn = (
    "_notify-validate&mc_gross=10.00&protection_eligibility=Eligible&address_status=confirmed&item_number1={book_id}&"
    "item_number2={delivery_id}&item_number3={delivery_id}&payer_id=XXYYZZ&address_street=Flat+1%2C+1+Test+Place&"
    "payment_date=14%3A45%3A55+Jan+10%2C+2021+PDT&option_name2_1=Course+Member+name&option_name2_2=Course+Member+name&"
    "option_selection1_1=Full&payment_status=Completed&option_selection1_2={delivery_zone}&charset=windows-1252&"
    "address_zip=n1+1aa&mc_shipping=0.00&first_name=TestName&mc_fee=0.54&"
    "address_country_code={country_code}&address_name=Test+Name"
    "&notify_version=3.9&custom=&payer_status=unverified&business=test%40test.com&address_country=United+Kingdom"
    "&um_cart_items=2&mc_handling1=0.00&nmc_handling2=0.00&address_city=London&verify_sign=AXl-"
    "x13NMy7f84hsUb1AfdPySBVSAn5cuQjLRnnBnlH2cpx64XuK5l34&payer_email={payer_email}&btn_id1=123456789&btn_id2="
    "012345678&option_name1_1=Type&option_name1_2=Type&txn_id=1122334455&payment_type=instant&option_selection2_1=-&"
    "last_name=Test&address_state=&option_selection2_2=-&item_name1=Philosophy+Test&receiver_email=receiver%40example"
    ".com&item_name2=Postage&item_name3=Postage&payment_fee=&shipping_discount=0.00&quantity1=1&"
    "insurance_amount=0.00&quantity2=1&quantity3=1&receiver_id=11223344&txn_type=cart&discount=0.00&mc_gross_1=5.00"
    "&mc_currency=GBP&mc_gross_2=5.00&mc_gross_3=5.00&residence_country=GB&receipt_id=0000-1111-2222-3333&"
    "shipping_method=Default&transaction_subject=&payment_gross=&ipn_track_id=1122334455aa"
    "&option_selection1_3={delivery_zone}&option_name1_3=Postage"
)

sample_mixed_order_ipn = (
    "_notify-validate&mc_gross=10.00&protection_eligibility=Eligible&address_status=confirmed&"
    "item_number1={book_id}&item_number2={delivery_id}&item_number3={event_id}"
    "&payer_id=XXYYZZ&address_street=Flat+1%2C+1+Test+Place&"
    "payment_date=14%3A45%3A55+Jan+10%2C+2021+PDT&"
    "option_name1_1=Type&option_name1_2=Type&option_name2_1=Course+Member+name&option_name3_1"
    "&option_selection1_3=Full&option_selection1_2={delivery_zone}&option_selection3_2=Full&"
    "option_selection2_1=-&option_selection3_1=Full&option_selection2_3=1&option_selection2_2=-"
    "&payment_status=Completed&charset=windows-1252&"
    "address_zip=n1+1aa&mc_shipping=0.00&first_name=TestName&mc_fee=0.54&"
    "address_country_code={country_code}&address_name=Test+Name"
    "&notify_version=3.9&custom=&payer_status=unverified&business=test%40test.com&address_country=United+Kingdom"
    "&um_cart_items=3&mc_handling1=0.00&nmc_handling2=0.00&address_city=London&verify_sign=AXl-"
    "x13NMy7f84hsUb1AfdPySBVSAn5cuQjLRnnBnlH2cpx64XuK5l34&payer_email={payer_email}&"
    "btn_id1=123456789&btn_id2=212345678&btn_id3=312345678&"
    "txn_id=1122334455&payment_type=instant&"
    "last_name=Test&address_state=&option_selection2_2=-&"
    "item_name1=Philosophy+Book&item_name2=Postage&item_name3=Philosophy+Event"
    "&receiver_email=receiver%40example.com&payment_fee=&shipping_discount=0.00&"
    "insurance_amount=0.00&receiver_id=11223344&txn_type=cart&discount=0.00&"
    "quantity1=1&quantity2=1&quantity3=1&mc_gross_1=5.00&mc_gross_2=5.00&mc_gross_3=10.00"
    "&mc_currency=GBP&residence_country=GB&receipt_id=0000-1111-2222-3333&shipping_method=Default&"
    "transaction_subject=&payment_gross=&ipn_track_id=1122334455aa"
)

sample_book_order_without_address_ipn = (
    "_notify-validate&mc_gross=10.00&protection_eligibility=Eligible&address_status=confirmed&"
    "item_number1={book_id}&item_number2={delivery_id}&payer_id=XXYYZZ&address_street=Flat+1%2C+1+Test+Place&"
    "payment_date=14%3A45%3A55+Jan+10%2C+2021+PDT&option_name2_1=Course+Member+name&option_name2_2=Course+Member+name&"
    "option_selection1_1=Full&payment_status=Completed&option_selection1_2=Full&charset=windows-1252&"
    "mc_shipping=0.00&first_name=TestName&mc_fee=0.54&"
    "&notify_version=3.9&custom=&payer_status=unverified&business=test%40test.com"
    "&um_cart_items=2&mc_handling1=0.00&nmc_handling2=0.00&verify_sign=AXl-"
    "x13NMy7f84hsUb1AfdPySBVSAn5cuQjLRnnBnlH2cpx64XuK5l34&payer_email={payer_email}&btn_id1=123456789&"
    "btn_id2=012345678&option_name1_1=Type&option_name1_2=Type&txn_id=1122334455&payment_type=instant&"
    "option_selection2_1=-&last_name=Test&option_selection2_2=-&item_name1=Philosophy+Test"
    "&receiver_email=receiver%40example.com&item_name2={delivery_zone}&payment_fee=&shipping_discount=0.00&quantity1=1&"
    "insurance_amount=0.00&quantity2=1&receiver_id=11223344&txn_type=cart&discount=0.00&mc_gross_1=5.00&mc_currency=GBP"
    "&mc_gross_2=5.00&residence_country=GB&receipt_id=0000-1111-2222-3333&shipping_method=Default&"
    "transaction_subject=&payment_gross=&ipn_track_id=1122334455aa"
)

sample_complete_order_ipn = (
    "_notify-validate&mc_gross={linked_payment}&protection_eligibility=Eligible&address_status=confirmed&"
    "item_number1={delivery_id}&payer_id=XXYYZZ&address_street=Flat+1%2C+1+Test+Place&"
    "payment_date=14%3A45%3A55+Jan+10%2C+2021+PDT&charset=windows-1252&"
    "payment_status=Completed&address_zip=n1+1aa&mc_shipping=0.00&first_name=TestName&last_name=User&mc_fee=0.54&"
    "address_country_code={country_code}&address_name=Test+Name"
    "&notify_version=3.9&custom={linked_txn_id}&payer_status=unverified&business=test%40test.com&"
    "address_country=United+Kingdom&address_city=London&verify_sign=AXl-"
    "x13NMy7f84hsUb1AfdPySBVSAn5cuQjLRnnBnlH2cpx64XuK5l34&payer_email={payer_email}"
    "&txn_id=2233445566&payment_type=instant&"
    "item_name1=UK"
    "&receiver_email=receiver%40example.com&payment_fee=&shipping_discount=0.00&quantity1=1&"
    "insurance_amount=0.00&receiver_id=11223344&txn_type=web_accept&discount=0.00&mc_gross_1=5.00&mc_currency=GBP"
    "0&residence_country=GB&receipt_id=0000-1111-2222-3333&shipping_method=Default&"
    "transaction_subject=&payment_gross=&ipn_track_id=1122334455aa"
)


@pytest.fixture(scope='function')
def mock_storage(mocker):
    mocker.patch('app.routes.orders.rest.Storage')
    mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')


class WhenHandlingPaypalIPN:
    def it_creates_orders_and_event_tickets_with_test_verify_flag(
        self, mocker, client, db_session, sample_event_with_dates
    ):
        mocker.patch.dict('app.application.config', {
            'TEST_VERIFY': True,
            'ENVIRONMENT': 'test'
        })

        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        txn_ids = ['112233', '112244', '112255', '112266']
        txn_types = ['cart', 'cart', 'paypal_here', 'cart']
        num_tickets = [1, 2, 1, 1]

        for i in range(len(txn_ids)):
            _sample_ipn = sample_ipns[i].format(
                id=sample_event_with_dates.id, txn_id=txn_ids[i], txn_type=txn_types[i])

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

    def it_creates_orders_and_event_tickets_on_replay(self, mocker, client, db_session, sample_event_with_dates):
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
                    url_for('orders.replay_paypal_ipn'),
                    data=_sample_ipn,
                    content_type="application/x-www-form-urlencoded",
                    headers=[
                        ('Content-Type', 'application/json'),
                        create_authorization_header(),
                        ('Allow-emails', 'true')
                    ]
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

    def it_replaces_existing_orders_and_event_tickets_on_replay(
        self, mocker, client, db_session, sample_event_with_dates
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        event_dates = sample_event_with_dates.get_sorted_event_dates()
        ticket = create_ticket(
            status=TICKET_STATUS_UNUSED,
            event_id=sample_event_with_dates.id,
            eventdate_id=event_dates[0]['id']
        )
        ticket2 = create_ticket(
            status=TICKET_STATUS_UNUSED,
            event_id=sample_event_with_dates.id,
            eventdate_id=event_dates[0]['id']
        )

        order = create_order(
            txn_id='112233', tickets=[ticket, ticket2], created_at='2018-01-01 10:00:00'
        )  # original order
        assert len(order.tickets) == 2

        txn_ids = ['112233']
        txn_types = ['cart']
        num_tickets = [1]
        i = 0

        _sample_ipn = sample_ipns[i].format(
            id=sample_event_with_dates.id, txn_id=txn_ids[i], txn_type=txn_types[i])

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.replay_paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded",
                headers=[
                    ('Content-Type', 'application/json'),
                    create_authorization_header(),
                    ('Allow-emails', 'true'),
                    ('Replace-order', 'true')
                ]
            )

        orders = dao_get_orders()

        assert mock_send_email.called
        assert len(orders) == 1
        assert orders[i].txn_id == txn_ids[i]
        assert orders[i].txn_type == txn_types[i]

        tickets = dao_get_tickets_for_order(orders[i].id)
        assert len(tickets) == num_tickets[i]

        for n in range(num_tickets[i]):
            assert 'http://test/images/qr_codes/{}'.format(
                str(tickets[n].id)) in mock_send_email.call_args_list[i][0][2]

    @pytest.mark.parametrize('txn_id,trunc_length', [
        ('XX-INVALID_1637667646-112233', 22),
        ('INVALID_1637667646-112233', 19)
    ])
    def it_replaces_existing_invalid_order_and_event_tickets_on_replay_using_txn_id(
        self, mocker, client, db_session, sample_event_with_dates, txn_id, trunc_length
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        txn_type = 'cart'

        _sample_ipn = sample_ipns[0].format(
            id=sample_event_with_dates.id, txn_id=txn_id, txn_type=txn_type)
        _params = json.dumps(parse_qs(_sample_ipn))

        order = create_order(
            txn_id=txn_id, created_at='2018-01-01 10:00:00', params=_params
        )  # original order
        assert len(order.tickets) == 0

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.replay_paypal_ipn', txn_id=txn_id),
                content_type="application/x-www-form-urlencoded",
                headers=[
                    ('Content-Type', 'application/json'),
                    create_authorization_header(),
                    ('Allow-emails', 'true'),
                    ('Replace-order', 'true')
                ]
            )

        orders = dao_get_orders()

        assert mock_send_email.called
        assert len(orders) == 1
        assert orders[0].txn_id == txn_id[trunc_length:]
        assert orders[0].txn_type == txn_type

        tickets = dao_get_tickets_for_order(orders[0].id)
        assert len(tickets) == 1

        assert 'http://test/images/qr_codes/{}'.format(
            str(tickets[0].id)) in mock_send_email.call_args_list[0][0][2]

    def it_creates_orders_and_event_tickets_on_replay_without_email(
        self, mocker, client, db_session, sample_event_with_dates
    ):
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
                    url_for('orders.replay_paypal_ipn'),
                    data=_sample_ipn,
                    content_type="application/x-www-form-urlencoded",
                    headers=[
                        ('Content-Type', 'application/json'),
                        create_authorization_header(),
                        ('Allow-emails', 'false')
                    ]
                )

        orders = dao_get_orders()
        assert len(orders) == 4
        assert not mock_send_email.called

        for i in range(len(sample_ipns)):
            assert orders[i].txn_id == txn_ids[i]
            assert orders[i].txn_type == txn_types[i]

            tickets = dao_get_tickets_for_order(orders[i].id)
            assert len(tickets) == num_tickets[i]

    def it_creates_orders_and_event_tickets_with_remote_login(
        self, mocker, client, db_session, sample_event_with_dates
    ):
        sample_event_with_dates.remote_access = '111'
        sample_event_with_dates.remote_pw = 'pwd'

        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        txn_ids = ['112233']
        txn_types = ['cart']
        num_tickets = [1]

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
        assert len(tickets) == num_tickets[0]

        assert 'http://test/images/qr_codes/{}'.format(
            str(tickets[0].id)) in mock_send_email.call_args_list[0][0][2]
        assert "Meeting id: 111, Password: pwd" in str(mock_send_email.call_args_list[0][0][2])
        assert f"<a href='https://zoom.us/j/{sample_event_with_dates.remote_access}'>Join zoom event</a>" in\
            str(mock_send_email.call_args_list[0][0][2])

    @pytest.mark.parametrize(
        'country_code,delivery_zone', [
            ('GB', 'UK'),
            ('FR', 'Europe'),
            ('US', 'RoW')
        ]
    )
    def it_creates_a_book_order_for_correct_delivery_zone(
        self, app, mocker, client, db_session, sample_book, country_code, delivery_zone
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        _sample_ipn = sample_book_order_ipn.format(
            book_id=f'book-{sample_book.id}', delivery_id=app.config['DELIVERY_ID'], payer_email="payer@example.com",
            delivery_zone=delivery_zone,
            country_code=country_code
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p>"
            "<table><tr><td>The Spirits of Nature</td><td> x 1</td><td> = 5</td></tr></table>"
            "<br><div>Delivery to: Flat 1, 1 Test Place,London, n1 1aa, United Kingdom</div>"
        )

    def it_creates_a_book_order_for_old_id(
        self, app, mocker, client, db_session, sample_book,
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        _sample_ipn = sample_book_order_ipn.format(
            book_id=f'book-{sample_book.old_id}', delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='UK',
            country_code='GB'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p>"
            "<table><tr><td>The Spirits of Nature</td><td> x 1</td><td> = 5</td></tr></table>"
            "<br><div>Delivery to: Flat 1, 1 Test Place,London, n1 1aa, United Kingdom</div>"
        )

    def it_creates_a_book_order_for_random_uuid_with_errors(
        self, app, mocker, client, db_session, sample_uuid,
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        _sample_ipn = sample_book_order_ipn.format(
            book_id=f'book-{sample_uuid}', delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='UK',
            country_code='GB'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert mock_send_email.called
        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p>"
            "<p>Errors in order: <div>Book not found for item_number: 42111e2a-c990-4d38-a785-394277bbc30c</div></p>"
        )

        assert len(orders[0].errors) == 1
        assert orders[0].errors[0].error == 'Book not found for item_number: 42111e2a-c990-4d38-a785-394277bbc30c'

    def it_creates_a_book_order_for_random_uuid_with_multiple_errors(
        self, app, mocker, client, db_session, sample_uuid,
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        _sample_ipn = sample_double_book_order_ipn.format(
            book_id=f'book-{sample_uuid}', delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='UK',
            country_code='GB'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert mock_send_email.called
        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p>"
            "<p>Errors in order: <div>Book not found for item_number: 42111e2a-c990-4d38-a785-394277bbc30c</div>"
            "<div>Book not found for item_number: 42111e2a-c990-4d38-a785-394277bbc30c</div></p>"
        )

        assert len(orders[0].errors) == 2
        assert orders[0].errors[0].error == 'Book not found for item_number: 42111e2a-c990-4d38-a785-394277bbc30c'
        assert orders[0].errors[1].error == 'Book not found for item_number: 42111e2a-c990-4d38-a785-394277bbc30c'

    def it_creates_a_mixed_order(
        self, mocker, app, client, db_session, sample_book, sample_event_with_dates
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        _sample_ipn = sample_mixed_order_ipn.format(
            book_id=f'book-{sample_book.id}', event_id=sample_event_with_dates.id,
            delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='UK',
            country_code='GB'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p>"
            f'<div><span><img src="http://test/images/qr_codes/{orders[0].tickets[0].id}">'
            '</span><div>test_title on 1 Jan at 7PM</div></div>'
            "<table><tr><td>The Spirits of Nature</td><td> x 1</td><td> = 5</td></tr></table>"
            "<br><div>Delivery to: Flat 1, 1 Test Place,London, n1 1aa, United Kingdom</div>"
        )

    def it_sends_an_email_if_missing_address_for_book_order(
        self, mocker, app, client, db_session, sample_book
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        _sample_ipn = sample_book_order_without_address_ipn.format(
            book_id=f'book-{sample_book.id}',
            delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='UK'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert orders[0].delivery_status == 'missing_address'
        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p>"
            "<table><tr><td>The Spirits of Nature</td><td> x 1</td><td> = 5</td></tr></table>"
            "<p>No address supplied. Please "
            "<a href='http://frontend-test/order/missing_address/1122334455'>complete</a> your order.</p>"
        )

    def it_sends_an_email_if_wrong_delivery_zone_for_country(self, mocker, app, client, db_session, sample_book):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        _sample_ipn = sample_book_order_ipn.format(
            book_id=f'book-{sample_book.id}',
            delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='Europe',
            country_code='US'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert orders[0].delivery_status == 'extra'

        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p><table><tr><td>The Spirits of Nature</td><td> x 1</td>"
            "<td> = 5</td></tr></table><p>Not enough delivery paid, &pound;1.50 due. Please <a href='"
            f"http://frontend-test/order/extra/{orders[0].txn_id}/RoW/1.50'>complete</a> your order.</p>")

    def it_sends_an_email_if_delivery_zone_not_recognized(
        self, mocker, app, client, db_session, sample_book, sample_admin_user
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
        mock_send_smtp_email = mocker.patch('app.routes.orders.rest.send_smtp_email')

        _sample_ipn = sample_book_order_ipn.format(
            book_id=f'book-{sample_book.id}',
            delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='Unknown',
            country_code='US'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert orders[0].delivery_status == 'extra'

        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p><table><tr><td>The Spirits of Nature</td><td> x 1</td>"
            "<td> = 5</td></tr></table><p>No delivery fee paid, &pound;6 due. Please <a href='"
            f"http://frontend-test/order/extra/{orders[0].txn_id}/RoW/6'>complete</a> your order.</p>"
            f"<p>Errors in order: <div>Delivery zone: Unknown not found</div></p>")
        assert mock_send_smtp_email.called

    def it_sends_an_email_if_no_delivery_id_for_country(self, mocker, app, client, db_session, sample_book):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        _sample_ipn = sample_book_order_without_delivery_ipn.format(
            book_id=f'book-{sample_book.id}',
            payer_email="payer@example.com",
            country_code='US'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert orders[0].delivery_status == 'extra'
        assert mock_send_email.call_args == call(
            'payer@example.com', 'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p><table><tr><td>The Spirits of Nature</td>"
            "<td> x 1</td><td> = 5</td></tr></table><p>No delivery fee paid, &pound;6 due. "
            f"Please <a href='http://frontend-test/order/extra/{orders[0].txn_id}/RoW/6'>complete</a> your order.</p>"
        )

    def it_sends_payer_and_admin_emails_if_more_than_1_delivery_id_refund(
        self, mocker, app, client, db_session, sample_book, sample_admin_user
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
        mock_send_smtp_email = mocker.patch('app.routes.orders.rest.send_smtp_email')

        _sample_ipn = sample_book_order_multiple_delivery_ipn.format(
            book_id=f'book-{sample_book.id}',
            delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='Europe',
            country_code='US'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert orders[0].delivery_status == 'refund'
        assert mock_send_smtp_email.called
        assert mock_send_smtp_email.call_args_list[0] == call(
            'admin@example.com', 'New Acropolis refund',
            f"Transaction ID: {orders[0].txn_id}<br>Order ID: {orders[0].id}<br>"
            "Refund of &pound;3 due as wrong delivery fee paid.<p>Order delivery zones: <table>"
            "<tr><td>Europe</td><td>4.50</td></tr><tr><td>Europe</td><td>4.50</td></tr></table>Total: &pound;9</p>"
            "<p>Expected delivery zone: RoW - &pound;6</p>"
        )
        assert len(mock_send_email.call_args_list) == 1
        assert mock_send_email.call_args_list[0] == call(
            'payer@example.com', 'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p><table><tr><td>The Spirits of Nature</td><td> x 1</td>"
            f"<td> = 5</td></tr></table><p>Refund of &pound;3 due as wrong delivery fee paid"
            f", please send a message to website admin if there is no refund within 5 working days.</p>"
        )

    def it_sends_an_email_if_more_than_1_delivery_id_costs_not_met(self, mocker, app, client, db_session, sample_book):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')

        _sample_ipn = sample_book_order_multiple_delivery_ipn.format(
            book_id=f'book-{sample_book.id}',
            delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='UK',
            country_code='FR'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert orders[0].delivery_status == 'extra'

        assert mock_send_email.call_args == call(
            'payer@example.com', 'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p><table><tr><td>The Spirits of Nature</td><td> x 1</td>"
            "<td> = 5</td></tr></table><p>Not enough delivery paid, &pound;0.50 due. Please "
            f"<a href='http://frontend-test/order/extra/{orders[0].txn_id}/Europe/0.50'>complete</a> your order.</p>")

    def it_sends_an_email_if_more_than_1_delivery_not_recognised(
        self, mocker, app, client, db_session, sample_book, sample_admin_user
    ):
        mocker.patch('app.routes.orders.rest.Storage')
        mocker.patch('app.routes.orders.rest.Storage.upload_blob_from_base64string')
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
        mock_send_smtp_email = mocker.patch('app.routes.orders.rest.send_smtp_email')

        _sample_ipn = sample_book_order_multiple_delivery_ipn.format(
            book_id=f'book-{sample_book.id}',
            delivery_id=app.config['DELIVERY_ID'],
            payer_email="payer@example.com",
            delivery_zone='Unknown',
            country_code='FR'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1
        assert orders[0].delivery_status == 'extra'

        assert mock_send_email.call_args == call(
            'payer@example.com', 'New Acropolis Order',
            f"<p>Thank you for your order ({orders[0].id})</p><table><tr><td>The Spirits of Nature</td><td> x 1</td>"
            "<td> = 5</td></tr></table><p>No delivery fee paid, &pound;4.50 due. Please <a href='"
            f"http://frontend-test/order/extra/{orders[0].txn_id}/Europe/4.50'>complete</a> your order.</p><p>Errors "
            "in order: <div>Delivery zone: Unknown not found</div><div>Delivery zone: Unknown not found</div></p>")
        assert mock_send_smtp_email.called

    def it_completes_an_order_that_had_missing_or_incorrect_delivery_fee(
        self, mocker, app, client, db_session
    ):
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
        order = create_order(delivery_balance=3.0, delivery_status='extra', delivery_zone='Europe')
        _sample_ipn = sample_complete_order_ipn.format(
            delivery_id=app.config['DELIVERY_ID'],
            linked_txn_id=order.txn_id,
            linked_payment='3.00',
            payer_email="payer@example.com",
            delivery_zone='Europe',
            country_code='FR'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.get(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        completion_order = Order.query.filter(Order.txn_type == 'web_accept').first()

        assert mock_send_email.called
        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f'<p>Thank you for your order ({completion_order.id})</p><div>'
            f'Outstanding payment for order ({order.txn_id}) of &pound;3 for delivery to Europe has been paid.</div>'
        )
        order_json = completion_order.serialize()
        assert order_json['linked_txn_id'] == order.txn_id

        completed_order = Order.query.filter(Order.txn_id == order.txn_id).one()
        assert completed_order.payment_total == 13.0

    def it_sends_more_fee_demands_if_completion_order_not_fulfilled(self, mocker, app, client, db_session):
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
        order = create_order(delivery_balance=3.0, delivery_status='extra', delivery_zone='Europe')
        _sample_ipn = sample_complete_order_ipn.format(
            delivery_id=app.config['DELIVERY_ID'],
            linked_txn_id=order.txn_id,
            linked_payment='2.00',
            payer_email="payer@example.com",
            delivery_zone='Europe',
            country_code='FR'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.get(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        completion_order = Order.query.filter(Order.txn_type == 'web_accept').first()

        assert mock_send_email.called
        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f'<p>Thank you for your order ({completion_order.id})</p><div>'
            f'Outstanding payment for order ({order.txn_id}) of &pound;2 for delivery to Europe has been partially '
            'paid.</div><div>Not enough delivery paid, &pound;1 due.</div><p>Please '
            f"<a href='http://frontend-test/order/extra/{completion_order.txn_id}/Europe/1'>complete</a>"
            " your order.</p>"
        )

    def it_sends_more_refund_if_completion_order_overpaid(self, mocker, app, client, db_session):
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
        order = create_order(delivery_balance=3.0, delivery_status='extra', delivery_zone='Europe')
        _sample_ipn = sample_complete_order_ipn.format(
            delivery_id=app.config['DELIVERY_ID'],
            linked_txn_id=order.txn_id,
            linked_payment='5.00',
            payer_email="payer@example.com",
            delivery_zone='Europe',
            country_code='FR'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.get(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        completion_order = Order.query.filter(Order.txn_type == 'web_accept').first()

        assert mock_send_email.called
        assert mock_send_email.call_args == call(
            'payer@example.com',
            'New Acropolis Order',
            f'<p>Thank you for your order ({completion_order.id})</p>'
            f'<p>You have overpaid for delivery on order ({order.txn_id}) by &pound;2, please send a message to '
            'website admin if there is no refund within 5 working days.</p>'
        )

    def it_does_not_create_an_order_if_payment_not_complete(self, mocker, client, db_session):
        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=sample_incomplete_ipn,
                content_type="application/x-www-form-urlencoded"
            )
        orders = dao_get_orders()
        assert len(orders) == 1
        assert orders[0].errors[0].error == 'Payment not Completed: Incomplete'

    def it_doesnt_create_an_order_if_txn_duplicate(self, app, client, db_session, sample_book):
        create_order(
            txn_id='1122334455',
            payment_total=1
        )

        _sample_ipn = sample_book_order_ipn.format(
            book_id=f'book-{sample_book.id}',
            payer_email="payer@example.com",
            delivery_id=app.config['DELIVERY_ID'],
            delivery_zone='UK',
            country_code='GB'
        )

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=_sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )

        orders = dao_get_orders()
        assert len(orders) == 1

    @freeze_time("2021-11-20T19:00:00")
    @pytest.mark.parametrize('resp', ['INVALID', 'UNKNOWN'])
    def it_creates_an_order_if_not_verified_with_updated_txn_id(
        self, mocker, client, db_session, sample_event_with_dates, resp
    ):
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
        assert len(orders) == 1
        assert len(orders[0].errors) == 1
        assert orders[0].errors[0].error == f"{resp} verification"
        assert orders[0].txn_id.startswith(f"XX-{resp}_1637434800-")

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
        assert len(orders) == 1
        assert len(orders[0].errors) == 1
        assert mock_logger.call_args == call('Paypal receiver not valid: %s for %s', u'another@example.com', u'112233')

    def it_creates_an_order_if_no_event_matched_with_errors(self, mocker, client, db_session, sample_uuid):
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
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
        assert len(orders) == 1
        assert mock_send_email.called
        assert mock_send_email.call_args == call(
            'test1@example.com', 'New Acropolis Order',
            f'<p>Thank you for your order ({orders[0].id})</p>'
            f'<p>Errors in order: <div>{orders[0].errors[0].error}</div></p>')

    def it_does_not_create_an_order_if_invalid_event_date(
        self, mocker, client, db_session, sample_event_with_dates, mock_storage
    ):
        sample_ipn = sample_invalid_date.format(id=sample_event_with_dates.id)

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )
        orders = dao_get_orders()
        assert len(orders) == 1
        assert len(orders[0].errors) == 1
        assert orders[0].errors[0].error == f"Event date 3 not found for: {sample_event_with_dates.id}"

    def it_creates_an_order_for_all_dates(
        self, mocker, client, db_session, sample_event_with_dates, mock_storage
    ):
        mock_send_email = mocker.patch('app.routes.orders.rest.send_email')
        sample_ipn = sample_all_dates.format(id=sample_event_with_dates.id)

        with requests_mock.mock() as r:
            r.post(current_app.config['PAYPAL_VERIFY_URL'], text='VERIFIED')

            client.post(
                url_for('orders.paypal_ipn'),
                data=sample_ipn,
                content_type="application/x-www-form-urlencoded"
            )
        orders = dao_get_orders()
        assert len(orders) == 1
        assert len(orders[0].tickets) == 2
        assert orders[0].tickets[0].eventdate_id == sample_event_with_dates.event_dates[0].id
        assert orders[0].tickets[1].eventdate_id == sample_event_with_dates.event_dates[1].id
        assert mock_send_email.called
        assert mock_send_email.call_args == call(
            'test1@example.com', 'New Acropolis Order',
            f'<p>Thank you for your order ({orders[0].id})</p>'
            f'<div><span><img src="http://test/images/qr_codes/{orders[0].tickets[0].id}"></span>'
            '<div>test_title on 1 Jan at 7PM</div></div>'
            f'<div><span><img src="http://test/images/qr_codes/{orders[0].tickets[1].id}"></span>'
            '<div>test_title on 2 Jan at 7PM</div></div>')

    def it_does_not_create_orders_with_duplicate_txn_ids(
        self, mocker, client, db_session, sample_event_with_dates, mock_storage
    ):
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


class WhenGettingOrders:
    def it_will_return_latest_orders(self, client, db_session, sample_order):
        create_order(
            txn_id='2223334455',
            payment_total=1,
            linked_txn_id=sample_order.txn_id
        )
        create_order(
            txn_id='3334455666',
            payment_total=1,
            linked_txn_id=sample_order.txn_id
        )
        create_order(
            txn_id='XX-INVALID_1122334455-112233',
            payment_total=1,
        )
        create_order(
            txn_id='INVALID_1122334455-112233',
            payment_total=1,
        )
        response = client.get(
            url_for('orders.get_orders')
        )

        assert len(response.json) == 1
        assert len(response.json[0]['books']) == 1
        assert response.json[0]['books'][0]['id'] == str(sample_order.books[0].id)
        assert len(response.json[0]['tickets']) == 1
        assert response.json[0]['tickets'][0]['id'] == str(sample_order.tickets[0].id)
        assert response.json[0]['txn_id'] == sample_order.txn_id
        assert response.json[0]['address_street'] == sample_order.address_street
        assert len(response.json[0]['linked_transactions']) == 2
        assert response.json[0]['payment_total'] == "10.00"
        assert response.json[0]['delivery_balance'] == "0.0"

    def it_will_return_latest_invalid_orders(self, client, db_session, sample_order):
        order = create_order(
            txn_id='XX-INVALID_1637667646-2223334455',
            payment_total=1
        )
        order2 = create_order(
            txn_id='INVALID_1637667646-2223334455',
            payment_total=1
        )
        response = client.get(
            url_for('orders.get_orders', _filter='invalid')
        )

        assert len(response.json) == 2
        assert response.json[0]['txn_id'] == order.txn_id
        assert response.json[1]['txn_id'] == order2.txn_id

    def it_will_return_ignore_duplicate_order(self, client, db_session, sample_order):
        create_order(
            txn_id='XX-1-3334455666',
            payment_total=1
        )
        response = client.get(
            url_for('orders.get_orders')
        )

        assert len(response.json) == 1
        assert len(response.json[0]['books']) == 1
        assert response.json[0]['books'][0]['id'] == str(sample_order.books[0].id)
        assert len(response.json[0]['tickets']) == 1
        assert response.json[0]['tickets'][0]['id'] == str(sample_order.tickets[0].id)
        assert response.json[0]['txn_id'] == sample_order.txn_id


class WhenGettingAnOrder:
    def it_will_the_order_using_txn_id(self, client, db_session, sample_order):
        create_order()  # another order
        response = client.get(
            url_for('orders.get_order', txn_id=sample_order.txn_id)
        )

        assert len(response.json['books']) == 1
        assert response.json['books'][0]['id'] == str(sample_order.books[0].id)
        assert len(response.json['tickets']) == 1
        assert response.json['tickets'][0]['id'] == str(sample_order.tickets[0].id)
        assert response.json['txn_id'] == sample_order.txn_id
        assert response.json['address_street'] == sample_order.address_street

    def it_will_raise_exception_wrong_txn_id(self, client, db_session, sample_uuid):
        response = client.get(
            url_for('orders.get_order', txn_id=sample_uuid)
        )

        assert response.status_code == 404


class WhenUpdatingAnOrder:
    def it_will_update_an_order_address(self, client, sample_order, db_session):
        data = {
            'address_country_code': 'FR',
            'address_street': '1 Grand Rue',
            'address_city': 'Paris',
            'address_postal_code': 'N1',
            'address_country': 'France'
        }
        Order.query.filter_by(id=sample_order.id).update(
            {
                'address_country_code': None,
                'address_street': None,
                'address_city': None,
                'address_postal_code': None,
                'address_country': None
            }
        )
        assert not sample_order.address_country_code
        response = client.post(
            url_for('orders.update_order_address', txn_id=sample_order.txn_id),
            data=json.dumps(data),
            headers=[create_authorization_header()]
        )

        order_db = Order.query.filter_by(id=sample_order.id).one()

        assert order_db.address_country_code == data['address_country_code']
        assert response.json['address_country_code'] == data['address_country_code']

    def it_will_update_an_order(self, client, sample_order, db_session):
        data = {
            'delivery_sent': True,
            'notes': 'New notes',
        }
        assert not sample_order.delivery_sent
        response = client.post(
            url_for('orders.update_order', txn_id=sample_order.txn_id),
            data=json.dumps(data),
            headers=[create_authorization_header()]
        )

        order_db = Order.query.filter_by(id=sample_order.id).one()

        assert order_db.delivery_sent is True
        assert response.json['notes'] == data['notes']
