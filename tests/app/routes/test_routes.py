import pytest

from app.routes import is_running_locally


@pytest.mark.parametrize('url,expected_res', [
    ('http://localhost:5001/test', True),
    ('http://127.0.0.1:5001/test', True),
    ('http://live.website/test', False),
])
class WhenCheckingRequest:
    def it_returns_true_if_running_locally(self, client, mocker, url, expected_res):
        class MockRequest:
            url_root = None

            def __init__(self, url_root):
                self.url_root = url_root

        mocker.patch('app.routes.request', MockRequest(url))

        res = is_running_locally()
        assert res == expected_res
