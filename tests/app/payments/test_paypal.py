from mock import call, Mock
import pytest
import random
import uuid

from app.errors import PaypalException
from app.payments.paypal import PayPal

mock_create_button_id = '5T455H4BBKU3W'
mock_update_button_id = 'U4EU53ARMDPUU'
mock_item_id = str(uuid.uuid4())

mock_get_resp_content = (
    'L_HOSTEDBUTTONID0=U4EU53ARMDPUU&L_HOSTEDBUTTONID1=JL69Y2PB6J5BQ&L_HOSTEDBUTTONID2={}&'
    'L_BUTTONTYPE0=ADDCART&L_BUTTONTYPE1=ADDCART&L_BUTTONTYPE2=ADDCART&'
    'L_ITEMNAME0=test%20update&L_ITEMNAME1=312&L_ITEMNAME2=Test%20paypal%20udpate&'
    'L_ITEMNAME3=Develop%20your%20Inner%20Philosopher%20%281%2dday%20workshop%29&'
    'L_MODIFYDATE0=2019%2d01%2d01T00%3a00%3a00Z&L_MODIFYDATE1=2019%2d01%2d01T00%3a00%3a00Z&'
    'L_MODIFYDATE2=2019%2d01%2d01T00%3a00%3a00Z&'
    'TIMESTAMP=2019%2d01%2d01T00%3a00%3a00Z&CORRELATIONID=a1c7f2226685d&ACK=Success&VERSION=51%2e0&'
    'BUILD=46457558'.format(mock_update_button_id)
)

mock_get_button_details = (
    'WEBSITECODE=%3cform%20target%3d%22paypal%22%20action%3d%22https%3a%2f%2fwww%2esandbox%2epaypal%2ecom%2fcgi%2dbin'
    '%2fwebscr%22%20method%3d%22post%22%3e%0a%2fform%3e%0a&HOSTEDBUTTONID={}&BUTTONCODE=HOSTED&'
    'BUTTONTYPE=ADDCART&BUTTONSUBTYPE=SERVICES&L_BUTTONVAR0=%22no_note%3d0%22&L_BUTTONVAR1=%22add%3d1%22&'
    'L_BUTTONVAR2=%22bn%3d%3dZ354JXLJ44EBU%3aPP%2dShopCartBF_S%22&L_BUTTONVAR3=%22business%3dZ354JXLJ44EBU%22&'
    'L_BUTTONVAR4=%22currency_code%3dGBP%22&L_BUTTONVAR5=%22item_name%3dTest%20paypal%20udpate%22&'
    '{}OPTION0NAME=%22Ticket%20type%22&OPTION1NAME=%22Date%22&L_OPTION0SELECT0=%22Full%22&'
    'L_OPTION0SELECT1=%22Concession%22&L_OPTION0SELECT2=%22Member%22&L_OPTION1SELECT0=%22all%22&'
    'L_OPTION1SELECT1=%221%22&L_OPTION1SELECT2=%222%22&L_OPTION1SELECT3=%223%22&L_OPTION1SELECT4=%224%22&'
    'L_OPTION0PRICE0=%225%2e00%22&L_OPTION0PRICE1=%223%2e00%22&L_OPTION0PRICE2=%220%2e01%22&BUTTONIMAGE=REG&'
    'BUTTONCOUNTRY=GB&BUTTONLANGUAGE=en&TIMESTAMP=2019%2d01%2d01T00%3a00%3a00Z&CORRELATIONID=c4e87abc815c3&'
    'ACK=Success&VERSION=51%2e0&BUILD=46457558'
)

mock_process_button = (
    'WEBSITECODE=%3cform%20target%3d%22paypal%22%20action%3d%22https%3a%2f%2fwww%2esandbox%2epaypal%2ecom%2fcgi%2dbin'
    '%2fwebscr%22%20method%3d%22post%22%3e%0a'
    '&HOSTEDBUTTONID={button_id}&TIMESTAMP=2019%2d01%2d01T00%3a00%3a00Z&CORRELATIONID=7c6bca39408c1&ACK={ack}&'
    'VERSION=51%2e0&BUILD=46457558{err_msg}'
)


class MockRequests:
    def __init__(self, ack='Success', err_msg='', has_item_number=True):
        self.ack = ack
        self.err_msg = err_msg
        self.has_item_number = has_item_number

    def post(self, _, data=None, **kwargs):
        mock_response = Mock()
        mock_response.raise_for_status = Mock()

        if data['METHOD'] == 'BMButtonSearch':
            mock_response.content = mock_get_resp_content
        elif data['METHOD'] == 'BMGetButtonDetails':
            mock_response.content = mock_get_button_details.format(
                mock_update_button_id,
                f"L_BUTTONVAR{random.randint(6, 9)}=%22item_number%3d{mock_item_id}%22&" if self.has_item_number else ''
            )
        elif data['METHOD'] in ['BMCreateButton']:
            mock_response.content = mock_process_button.format(
                button_id=mock_create_button_id, ack=self.ack, err_msg=self.err_msg)
        elif data['METHOD'] in ['BMUpdateButton']:
            mock_response.content = mock_process_button.format(
                button_id=mock_update_button_id, ack=self.ack, err_msg=self.err_msg)

        mock_response.content = bytes(mock_response.content.encode("utf-8"))
        return mock_response

    def raise_for_status(self):
        return Mock()


class WhenCreatingPaypalButton:

    def it_calls_paypal_apis_to_create_button(self, app, mocker, sample_uuid):
        mocker.patch('app.payments.paypal.requests', MockRequests())

        p = PayPal()
        button_id = p.create_update_paypal_button(
            sample_uuid, 'test title', all_fee=20, all_conc_fee=15, members_free=True)
        assert button_id == mock_create_button_id

    def it_returns_a_mock_button_id_if_paypal_not_configured(self, app, mocker, sample_uuid):
        self.mock_config = {
            'PAYPAL_URL': None,
            'PAYPAL_USER': None,
            'PAYPAL_PASSWORD': None,
            'PAYPAL_SIG': None
        }

        mocker.patch.dict(
            'app.payments.paypal.current_app.config',
            self.mock_config
        )

        mock_logger = mocker.patch('app.payments.paypal.current_app.logger.info')

        p = PayPal()
        button_id = p.create_update_paypal_button(
            sample_uuid, 'test title', all_fee=20, all_conc_fee=15, members_free=True)
        assert mock_logger.call_args == call('Paypal not configured, returning MOCK_BUTTON_ID')
        assert button_id == 'MOCK_BUTTON_ID'

    def it_calls_paypal_apis_to_update_button(self, app, mocker):
        mocker.patch('app.payments.paypal.requests', MockRequests())

        p = PayPal()
        button_id = p.create_update_paypal_button(mock_item_id, 'test title')
        assert button_id == mock_update_button_id

    def it_creates_a_paypal_button_for_search_without_item_number(self, app, mocker, sample_uuid):
        mocker.patch('app.payments.paypal.requests', MockRequests(has_item_number=False))

        p = PayPal()
        button_id = p.create_update_paypal_button(
            sample_uuid, 'test title', all_fee=20, all_conc_fee=15, members_free=True)
        assert button_id == mock_create_button_id

    def it_raises_an_error_on_paypal_error(self, app, mocker):
        mocker.patch('app.payments.paypal.requests', MockRequests(ack='Error', err_msg='&L_LONGMESSAGE0=Error'))

        p = PayPal()

        with pytest.raises(expected_exception=PaypalException):
            p.create_update_paypal_button('152', 'test title')


class WhenUpdatingPaypalButton:

    def it_calls_paypal_apis_to_update_button(self, app, mocker):
        mocker.patch('app.payments.paypal.requests', MockRequests())

        p = PayPal()
        button_id = p.create_update_paypal_button(mock_item_id, 'test title')
        assert button_id == mock_update_button_id

    def it_raises_an_error_if_no_item_found(self, app, mocker, sample_uuid):
        mocker.patch('app.payments.paypal.requests', MockRequests())

        p = PayPal()
        with pytest.raises(expected_exception=PaypalException):
            p.create_update_paypal_button(sample_uuid, 'test title', booking_code='test booking code')
