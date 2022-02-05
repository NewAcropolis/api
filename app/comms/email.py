from email.mime.text import MIMEText
from flask import current_app, jsonify, render_template
from html import escape
import json
import os
import re
import requests
import smtplib
import ssl

from html.parser import HTMLParser

from na_common.dates import get_nice_event_dates

from app.comms.encryption import encrypt
from app.errors import InvalidRequest
from app.models import BASIC, EVENT, MAGAZINE, BEARER_AUTH, API_AUTH
from app.dao.events_dao import dao_get_event_by_id
from app.dao.emails_dao import (
    dao_get_last_minute_email_count_for_provider,
    dao_get_past_hour_email_count_for_provider,
    dao_get_todays_email_count_for_provider,
    dao_get_last_30_days_email_count_for_provider
)
from app.dao.email_providers_dao import (
    dao_get_first_email_provider, dao_get_next_email_provider, dao_get_next_available_email_provider
)
from app.dao.magazines_dao import dao_get_magazine_by_id

h = HTMLParser()


def get_email_provider(override=False, email_provider=None):
    if not email_provider:
        email_provider = dao_get_first_email_provider()
        if not email_provider:
            return None

    minute_email_count = hourly_email_count = daily_email_count = monthly_email_count = 0

    def _get_email_provider_or_count(limit, dao_count, limit_reached):
        email_count = dao_count(email_provider.id)
        if email_count > limit:
            next_email_provider = dao_get_next_available_email_provider(email_provider.pos)
            if next_email_provider:
                return get_email_provider(override, next_email_provider)

            if override:
                next_email_provider = dao_get_next_email_provider(email_provider.pos)

                if next_email_provider:
                    return get_email_provider(override, next_email_provider)
            else:
                email_provider.limit = 0
                setattr(email_provider, limit_reached, True)
            return email_provider
        return email_count

    if email_provider.monthly_limit > 0:
        email_provider_or_count = _get_email_provider_or_count(
            email_provider.monthly_limit,
            dao_get_last_30_days_email_count_for_provider,
            'monthly_limit_reached')

        if type(email_provider_or_count) == int:
            email_provider.limit = email_provider.monthly_limit - email_provider_or_count
        else:
            return email_provider_or_count

    if email_provider.daily_limit > 0:
        email_provider_or_count = _get_email_provider_or_count(
            email_provider.daily_limit,
            dao_get_todays_email_count_for_provider,
            'daily_limit_reached')

        if type(email_provider_or_count) == int:
            email_provider.limit = email_provider.daily_limit - email_provider_or_count
        else:
            return email_provider_or_count

    if email_provider.hourly_limit > 0:
        email_provider_or_count = _get_email_provider_or_count(
            email_provider.hourly_limit,
            dao_get_past_hour_email_count_for_provider,
            'hourly_limit_reached')

        if type(email_provider_or_count) == int:
            email_provider.limit = email_provider.hourly_limit - email_provider_or_count
        else:
            return email_provider_or_count
    if email_provider.minute_limit > 0:
        email_provider_or_count = _get_email_provider_or_count(
            email_provider.minute_limit,
            dao_get_last_minute_email_count_for_provider,
            'minute_limit_reached')

        if type(email_provider_or_count) == int:
            email_provider.limit = email_provider.minute_limit - email_provider_or_count
        else:
            return email_provider_or_count

    return email_provider


def get_email_html(email_type, **kwargs):
    member_id = kwargs.get('member_id')
    unsubcode = encrypt(
        "{}={}".format(current_app.config['EMAIL_TOKENS']['member_id'], member_id),
        current_app.config['EMAIL_UNSUB_SALT']
    ) if member_id else None

    if email_type == EVENT:
        event = dao_get_event_by_id(kwargs.get('event_id'))
        current_app.logger.debug('Email Tokens %s', current_app.config['EMAIL_TOKENS'])
        return render_template(
            'emails/events.html',
            event=event,
            event_dates=get_nice_event_dates(event.event_dates),
            description=h.unescape(event.description),
            details=kwargs.get('details'),
            extra_txt=kwargs.get('extra_txt'),
            unsubcode=unsubcode,
            remote_access=kwargs.get('remote_access'),
            remote_pw=kwargs.get('remote_pw'),
        )
    elif email_type == MAGAZINE:
        magazine = dao_get_magazine_by_id(kwargs.get('magazine_id'))
        topics = []
        if magazine.topics:
            if all([':' in t for t in magazine.topics.split('\n')]):
                _topics = [(t.split(':')[0], t.split(':')[1]) for t in magazine.topics.split('\n')]
            else:
                _topics = [
                    ("Missing divider", "Use : as divider between topic header and sub-header"),
                    ("Topics", magazine.topics)
                ]

            for title, description in _topics:
                topics.append({'title': title, 'description': description})
        return render_template(
            'emails/magazine.html',
            magazine=magazine,
            topics=topics,
            unsubcode=unsubcode
        )
    elif email_type == BASIC:
        return render_template(
            'emails/basic.html',
            title=kwargs.get('title', ''),
            message=kwargs.get('message'),
            unsubcode=unsubcode
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
    if current_app.config['EMAIL_DISABLED']:
        current_app.logger.info("Emails disabled, unset EMAIL_DISABLED env var to re-enable")
        return 200, None
    if current_app.config['ENVIRONMENT'] != 'live' or current_app.config.get('EMAIL_RESTRICT'):
        if f"test@{current_app.config['EMAIL_DOMAIN']}" not in to:
            message = message.replace('<body>', '<body><div>Test email, intended for {}</div>'.format(to))
            to = current_app.config['TEST_EMAIL']

    if not from_email:
        from_email = 'noreply@{}'.format(current_app.config['EMAIL_DOMAIN'])
    if not from_name:
        from_name = 'New Acropolis'

    email_provider = get_email_provider(override)

    if email_provider:
        if hasattr(email_provider, "minute_limit_reached"):
            raise InvalidRequest('Minute limit reached', 429)
        elif hasattr(email_provider, "hourly_limit_reached"):
            raise InvalidRequest('Hourly limit reached', 429)
        elif hasattr(email_provider, "daily_limit_reached"):
            raise InvalidRequest('Daily limit reached', 429)
        elif hasattr(email_provider, "monthly_limit_reached"):
            raise InvalidRequest('Monthly limit reached', 429)

        if email_provider.smtp_server:
            smtp_info = {
                "SMTP_SERVER": email_provider.smtp_server,
                "SMTP_USER": email_provider.smtp_user,
                "SMTP_PASS": email_provider.smtp_password,
            }
            response_code = send_smtp_email(to, subject, message, from_name="New Acropolis", smtp_info=smtp_info)
            return response_code, email_provider.id
        else:
            data = get_email_data(email_provider.data_map, to, subject, message, from_email, from_name)
            data = data if email_provider.as_json else json.dumps(data)

            headers = None
            if email_provider.headers:
                headers = {
                    'accept': 'application/json',
                    'Content-Type': 'application/json'
                }
                if email_provider.auth_type == BEARER_AUTH:
                    headers['Authorization'] = f"Bearer {email_provider.api_key}"
                elif email_provider.auth_type == API_AUTH:
                    headers['api-key'] = email_provider.api_key

            response = requests.post(
                email_provider.api_url,
                auth=('api', email_provider.api_key) if email_provider.auth_type == API_AUTH else None,
                headers=headers,
                data=data,
            )

            response.raise_for_status()
            current_app.logger.info('Sent email: {}, response: {}'.format(subject, response.text))
            if current_app.config['ENVIRONMENT'] != 'live':  # pragma: no cover
                current_app.logger.info('Email to: {}'.format(to))
                current_app.logger.info('Email provider: {}'.format(email_provider.api_url))
                current_app.logger.info('Email key: {}'.format(email_provider.api_key[:5]))

            return response.status_code, email_provider.id
    else:
        data = {
            'to': to,
            'from_email': from_email,
            'from_name': from_name,
            'subject': subject,
            'message': message
        }
        current_app.logger.info('No email providers configured, email would have sent: {}'.format(data))


def send_smtp_email(to, subject, message, from_email=None, from_name='', smtp_info=None):  # pragma: no cover
    if current_app.config['EMAIL_DISABLED']:
        current_app.logger.info("Emails disabled, unset EMAIL_DISABLED env var to re-enable")
        return 200

    if not to:
        current_app.logger.info("smtp: no email to send to")
        return

    current_app.logger.info("Starting to send smtp")

    if not smtp_info:
        smtp_info = {
            "SMTP_SERVER": current_app.config.get("SMTP_SERVER"),
            "SMTP_USER": current_app.config.get("SMTP_USER"),
            "SMTP_PASS": current_app.config.get("SMTP_PASS"),
        }
    if not from_email:
        from_email = f"noreply@{current_app.config['EMAIL_DOMAIN']}"
    if from_name:
        _from = f"{from_name}<{from_email}>"
    else:
        _from = f"New Acropolis Admin<{from_email}>"

    if isinstance(to, list):
        to = ','.join(to)

    msg = MIMEText(message, "html")
    msg['Subject'] = subject
    msg['From'] = _from
    msg['To'] = to
    msg['reply-to'] = from_email

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_info['SMTP_SERVER'], 587) as conn:
            conn.starttls(context=context)
            conn.ehlo()
            current_app.logger.info('SU: %r', smtp_info["SMTP_USER"][:5])
            current_app.logger.info('SP: %r', smtp_info["SMTP_PASS"][:3])
            conn.login(smtp_info["SMTP_USER"], smtp_info["SMTP_PASS"])
            conn.send_message(msg)
            current_app.logger.info("Successfully sent smtp email")
            return 200
    except smtplib.SMTPAuthenticationError as e:
        current_app.logger.error("Error sending smtp email %r", e)
        return e.smtp_code
