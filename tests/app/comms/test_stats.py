from app.comms.stats import send_ga_event


class WhenSendingStats:

    def it_doesnt_send_in_test_environment(self, app, mocker):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'test'
        })

        mock_post = mocker.patch('app.comms.stats.requests.post')

        send_ga_event("test", "test", "test", "test")

        assert not mock_post.called

    def it_sends_in_non_test_environments(self, app, mocker):
        mocker.patch.dict('app.application.config', {
            'ENVIRONMENT': 'development'
        })

        mock_post = mocker.patch('app.comms.stats.requests.post')

        send_ga_event("test", "test", "test", "test")

        assert mock_post.called
