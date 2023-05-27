import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import current_app
import requests


def send_ga_event(description, category, action, label, value=1):
    payload = {
        'v': 1,
        'tid': current_app.config['GA_ID'],
        'cid': 888,
        't': 'event',
        'ec': category,
        'ea': action,
        'el': label,
        'ev': value
    }

    if current_app.config.get("DISABLE_STATS"):
        current_app.logger.info(f"Stats disabled: {description}: {category} - {label}, {value}")
        return

    if current_app.config["ENVIRONMENT"] != "test":
        headers = {'User-Agent': f'NA-API-{current_app.config.get("ENVIRONMENT")}'}
        r = requests.post("http://www.google-analytics.com/collect", data=payload, headers=headers)
        if r.status_code != 200:
            current_app.logger.info(f"Failed to track {description}: {category} - {label}, {value}")
        else:
            current_app.logger.info(f"Sent stats for {description}: {category} - {label}, {value}")
