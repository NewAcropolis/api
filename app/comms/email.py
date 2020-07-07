from flask import current_app, jsonify, render_template
import json
import re
import requests
from HTMLParser import HTMLParser

from na_common.dates import get_nice_event_dates

from app.comms.encryption import encrypt
from app.errors import InvalidRequest
from app.models import BASIC, EVENT, MAGAZINE
from app.dao.events_dao import dao_get_event_by_id
from app.dao.emails_dao import dao_get_past_hour_email_count_for_provider, dao_get_todays_email_count_for_provider
from app.dao.email_providers_dao import dao_get_first_email_provider, dao_get_next_email_provider
from app.dao.magazines_dao import dao_get_magazine_by_id

h = HTMLParser()


def get_email_provider(override=False, email_provider=None):
    if not email_provider:
        email_provider = dao_get_first_email_provider()
        if not email_provider:
            return None

    daily_email_count = dao_get_todays_email_count_for_provider(email_provider.id)
    hourly_email_count = 0

    if email_provider.hourly_limit > 0:
        hourly_email_count = dao_get_past_hour_email_count_for_provider(email_provider.id)

    if daily_email_count > email_provider.daily_limit:
        if override:
            next_email_provider = dao_get_next_email_provider(email_provider.pos)

            if next_email_provider:
                return get_email_provider(override, next_email_provider)
        else:
            email_provider.limit = 0
            email_provider.daily_limit_reached = True
        return email_provider

    if hourly_email_count > email_provider.hourly_limit:
        if override:
            next_email_provider = dao_get_next_email_provider(email_provider.pos)
            if next_email_provider:
                return get_email_provider(override, next_email_provider)
        email_provider.limit = 0
        email_provider.hourly_limit_reached = True

    if email_provider.hourly_limit > 0:
        email_provider.limit = email_provider.hourly_limit - hourly_email_count

    email_provider.limit = email_provider.daily_limit - daily_email_count
    return email_provider


def get_email_html(email_type, **kwargs):
    if email_type == EVENT:
        event = dao_get_event_by_id(kwargs.get('event_id'))
        member_id = kwargs.get('member_id')
        if not member_id:
            member_id = '0'  # for preview of emails
        current_app.logger.debug('Email Tokens %s', current_app.config['EMAIL_TOKENS'])
        unsubcode = encrypt(
            "{}={}".format(current_app.config['EMAIL_TOKENS']['member_id'], member_id),
            current_app.config['EMAIL_UNSUB_SALT']
        )
        return render_template(
            'emails/events.html',
            event=event,
            event_dates=get_nice_event_dates(event.event_dates),
            description=h.unescape(event.description),
            details=kwargs.get('details'),
            extra_txt=kwargs.get('extra_txt'),
            unsubcode=unsubcode
        )
    elif email_type == MAGAZINE:
        magazine = dao_get_magazine_by_id(kwargs.get('magazine_id'))
        topics = []
        if magazine.topics:
            _topics = [(t.split(':')[0], t.split(':')[1]) for t in magazine.topics.split('\n')]

            for title, description in _topics:
                topics.append({'title': title, 'description': description})
        return render_template(
            'emails/magazine.html',
            magazine=magazine,
            topics=topics
        )
    elif email_type == BASIC:
        return render_template(
            'emails/basic.html',
            title=kwargs.get('title', ''),
            message=kwargs.get('message')
        )


def get_email_data(data_map, to, subject, message, from_email, from_name):
    data_struct = {}
    if isinstance(to, list):
        to = ','.join(to)

    def set_data(_map, val):
        elements = _map.split(",")

        if len(elements) == 2:
            match = re.match(r"\[(?P<list_element>.+)\]", elements[1])
            if match:
                data_struct[elements[0]] = []

                for item in val.split(','):
                    data_struct[elements[0]].append({
                        match.group('list_element'): item
                    })
            else:
                if data_struct.get(elements[0]):
                    data_struct[elements[0]][elements[1]] = val
                else:
                    data_struct[elements[0]] = {elements[1]: val}
        else:
            data_struct[elements[0]] = val

    set_data(data_map['to'], to)
    set_data(data_map['subject'], subject)
    set_data(data_map['from'], from_email)
    if 'from_name' in data_map.keys():
        set_data(data_map['from_name'], from_name)
    set_data(data_map['message'], message)

    return data_struct


def send_email(to, subject, message, from_email=None, from_name=None, override=False):
    if current_app.config['ENVIRONMENT'] != 'live' or current_app.config.get('EMAIL_RESTRICT'):
        message = message.replace('<body>', '<body><div>Test email, intended for {}</div>'.format(to))
        to = current_app.config['TEST_EMAIL']

    if not from_email:
        from_email = 'noreply@{}'.format(current_app.config['EMAIL_DOMAIN'])
    if not from_name:
        from_name = 'New Acropolis'

    email_provider = get_email_provider(override)

    if email_provider:
        if hasattr(email_provider, "hourly_limit_reached"):
            raise InvalidRequest('Hourly limit reached', 429)
        elif hasattr(email_provider, "daily_limit_reached"):
            raise InvalidRequest('Daily limit reached', 429)

        data = get_email_data(email_provider.data_map, to, subject, message, from_email, from_name)
        data = data if email_provider.as_json else json.dumps(data)

        headers = {
            'api-key': email_provider.api_key,
            'accept': 'application/json',
            'content-type': 'application/json'
        } if email_provider.headers else None

        response = requests.post(
            email_provider.api_url,
            auth=('api', email_provider.api_key),
            headers=headers,
            data=data,
        )

        response.raise_for_status()
        current_app.logger.info('Sent email: {}, response: {}'.format(subject, response.text))
        if current_app.config['ENVIRONMENT'] != 'live':  # pragma: no cover
            current_app.logger.info('Email to: {}'.format(to))
            current_app.logger.info('Email provider: {}'.format(email_provider.api_url))
            current_app.logger.info('Email key: {}'.format(email_provider.api_key[:5]))

        return response.status_code
    else:
        data = {
            'to': to,
            'from_email': from_email,
            'from_name': from_name,
            'subject': subject,
            'message': message
        }
        current_app.logger.info('No email providers configured, email would have sent: {}'.format(data))
