import base64
from decimal import Decimal
import json
import io
import pyqrcode
import sys
from urllib.parse import unquote
import requests
from datetime import datetime
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request,
    url_for
)
import os.path
import re
from sqlalchemy.orm.exc import NoResultFound
import time

from flask_jwt_extended import jwt_required
from app.comms.email import send_email, send_smtp_email
from app.dao import dao_create_record, dao_update_record
from app.dao.books_dao import dao_create_book_to_order, dao_get_book_by_old_id, dao_get_book_by_id
from app.dao.events_dao import dao_get_event_by_id
from app.dao.event_dates_dao import dao_get_event_date_on_date, dao_get_event_date_by_id
from app.dao.orders_dao import dao_get_order_with_txn_id, dao_get_orders
from app.dao.tickets_dao import dao_get_ticket_id, dao_update_ticket
from app.dao.users_dao import dao_get_admin_users
from app.errors import register_errors, InvalidRequest

from app.models import (
    BookToOrder, Order, OrderError, Ticket,
    BOOK, TICKET_STATUS_USED,
    DELIVERY_FEE_UK_EU, DELIVERY_FEE_UK_ROW, DELIVERY_FEE_EU_ROW,
    DELIVERY_REFUND_EU_UK, DELIVERY_REFUND_ROW_UK, DELIVERY_REFUND_ROW_EU
)
from app.routes.orders.schemas import post_update_order_address_schema, post_update_order_schema
from app.schema_validation import validate
from app.utils.storage import Storage

from na_common.delivery import DELIVERY_ZONES, statuses, get_delivery_zone

orders_blueprint = Blueprint('orders', __name__)
register_errors(orders_blueprint)


@orders_blueprint.route('/order/<string:txn_id>', methods=['GET'])
def get_order(txn_id):
    order = dao_get_order_with_txn_id(txn_id)
    if order:
        return jsonify(order.serialize())
    else:
        return jsonify({'message': f'Transaction ID: {txn_id} not found'}), 404


@orders_blueprint.route('/orders', methods=['GET'])
@orders_blueprint.route('/orders/<int:year>', methods=['GET'])
def get_orders(year=None):
    orders = dao_get_orders(year)

    return jsonify([o.serialize() for o in orders])


@orders_blueprint.route('/order/<string:txn_id>', methods=['POST'])
@jwt_required
def update_order(txn_id):
    data = request.get_json(force=True)

    validate(data, post_update_order_schema)

    order = dao_get_order_with_txn_id(txn_id)
    dao_update_record(Order, order.id, **data)

    return jsonify(order.serialize())


@orders_blueprint.route('/order/update_address/<string:txn_id>', methods=['POST'])
@jwt_required
def update_order_address(txn_id):
    data = request.get_json(force=True)

    validate(data, post_update_order_address_schema)

    order = dao_get_order_with_txn_id(txn_id)

    dz = get_delivery_zone(data['address_country_code'])

    # delivery status is set to extra as delivery fee has not been paid without order address
    data['delivery_status'] = statuses.DELIVERY_EXTRA
    data['delivery_balance'] = dz['price']
    data['delivery_zone'] = dz['name']

    dao_update_record(Order, order.id, **data)

    return jsonify(order.serialize())


def _get_nice_cost(cost):
    _cost = float(cost) if isinstance(cost, str) else abs(cost)
    return int(_cost) if _cost % 1 == 0 else "{:0,.2f}".format(_cost)


@orders_blueprint.route('/orders/paypal/ipn', methods=['GET', 'POST'])
def paypal_ipn():
    params = request.form.to_dict(flat=False)
    current_app.logger.info('IPN params: %r', params)

    if current_app.config['TEST_VERIFY'] and current_app.config['ENVIRONMENT'] != 'live':
        v_response = 'VERIFIED'
        current_app.logger.info('Test paypal verify')
    else:
        VERIFY_URL = current_app.config['PAYPAL_VERIFY_URL']

        params['cmd'] = '_notify-validate'
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'user-agent': 'Python-IPN-Verification-Script'
        }
        current_app.logger.info("params: %r", params)  # debug

        r = requests.post(VERIFY_URL, params=params, headers=headers, verify=True)
        r.raise_for_status()
        v_response = r.text
        if v_response == 'VERIFIED':
            current_app.logger.info('VERIFIED: %s', params['txn_id'])

    # Check return message and take action as needed
    if v_response == 'VERIFIED':
        status = product_message = delivery_message = error_message = ''
        diff = 0.0
        data = {}
        for key in params.keys():
            if isinstance(params[key], list):
                data[key] = params[key][0]
            else:
                data[key] = params[key]

        order_data, tickets, events, products, delivery_zones, errors = parse_ipn(data)

        if not order_data:
            return 'Paypal IPN no order created'
        order_data['params'] = json.dumps(params)

        order = Order(**order_data)
        dao_create_record(order)

        message = f"<p>Thank you for your order ({order.id})</p>"

        if order_data['txn_type'] == 'web_accept' and order_data['linked_txn_id']:
            linked_order = dao_get_order_with_txn_id(order_data['linked_txn_id'])

            diff = linked_order.delivery_balance - Decimal(order_data['payment_total'])
            if diff == 0:
                status = statuses.DELIVERY_EXTRA_PAID
            elif diff > 0:
                status = statuses.DELIVERY_EXTRA
                current_app.logger.warning('Delivery balance not paid in full')
            elif diff < 0:
                status = statuses.DELIVERY_REFUND
                current_app.logger.warning('Delivery balance overpaid')

            dao_update_record(
                Order,
                linked_order.id,
                delivery_status=status,
                payment_total=linked_order.payment_total + Decimal(order_data['payment_total']),
                delivery_balance=abs(diff)
            )

            order_data['delivery_status'] = status
            order_data['delivery_zone'] = linked_order.delivery_zone
            order_data['delivery_balance'] = abs(diff)

            _payment_total = _get_nice_cost(order.payment_total)
            _diff = _get_nice_cost(diff)
            if status == statuses.DELIVERY_EXTRA_PAID:
                message += f"<div>Outstanding payment for order ({order_data['linked_txn_id']}) of &pound;" \
                    f"{_payment_total} for delivery to {order_data['delivery_zone']} has been paid.</div>"
            elif status == statuses.DELIVERY_EXTRA:
                message += f"<div>Outstanding payment for order ({order_data['linked_txn_id']}) of &pound;" \
                    f"{_payment_total} for delivery to {order_data['delivery_zone']} has been " \
                    f"partially paid.</div><div>Not enough delivery paid, &pound;{_diff} due.</div>"
            elif status == statuses.DELIVERY_REFUND:
                message += f"<p>You have overpaid for delivery on order ({order_data['linked_txn_id']}) " \
                    f"by &pound;{_diff}, please send a message to website admin if there is " \
                    "no refund within 5 working days.</p>"
        else:
            if products:
                for product in products:
                    if product['type'] == BOOK:
                        book_to_order = BookToOrder(
                            book_id=product['book_id'],
                            order_id=order.id,
                            quantity=product['quantity']
                        )
                        dao_create_book_to_order(book_to_order)

                        product_message += (
                            f'<tr><td>{product["title"]}</td><td>{product["quantity"]}</td>'
                            f'<td>{_get_nice_cost(product["price"])}</td></tr>'
                        )
                product_message = f'<table>{product_message}</table>'
                address_delivery_zone = None

                if 'address_country_code' not in order_data:
                    delivery_message = "No address supplied. "
                    status = "missing_address"
                else:
                    address_delivery_zone = get_delivery_zone(order_data['address_country_code'])
                    admin_message = ""

                    total_cost = 0
                    for dz in delivery_zones:
                        _d = [_dz for _dz in DELIVERY_ZONES if _dz['name'] == dz]
                        if _d:
                            d = _d[0]
                            total_cost += d['price']
                            _price = _get_nice_cost(d['price'])
                            admin_message += f"<tr><td>{d['name']}</td><td>{_price}</td></tr>"
                        else:
                            errors.append(f'Delivery zone: {dz} not found')
                            admin_message += f"<tr><td>{dz}</td><td>Not found</td></tr>"
                    _total_cost = _get_nice_cost(total_cost)
                    _price = _get_nice_cost(address_delivery_zone['price'])
                    diff = total_cost - address_delivery_zone['price']

                    if diff != 0:
                        admin_message = f"<p>Order delivery zones: <table>{admin_message}" \
                            f"</table>Total: &pound;{_total_cost}</p>"

                        admin_message += "<p>Expected delivery zone: " \
                            f"{address_delivery_zone['name']} - &pound;{_price}</p>"

                        order_data['delivery_balance'] = _get_nice_cost(diff)
                        if diff > 0:
                            status = "refund"
                            delivery_message = f"Refund of &pound;{order_data['delivery_balance']} " \
                                "due as wrong delivery fee paid"
                            admin_message = f"Transaction ID: {order.txn_id}<br>Order ID: {order.id}" \
                                f"<br>{delivery_message}.{admin_message}"
                        elif diff < 0:
                            _diff = _get_nice_cost(diff)

                            status = "extra"
                            delivery_message = "{}, &pound;{} due. ".format(
                                "No delivery fee paid" if total_cost == 0 else "Not enough delivery paid",
                                order_data['delivery_balance']
                            )

                        for user in dao_get_admin_users():
                            send_smtp_email(user.email, f'New Acropolis {status}', admin_message)
                    else:
                        status = statuses.DELIVERY_PAID

                dao_update_record(
                    Order, order.id,
                    delivery_status=status,
                    delivery_zone=address_delivery_zone['name'] if address_delivery_zone else None,
                    delivery_balance=str(abs(diff))
                )

                if delivery_message:
                    order_data['delivery_status'] = status
                    if status == 'refund':
                        delivery_message = f"<p>{delivery_message}, please send a message " \
                            "to website admin if there is no refund within 5 working days.</p>"
                    else:
                        order_data['delivery_zone'] = address_delivery_zone['name'] if address_delivery_zone else None
                else:
                    product_message = (
                        f'{product_message}<br><div>Delivery to: {order_data["address_street"]},'
                        f'{order_data["address_city"]}, '
                        f'{order_data["address_postal_code"]}, {order_data["address_country"]}</div>'
                    )

            for i, _ticket in enumerate(tickets):
                _ticket['order_id'] = order.id
                ticket = Ticket(**_ticket)
                dao_create_record(ticket)
                tickets[i]['ticket_id'] = ticket.id

            if tickets:
                storage = Storage(current_app.config['STORAGE'])
                for i, event in enumerate(events):
                    link_to_post = '{}{}'.format(
                        current_app.config['API_BASE_URL'], url_for('.use_ticket', ticket_id=tickets[i]['ticket_id']))
                    img = pyqrcode.create(link_to_post)
                    buffer = io.BytesIO()
                    img.png(buffer, scale=2)

                    img_b64 = base64.b64encode(buffer.getvalue())
                    target_image_filename = '{}/{}'.format('qr_codes', str(tickets[i]['ticket_id']))
                    storage.upload_blob_from_base64string('qr.code', target_image_filename, img_b64)

                    message += '<div><span><img src="{}/{}"></span>'.format(
                        current_app.config['IMAGES_URL'], target_image_filename)

                    event_date = dao_get_event_date_by_id(tickets[i]['eventdate_id'])
                    minutes = ':%M' if event_date.event_datetime.minute > 0 else ''
                    message += "<span>{} on {}</span></div>".format(
                        event.title, event_date.event_datetime.strftime('%-d %b at %-I{}%p'.format(minutes)))

                    if event_date.event.remote_access:
                        message += f"<br><div>Meeting id: {event_date.event.remote_access}"
                        if event_date.event.remote_pw:
                            message += f", Password: {event_date.event.remote_pw}"
                        message += "</div>"

        if errors:
            error_message = ''
            for error in errors:
                error_message += f"<div>{error}</div>"
                order.errors.append(OrderError(error=error))
            error_message = f"<p>Errors in order: {error_message}</p>"

        if status in [
            statuses.DELIVERY_EXTRA, statuses.DELIVERY_MISSING_ADDRESS, statuses.DELIVERY_NOT_PAID
        ]:
            _delivery_zone_balance = ''

            if 'delivery_balance' in order_data:
                _delivery_balance = _get_nice_cost(order_data['delivery_balance'])
                _delivery_zone_balance = f"/{order_data['delivery_zone']}/{_delivery_balance}"\
                    if order_data['delivery_zone'] else ''

            delivery_message = (
                f"<p>{delivery_message}Please "
                f"<a href='{current_app.config['FRONTEND_URL']}/order/{order_data['delivery_status']}/"
                f"{order_data['txn_id']}{_delivery_zone_balance}'>complete</a>"
                "your order.</p>"
            )

        send_email(
            order.email_address,
            'New Acropolis Order',
            message + product_message + delivery_message + error_message
        )

    elif v_response == 'INVALID':
        current_app.logger.info('INVALID %r', params['txn_id'])
    else:
        current_app.logger.info('UNKNOWN response %r', params['txn_id'])

    return 'Paypal IPN'


@orders_blueprint.route('/orders/ticket/<string:ticket_id>', methods=['GET'])
def use_ticket(ticket_id):
    ticket = dao_get_ticket_id(ticket_id)

    if not ticket.event.is_event_today(ticket.eventdate_id):
        data = {
            'update_response': 'Event is not today'
        }
    else:
        if ticket.status == TICKET_STATUS_USED:
            data = {
                'update_response': 'Ticket already used'
            }
        else:
            dao_update_ticket(ticket_id, status=TICKET_STATUS_USED)

            data = {
                'update_response': 'Ticket updated to used'
            }

    data['ticket_id'] = ticket_id
    data['title'] = ticket.event.title

    return jsonify(data)


def parse_ipn(ipn):
    order_data = {}
    receiver_email = None
    errors = []
    none_response = None, None, None, None, None, errors
    tickets = []
    events = []
    products = []
    delivery_zones = []

    order_mapping = {
        'custom': 'linked_txn_id',
        'payer_email': 'email_address',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'payment_status': 'payment_status',
        'txn_type': 'txn_type',
        'mc_gross': 'payment_total',
        'txn_id': 'txn_id',
        'payment_date': 'created_at',
        'address_street': 'address_street',
        'address_city': 'address_city',
        'address_zip': 'address_postal_code',
        'address_state': 'address_state',
        'address_country': 'address_country',
        'address_country_code': 'address_country_code',
    }

    for key in ipn.keys():
        if key == 'receiver_email':
            receiver_email = ipn[key]
        if key in order_mapping.keys():
            order_data[order_mapping[key]] = ipn[key]

    if order_data['payment_status'] != 'Completed':
        current_app.logger.error(
            'Order: %s, payment not complete: %s', order_data['txn_id'], order_data['payment_status'])
        return none_response

    if receiver_email.replace(' ', '+') != current_app.config['PAYPAL_RECEIVER']:
        current_app.logger.error('Paypal receiver not valid: %s for %s', receiver_email, order_data['txn_id'])
        order_data['payment_status'] = 'Invalid receiver'
        return none_response

    order_found = dao_get_order_with_txn_id(order_data['txn_id'])
    if order_found:
        msg = 'Order: %s, payment already made', order_data['txn_id']
        current_app.logger.error(msg)
        errors.append(msg)
        return none_response

    if ipn['txn_type'] == 'paypal_here':
        _event_date = datetime.strptime(ipn['payment_date'], '%H:%M:%S %b %d, %Y PST').strftime('%Y-%m-%d')
        event_date = dao_get_event_date_on_date(_event_date)
        ticket = {
            'ticket_number': 1,
            'event_id': event_date.event_id,
            'eventdate_id': event_date.id,
            'status': TICKET_STATUS_USED
        }
        event = dao_get_event_by_id(event_date.event_id)
        events.append(event)

        tickets.append(ticket)
    elif ipn['txn_type'] != 'web_accept':
        counter = 1
        while ('item_number%d' % counter) in ipn:
            quantity = int(ipn['quantity%d' % counter])
            price = float("{0:.2f}".format(float(ipn['mc_gross_%d' % counter]) / quantity))

            if ipn['item_number%d' % counter].startswith('delivery'):
                delivery_zone = ipn['option_selection1_%d' % counter]
                if 'delivery_zone' not in order_data.keys():
                    order_data['delivery_zone'] = delivery_zone
                else:
                    current_app.logger.error(f"Multiple delivery costs in order: {order_data['txn_id']}")
                delivery_zones.append(delivery_zone)
            elif ipn['item_number%d' % counter].startswith('book-'):
                book_id = ipn['item_number%d' % counter][len("book-"):]
                UUID_LENGTH = 36
                if len(book_id) < UUID_LENGTH:
                    book = dao_get_book_by_old_id(book_id)
                else:
                    book = dao_get_book_by_id(book_id)
                if book:
                    products.append(
                        {
                            "type": BOOK,
                            "book_id": book.id,
                            "title": book.title,
                            "quantity": quantity,
                            "price": price
                        }
                    )
                else:
                    msg = f"Book not found for item_number: {book_id}"
                    current_app.logger.error(msg)
                    counter += 1
                    errors.append(msg)
                    continue
            else:
                try:
                    event = dao_get_event_by_id(ipn['item_number%d' % counter])
                    events.append(event)
                except NoResultFound:
                    msg = f"Event not found for item_number: {ipn['item_number%d' % counter]}"
                    current_app.logger.error(msg)
                    counter += 1
                    errors.append(msg)
                    continue

                if 'option_name2_%d' % counter in ipn.keys():
                    event_date_index = int(ipn['option_selection2_%d' % counter]) \
                        if ipn['option_name2_%d' % counter] == 'Date' else 1
                else:
                    event_date_index = 1

                if event_date_index > len(event.event_dates):
                    error_msg = f"Event date {event_date_index} not found for: {ipn['item_number%d' % counter]}"
                    current_app.logger.error(error_msg)
                    counter += 1
                    errors.append(error_msg)
                    continue

                event_date_id = event.event_dates[event_date_index - 1].id

                for i in range(1, quantity + 1):
                    ticket = {
                        'ticket_number': i,
                        'event_id': event.id,
                        'ticket_type': ipn['option_selection1_%d' % counter],
                        'eventdate_id': event_date_id,
                        'price': price,
                        'name':
                            ipn.get('option_selection3_%d' % counter)
                            if ipn.get('option_name3_%d' % counter) == 'Course Member name'
                            else ipn.get('option_selection2_%d' % counter)
                            if ipn.get('option_name2_%d' % counter) == 'Course Member name'
                            else None
                    }
                    tickets.append(ticket)
            counter += 1

    order_data['buyer_name'] = '{} {}'.format(order_data['first_name'], order_data['last_name'])
    del order_data['first_name']
    del order_data['last_name']

    return order_data, tickets, events, products, delivery_zones, errors
