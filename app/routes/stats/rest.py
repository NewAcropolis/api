import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import jwt_required

from app.comms.stats import send_ga_event
from app.dao.emails_dao import dao_get_emails_sent_count
from app.dao.members_dao import dao_get_active_member_count, dao_get_new_member_count, dao_get_unsubscribed_member_count
from app.na_celery.stats_tasks import send_num_subscribers_and_social_stats
from app.errors import register_errors

stats_blueprint = Blueprint('stats', __name__)
register_errors(stats_blueprint)


@stats_blueprint.route('/stats/social')
@jwt_required()
def send_social_stats():
    current_app.logger.info("Sending social stats...")
    _, _, facebook_count, instagram_count = send_num_subscribers_and_social_stats(inc_subscribers=False)
    current_app.logger.info("Social stats %r, %r", facebook_count, instagram_count)
    return f'facebook={facebook_count}, instagram={instagram_count}'


@stats_blueprint.route('/stats/subscribers_and_social')
@jwt_required()
def send_subscribers_and_social_stats():
    current_app.logger.info("Sending subscribers and social stats...")
    num_subscribers, num_new_subscribers, facebook_count, instagram_count = send_num_subscribers_and_social_stats(
        inc_subscribers=True)
    current_app.logger.info("Social stats %r, %r", facebook_count, instagram_count)
    return f'subscribers={num_subscribers}, new subscribers={num_new_subscribers}, ' \
        f'facebook={facebook_count}, instagram={instagram_count}'


@stats_blueprint.route('/stats/send/emails/<int:month>/<int:year>')
@jwt_required()
def send_email_stats(month=None, year=None):
    count = dao_get_emails_sent_count(month=month, year=year)

    send_ga_event(
        "Emails sent count",
        "email",
        "send_success",
        "Email Stats",
        value=count
    )

    current_app.logger.info(f"Email count for {month}/{year}: {count}")
    return f'email count for {month}/{year} = {count}'


@stats_blueprint.route('/stats/emails/<int:month>/<int:year>')
@jwt_required()
def get_email_stats(month=None, year=None):
    count = dao_get_emails_sent_count(month=month, year=year)

    return jsonify(
        {
            "month": month,
            "year": year,
            "count": count
        }
    )


@stats_blueprint.route('/stats/members/<int:month>/<int:year>')
@jwt_required()
def get_members_stats(month=None, year=None):
    active_members_count = dao_get_active_member_count()
    new_member_count = dao_get_new_member_count(month=month, year=year)
    unsub_count = dao_get_unsubscribed_member_count(month=month, year=year)

    return jsonify(
        {
            "month": month,
            "year": year,
            "active_members_count": active_members_count,
            "new_members_count": new_member_count,
            "unsub_count": unsub_count
        }
    )


@stats_blueprint.route('/stats/<int:month>/<int:year>')
@jwt_required()
def get_stats(month=None, year=None):
    emails_count = dao_get_emails_sent_count(month=month, year=year)
    active_members_count = dao_get_active_member_count()
    new_member_count = dao_get_new_member_count(month=month, year=year)
    unsub_count = dao_get_unsubscribed_member_count(month=month, year=year)

    return jsonify(
        {
            "emails": {
                "count": emails_count
            },
            "members": {
                "active": active_members_count,
                "new": new_member_count,
                "unsub": unsub_count
            }
        }
    )
