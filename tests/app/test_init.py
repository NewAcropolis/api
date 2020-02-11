from mock import call
import pytest

from app import create_app, configure_logging, LogTruncatingFormatter
from app.config import Development, Preview, Live


class WhenInitializingApp(object):

    @pytest.mark.parametrize("returnval,config_class", [
        ('www-preview', Preview),
        ('www-live', Live),
        ('', Development)
    ])
    def it_has_correct_environment(self, mocker, returnval, config_class):
        mocker.patch("os.environ", {})
        mocker.patch.dict('app.application.config', {
            'SQLALCHEMY_DATABASE_URI': 'db://localhost/test_db',
            'API_BASE_URL': 'http://test',
            'FRONTEND_URL': 'http://frontend-test',
            'ENVIRONMENT': 'test'
        })
        mocker.patch("app.get_root_path", return_value=returnval)
        mocked_config = mocker.patch("app.application.config.from_object", return_value={})
        create_app()

        assert mocked_config.called
        assert mocked_config.call_args == call(config_class)

    @pytest.mark.parametrize("app_server,expected_msg", [
        ('gunicorn', 'Gunicorn logging configured'),
        ('flask', 'Flask logging configured')
    ])
    def it_configures_correct_logging(self, mocker, app_server, expected_msg):
        mocker.patch.dict('app.application.config', {
            'APP_SERVER': app_server,
            'SQLALCHEMY_DATABASE_URI': 'db://localhost/test_db'
        })
        mock_logger_info = mocker.patch("app.application.logger.info")

        configure_logging()
        assert mock_logger_info.called
        assert mock_logger_info.call_args == call(expected_msg)

    def it_exits_from_configure_logging_if_already_configured(self, mocker):
        mocker.patch.dict('app.application.config', {
            'APP_SERVER': 'flask',
            'SQLALCHEMY_DATABASE_URI': 'db://localhost/test_db'
        })

        mocker.patch("app.logging.StreamHandler", return_value='logger')
        mocker.patch('app.application.logger.handlers', ['logger'])
        mock_handler = mocker.patch("app.application.logger.addHandler")

        configure_logging()
        assert not mock_handler.called

    def it_inits_celery_when_is_celery_kwarg_set(self, mocker):
        mocker.patch('app.configure_logging')
        mocker.patch('app.report_missing_config')
        mocker.patch('app.init_app')
        mocker.patch('app.SQLAlchemy.__init__')
        mock_celery = mocker.patch('app.celery.init_app')

        create_app(is_celery=True)
        assert mock_celery.called


class WhenFormattingLogs(object):

    @pytest.mark.parametrize('log_string,expected', [
        ('127.0.0.1 - - [20/Nov/2017 23:38:25 +0000]Truncated', 'Truncated\nTruncated'),
        ('127.0.0.1 - - Not truncated', '127.0.0.1 - - Not truncated\n127.0.0.1 - - Not truncated')
    ])
    def it_truncates_start_of_logs_matching_pattern(self, app, mocker, log_string, expected):
        class mock_record(object):

            def __init__(self):
                self._msg = log_string

            @property
            def exc_info(self):
                return None

            @property
            def exc_text(self):
                return self._msg

            @property
            def msg(self):
                return self._msg

            @msg.setter
            def msg(self, val):
                self._msg = val

            def getMessage(self):
                return self._msg

        test = mock_record()

        log = LogTruncatingFormatter()

        res = log.format(test)

        assert res == expected
