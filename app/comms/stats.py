from flask import current_app
import requests


def send_ga_event(description, category, action, label):
    payload = {
        'v': 1,
        'tid': current_app.config['GA_ID'],
        'cid': 888,
        't': 'event',
        'ec': category,
        'ea': action,
        'el': label
    }

    if current_app.config.get("DISABLE_STATS"):
        current_app.logger.info(f"Stats disabled: {description}: {category} - {label}")
        return

    if current_app.config["ENVIRONMENT"] != "test":
        r = requests.post("http://www.google-analytics.com/collect", data=payload)
        if r.status_code != 200:
            current_app.logger.info(f"Failed to track {description}: {category} - {label}")
