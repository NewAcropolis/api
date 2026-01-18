import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import url_for
from mock import call
from tests.conftest import create_authorization_header


class WhenGettingSocialStats:

    def it_sends_social_stats(self, mocker, client):
        mock_send_social_stats = mocker.patch(
            'app.routes.stats.rest.send_num_subscribers_and_social_stats',
            return_value=(0, 0, 100, 100)
        )
        response = client.get(
            url_for('stats.send_social_stats'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert mock_send_social_stats.called
        assert mock_send_social_stats.call_args == call(inc_subscribers=False)
        assert response.get_data(as_text=True) == "facebook=100, instagram=100"


class WhenGettingSubscribersAndSocialStats:

    def it_sends_subscribers_and_social_stats(self, mocker, client):
        mock_send_social_stats = mocker.patch(
            'app.routes.stats.rest.send_num_subscribers_and_social_stats',
            return_value=(200, 200, 100, 100)
        )
        response = client.get(
            url_for('stats.send_subscribers_and_social_stats'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert mock_send_social_stats.called
        assert mock_send_social_stats.call_args == call(inc_subscribers=True)
        assert response.get_data(as_text=True) == "subscribers=200, new subscribers=200, facebook=100, instagram=100"

    def it_sends_email_stats(self, mocker, client):
        mocker.patch(
            'app.routes.stats.rest.dao_get_emails_sent_count',
            return_value=10
        )
        mocker.patch('requests.post')
        response = client.get(
            url_for('stats.send_email_stats', month=12, year=2020),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.get_data(as_text=True) == "email count for 12/2020 = 10"


class WhenGettingStats:
    def it_returns_email_stats_for_month_year(self, mocker, client):
        mocker.patch(
            'app.routes.stats.rest.dao_get_emails_sent_count',
            return_value=10
        )

        response = client.get(
            url_for('stats.get_email_stats', month=12, year=2020),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.json == {"count": 10, "month": 12, "year": 2020}

    def it_returns_member_stats_for_month_year(self, mocker, client):
        mocker.patch(
            'app.routes.stats.rest.dao_get_active_member_count',
            return_value=100
        )
        mocker.patch(
            'app.routes.stats.rest.dao_get_new_member_count',
            return_value=10
        )
        mocker.patch(
            'app.routes.stats.rest.dao_get_unsubscribed_member_count',
            return_value=5
        )

        response = client.get(
            url_for('stats.get_members_stats', month=12, year=2020),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.json == {
            "month": 12,
            "year": 2020,
            "active_members_count": 100,
            "new_members_count": 10,
            "unsub_count": 5
        }

    def it_returns_all_stats(self, mocker, client):
        mocker.patch(
            'app.routes.stats.rest.dao_get_emails_sent_count',
            return_value=10
        )
        mocker.patch(
            'app.routes.stats.rest.dao_get_active_member_count',
            return_value=100
        )
        mocker.patch(
            'app.routes.stats.rest.dao_get_new_member_count',
            return_value=10
        )
        mocker.patch(
            'app.routes.stats.rest.dao_get_unsubscribed_member_count',
            return_value=5
        )

        response = client.get(
            url_for('stats.get_stats', month=12, year=2020),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.json == {
            "emails": {
                "count": 10
            },
            "members": {
                "active": 100,
                "new": 10,
                "unsub": 5
            }
        }
