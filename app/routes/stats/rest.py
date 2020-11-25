from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.na_celery.stats_tasks import send_num_subscribers_and_social_stats
from app.errors import register_errors

stats_blueprint = Blueprint('stats', __name__)
register_errors(stats_blueprint)


@stats_blueprint.route('/stats/social')
@jwt_required
def send_social_stats():
    facebook_count, instagram_count = send_num_subscribers_and_social_stats(inc_subscribers=False)
    return f'facebook={facebook_count}, instagram={instagram_count}'
