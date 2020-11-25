from flask import url_for
from mock import call
from tests.conftest import create_authorization_header


class WhenGettingSocialStats:

    def it_sends_social_stats(self, mocker, client):
        mock_send_social_stats = mocker.patch(
            'app.routes.stats.rest.send_num_subscribers_and_social_stats',
            return_value=(100, 100)
        )
        response = client.get(
            url_for('stats.send_social_stats'),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert mock_send_social_stats.called
        assert mock_send_social_stats.call_args == call(inc_subscribers=False)
        assert response.get_data(as_text=True) == "facebook=100, instagram=100"
