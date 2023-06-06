from datetime import datetime, timedelta
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask import current_app
import json
import requests
from urllib.parse import parse_qs

from app.errors import PaypalException

PAYPAL_SEARCH_BACK_FROM = 90


class PayPal:

    def __init__(self):
        self.base_data = {
            'USER': current_app.config['PAYPAL_USER'],
            'PWD': current_app.config['PAYPAL_PASSWORD'],
            'SIGNATURE': current_app.config['PAYPAL_SIG'],
            'VERSION': '51.0',
        }
        self.paypal_url = current_app.config['PAYPAL_URL']

    def create_update_paypal_button(
        self, item_id, title, fee=5, conc_fee=3, all_fee=None, all_conc_fee=None, members_free=False, booking_code=None
    ):
        if not self.paypal_url:
            current_app.logger.info('Paypal not configured, returning MOCK_BUTTON_ID')
            return 'MOCK_BUTTON_ID'

        search_data = self.base_data.copy()
        search_data.update({
            'METHOD': 'BMButtonSearch',
            'STARTDATE': datetime.now() - timedelta(days=PAYPAL_SEARCH_BACK_FROM)
        })

        response = requests.post(
            self.paypal_url,
            data=search_data,
            headers={'content-type': 'application/x-www-form-urlencoded'}
        )

        response.raise_for_status()

        search_resp = parse_qs(response.content.decode("utf-8"))

        if item_id:
            for key in [k for k in search_resp.keys() if k.startswith('L_HOSTEDBUTTONID')]:
                get_data = self.base_data.copy()
                get_data.update({
                    'METHOD': 'BMGetButtonDetails',
                    'HOSTEDBUTTONID': search_resp[key]
                })

                response = requests.post(
                    self.paypal_url,
                    data=get_data,
                    headers={'content-type': 'application/x-www-form-urlencoded'}
                )

                response.raise_for_status()

                get_resp = parse_qs(response.content.decode('ASCII'))

                _item_id = None
                for _key in [k for k in get_resp.keys() if k.startswith('L_BUTTONVAR')]:
                    item = get_resp[_key][0].split('=')
                    if item[0][1:] == 'item_number':
                        _item_id = item[1][:-1]
                        break

                current_app.logger.info(
                    'Button compare: {} - {} = {}'.format(item_id, _item_id, str(item_id) == str(_item_id)))

                if str(item_id) == str(_item_id):
                    current_app.logger.info('Update paypal button: {}'.format(item_id))
                    return self.paypal_button_process(
                        'BMUpdateButton', search_resp[key], title, item_id,
                        fee, conc_fee, all_fee, all_conc_fee, members_free
                    )

        if booking_code:
            raise PaypalException('Paypal error: button for {} not found'.format(item_id))
        else:
            current_app.logger.info('Create paypal button: {}'.format(item_id))
            return self.paypal_button_process(
                'BMCreateButton', 'New', title, item_id,
                fee, conc_fee, all_fee, all_conc_fee, members_free
            )

    def paypal_button_process(
        self, method, button_id, title, item_id, fee, conc_fee, all_fee, all_conc_fee, members_free
    ):
        data = self.base_data.copy()
        data.update({
            'METHOD': method,
            'HOSTEDBUTTONID': button_id,
            'BUTTONCODE': 'HOSTED',
            'BUTTONTYPE': 'CART',
            'BUTTONSUBTYPE': 'SERVICES',
            'BUTTONCOUNTRY': 'GB',
            'L_BUTTONVAR1': 'item_name={}'.format(title),
            'L_BUTTONVAR2': 'item_number={}'.format(item_id),
            'L_BUTTONVAR3': 'currency_code=GBP',
            'OPTION0NAME': 'Ticket type',
            'L_OPTION0SELECT0': 'Full',
            'L_OPTION0PRICE0': fee,
            'L_OPTION0SELECT1': 'Concession',
            'L_OPTION0PRICE1': conc_fee,
            'OPTION1NAME': 'Date',
            'L_OPTION1SELECT0': 'all',
            'L_OPTION1SELECT1': '1',
            'L_OPTION1SELECT2': '2',
            'L_OPTION1SELECT3': '3',
            'L_OPTION1SELECT4': '4',
            'L_OPTION0SHIPPINGAMOUNT0': '0',
            'L_OPTION0SHIPPINGAMOUNT1': '0',
            'L_SHIPPINGOPTIONISDEFAULT0': 'false',
        })

        index = 2

        if all_fee:
            data['L_OPTION0SELECT2'] = 'All_Full'
            data['L_OPTION0PRICE2'] = all_fee
            data['L_OPTION0SELECT3'] = 'All_Concession'
            data['L_OPTION0PRICE3'] = all_conc_fee
            index = 4

        if members_free:
            data['L_OPTION0SELECT{}'.format(index)] = 'Member'
            data['L_OPTION0PRICE{}'.format(index)] = '0.01'

        current_app.logger.info('Paypal process: {}'.format(data))

        response = requests.post(
            self.paypal_url,
            data=data,
            headers={'content-type': 'application/x-www-form-urlencoded'}
        )

        response.raise_for_status()

        process_resp = parse_qs(response.content.decode("utf-8"))

        if 'Success' in process_resp['ACK']:
            current_app.logger.info('Paypal success: {} - {}'.format(item_id, process_resp['HOSTEDBUTTONID'][0]))
            return process_resp['HOSTEDBUTTONID'][0]
        else:
            error_msg = ""
            for key in [k for k in process_resp.keys() if k.startswith('L_LONGMESSAGE')]:
                error_msg += f'{process_resp[key]}, '
            raise PaypalException('Paypal error: {}'.format(error_msg))
