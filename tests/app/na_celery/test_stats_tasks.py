from freezegun import freeze_time
from mock import call

from app.na_celery.stats_tasks import send_num_subscribers


class WhenProcessingSendNumSubscribersTask:

    @freeze_time("2020-11-01T10:00:00")
    def it_sends_num_subscribers(self, mocker, db_session, sample_member):
        mock_send_ga_event = mocker.patch('app.na_celery.stats_tasks.send_ga_event')

        send_num_subscribers()

        assert mock_send_ga_event.call_args == call(
            'Number of subscribers', 'members', 'num_subscribers_october', 1)
