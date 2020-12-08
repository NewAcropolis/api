from flask import Blueprint, current_app
from flask_jwt_extended import jwt_required

from app.na_celery.stats_tasks import send_num_subscribers_and_social_stats
from app.errors import register_errors

stats_blueprint = Blueprint('stats', __name__)
register_errors(stats_blueprint)


@stats_blueprint.route('/stats/social')
@jwt_required
def send_social_stats():
    current_app.logger.info("Sending social stats...")
    _, _, facebook_count, instagram_count = send_num_subscribers_and_social_stats(inc_subscribers=False)
    current_app.logger.info("Social stats %r, %r", facebook_count, instagram_count)
    return f'facebook={facebook_count}, instagram={instagram_count}'


@stats_blueprint.route('/stats/subscribers_and_social')
@jwt_required
def send_subscribers_and_social():
    current_app.logger.info("Sending subscribers and social stats...")
    num_subscribers, num_new_subscribers, facebook_count, instagram_count = send_num_subscribers_and_social_stats(
        inc_subscribers=True)
    current_app.logger.info("Social stats %r, %r", facebook_count, instagram_count)
    return f'subscribers={num_subscribers}, new subscribers={num_new_subscribers}, ' \
        f'facebook={facebook_count}, instagram={instagram_count}'
