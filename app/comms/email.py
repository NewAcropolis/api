from flask import current_app, jsonify, render_template
import requests
from HTMLParser import HTMLParser

from app.comms.encryption import encrypt
from app.models import BASIC, EVENT
from app.dao.events_dao import dao_get_event_by_id

h = HTMLParser()


def get_nice_event_dates(event_dates):
    event_dates.sort(key=lambda k: k.event_datetime)

    event_date_str = ''
    _event_month = ''
    _event_dates = ''
    for event_date in event_dates:
        m = event_date.event_datetime.strftime("%B")
        d = event_date.event_datetime.strftime("%a %-d, ")

        if not _event_month:
            _event_month = event_date.event_datetime.strftime("%B")

        if m == _event_month:
            _event_dates += d
        elif _event_dates:
            event_date_str += _event_dates[:-2] + ' of ' + _event_month + ', '
            _event_dates = d
            _event_month = m

    event_date_str = (event_date_str if len(event_date_str) > 2 else '') + _event_dates[:-2] + ' of ' + _event_month
    event_datetime = event_dates[0].event_datetime
    event_date_str += ' - ' + event_datetime.strftime(
        "%-I:%M %p" if event_datetime.strftime("%M") != '00' else "%-I %p")

    return event_date_str


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
