from flask import current_app, jsonify, render_template
import json
import requests
from HTMLParser import HTMLParser

from na_common.dates import get_nice_event_dates

from app.comms.encryption import encrypt
from app.errors import InvalidRequest
from app.models import BASIC, EVENT, MAGAZINE, PROVIDER_MG, PROVIDER_SB
from app.dao.events_dao import dao_get_event_by_id
from app.dao.emails_dao import dao_get_todays_email_count_for_provider
from app.dao.email_providers_dao import dao_get_first_email_provider, dao_get_next_email_provider
from app.dao.magazines_dao import dao_get_magazine_by_id

h = HTMLParser()
EMAIL_BUFFER = 5


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


def get_email_data(data_struct, to, subject, message, _from=None):
    if isinstance(to, list):
        to = ','.join(to)

    data_struct = data_struct.replace("<<to>>", to)
    data_struct = data_struct.replace("<<subject>>", subject)
    data_struct = data_struct.replace("<<message>>", message.replace("\"", "\\\""))
    if _from:
        data_struct = data_struct.replace("<<from>>", _from)

    return json.loads(data_struct)


def send_email(to, subject, message, _from=None, override=False):
    if current_app.config['ENVIRONMENT'] != 'live' or current_app.config.get('EMAIL_RESTRICT'):
        message = message.replace('<body>', '<body><div>Test email, intended for {}</div>'.format(to))
        to = current_app.config['TEST_EMAIL']

    if not _from:
        _from = 'noreply@{}'.format(current_app.config['EMAIL_DOMAIN'])

    email_provider = dao_get_first_email_provider()

    if email_provider:
        if (dao_get_todays_email_count_for_provider(email_provider.name) >
                email_provider.daily_limit - EMAIL_BUFFER):
            next_email_provider = dao_get_next_email_provider(email_provider.pos)
            email_provider = next_email_provider if next_email_provider else email_provider

            if (not email_provider and not override) or ((dao_get_todays_email_count_for_provider(
                    email_provider.name) > email_provider.daily_limit - EMAIL_BUFFER) and not override):
                raise InvalidRequest('Daily limit reached', 429)

        data = get_email_data(email_provider.data_struct, to, subject, message, _from)
        response = requests.post(
            email_provider.api_url,
            auth=('api', email_provider.api_key),
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
            'from': _from,
            'subject': subject,
            'message': message
        }
        current_app.logger.info('No email providers configured, email would have sent: {}'.format(data))
