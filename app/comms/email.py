from flask import current_app, jsonify, render_template
import json
import requests
from HTMLParser import HTMLParser

from na_common.dates import get_nice_event_dates

from app.comms.encryption import encrypt
from app.models import BASIC, EVENT, MAGAZINE
from app.dao.events_dao import dao_get_event_by_id
from app.dao.magazines_dao import dao_get_magazine_by_id

h = HTMLParser()


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
            _topics = [(t.split(':')[0], t.split(':')[1]) for t in magazine.topics.split('\\n')]
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


def send_email(to, subject, message, _from=None):
    if not _from:
        _from = 'noreply@{}'.format(current_app.config['EMAIL_DOMAIN'])

    email_provider_url = current_app.config['EMAIL_PROVIDER_URL']
    email_provider_apikey = current_app.config['EMAIL_PROVIDER_APIKEY']

    if current_app.config['ENVIRONMENT'] != 'live' or current_app.config.get('EMAIL_RESTRICT'):
        message = message.replace('<body>', '<body><div>Test email, intended for {}</div>'.format(to))
        to = current_app.config['TEST_EMAIL']

    data = {
        "from": _from,
        "to": to,
        "subject": subject,
        "html": message
    }

    if email_provider_url and email_provider_apikey:
        response = requests.post(
            email_provider_url,
            auth=('api', email_provider_apikey),
            data=data,
        )

        response.raise_for_status()
        current_app.logger.info('Sent email: {}, response: {}'.format(subject, response.text))
        if current_app.config['ENVIRONMENT'] != 'live':  # pragma: no cover
            current_app.logger.info('Email to: {}'.format(to))
            current_app.logger.info('Email provider: {}'.format(email_provider_url))
            current_app.logger.info('Email key: {}'.format(email_provider_apikey[:5]))

        return response.status_code
    else:
        current_app.logger.info('Email not configured, email would have sent: {}'.format(data))
