from flask import Blueprint

from flask_jwt_extended import jwt_required
from app.na_celery.email_tasks import send_periodic_emails_task
from app.na_celery.event_tasks import send_event_email_reminder_task


celery_blueprint = Blueprint('celery', __name__)


@celery_blueprint.route('/celery/send_periodic_emails')
@jwt_required()
def celery_send_periodic_emails():
    send_periodic_emails_task.apply_async()
    return "ok", 200


@celery_blueprint.route('/celery/send_event_email_reminder')
@jwt_required()
def celery_send_event_email_reminder():
    send_event_email_reminder_task.apply_async()
    return "ok", 200
