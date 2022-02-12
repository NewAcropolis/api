from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from flask import current_app
import json
import pytz
import re
import requests

from app import celery
from app.comms.stats import send_ga_event
from app.dao.users_dao import dao_get_admin_users
from app.dao.members_dao import dao_get_active_member_count


def get_facebook_count():
    response = None
    try:
        response = requests.get(current_app.config.get('FACEBOOK_URL'))
        soup = BeautifulSoup(response.content, 'html.parser')
        div = soup.find('div', text=re.compile('total follows', re.IGNORECASE))
        return int(div.previousSibling.get_text().replace(',', ''))
    except Exception as e:
        current_app.logger.error(f"Problem retrieving facebook followers count: {str(e)}")
        current_app.logger.error(f"Facebook URL: {current_app.config.get('FACEBOOK_URL')}")
        current_app.logger.error(f"Content: {response.content}")
        return 'failed'


def get_instagram_count():
    instagram_url = current_app.config.get('INSTAGRAM_URL')
    if not instagram_url:
        current_app.logger.error("Instagram URL not set")
        return 'url not set'

    try:
        response = requests.get(instagram_url)
        instagram_json = json.loads(response.content)
        return instagram_json['data']['user']['edge_followed_by']['count']
    except Exception as e:
        current_app.logger.error(f"Problem retrieving instagram followers count: {str(e)}")
        return 'failed'


# @celery.task(name='send_num_subscribers_and_social_stats')
def send_num_subscribers_and_social_stats(inc_subscribers=True):
    current_app.logger.info('Task send_num_subscribers_and_social_stats received: {}')
    report_month = (datetime.today() - timedelta(weeks=2)).strftime('%B').lower()

    num_subscribers = num_new_subscribers = 0

    if inc_subscribers:
        month_year = (datetime.today() - timedelta(weeks=2)).strftime('%m-%Y')
        num_subscribers = dao_get_active_member_count()
        send_ga_event(
            "Number of subscribers",
            "members",
            f"num_subscribers_{report_month}",
            num_subscribers
        )

        num_new_subscribers = dao_get_active_member_count(month=month_year.split('-')[0], year=month_year.split('-')[1])

        send_ga_event(
            "Number of new subscribers",
            "members",
            f"num_new_subscribers_{report_month}",
            num_new_subscribers
        )

    facebook_count = get_facebook_count()
    if facebook_count:
        send_ga_event(
            "Facebook followers count",
            "social",
            f"num_facebook_{report_month}",
            facebook_count
        )

    instagram_count = get_instagram_count()
    if instagram_count:
        send_ga_event(
            "Instagram followers count",
            "social",
            f"num_instagram_{report_month}",
            instagram_count
        )

    return num_subscribers, num_new_subscribers, facebook_count, instagram_count
