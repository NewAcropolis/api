from collections import namedtuple

from mock import call
import pytest

from app.config import main


class WhenGettingPort(object):

    @pytest.mark.parametrize('env,expected_port', [
        ('preview', 4000),
        ('development', 5001),
        ('live', 8000),
        ('', 'No environment')
    ])
    def it_gets_right_port(self, mocker, env, expected_port):
        args = namedtuple('args', ['env'])
        args.env = env

        mocker.patch("app.config.parse_args", return_value=args)
        mocked_output = mocker.patch("app.config.output")

        main(['-e', env])
        assert mocked_output.call_args == call(expected_port)
