from datetime import datetime, timedelta
from flask import current_app
import pytz

from app import celery
from app.comms.stats import send_ga_event
from app.dao.users_dao import dao_get_admin_users
from app.dao.members_dao import dao_get_active_member_count


@celery.task(name='send_num_subscribers')
def send_num_subscribers():
    current_app.logger.info('Task send_num_subscribers received: {}')

    send_ga_event(
        "Number of subscribers",
        "members",
        f"num_subscribers_{(datetime.today() - timedelta(weeks=1)).strftime('%B').lower()}",
        dao_get_active_member_count()
    )
