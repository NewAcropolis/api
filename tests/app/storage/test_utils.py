import base64
import pytest

from mock import Mock

from app.storage.utils import Storage, sizeof_fmt


class MockBlob:
    def __call__(self, filename=None):
        self.name = filename
        self.filename = filename
        return self

    def upload_from_filename(self, filename):
        self.source_filename = filename

    def upload_from_string(self, string, content_type=None):
        self.source_string = string

    def make_public(self):
        self.public = True


class MockBucket:
    def __init__(self, bucket_name):
        self.name = bucket_name
        self.bucket_created = False

    def blob(self, filename=None):
        self.destination_filename = filename
        self.blob = MockBlob()
        return self.blob

    def upload_blob(self, filename):
        self.upload_block = True

    def list_blobs(self, prefix, delimiter):
        self.prefix = prefix
        self.delimiter = delimiter
        return ['prefix']

    def create_bucket(self, bucket_name):
        self.bucket_created = True


class MockEmptyStorageClient:
    def __init__(self, credentials=None, project=None):
        self.credentials = credentials
        self.project = project
        self.buckets = []

    def list_buckets(self):
        return self.buckets

    def create_bucket(self, bucket_name):
        self.buckets.append(bucket_name)

        return MockBucket(bucket_name)


class MockStorageClient:
    def list_buckets(self):
        return [MockBucket('test-store')]

    def get_bucket(self, bucket_name):
        return MockBucket(bucket_name)

    def list_blobs(self, bucket_name, **kwargs):
        return [Mock()]


class WhenUsingStorage:

    base64img = (
        'iVBORw0KGgoAAAANSUhEUgAAADgAAAAsCAYAAAAwwXuTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAEMElEQVRoge2ZTUxcVRTH'
        '/+fed9+bDxFEQUCmDLWbtibWDE2MCYGa6rabykITA7pV6aruNGlcGFe6c2ui7k1cmZp0YGdR2pjqoklBpkCVykem8/'
        'HeffceF8MgIC3YvDczNP0ls5l3cuf8cuee++65wGMe09LQQQP5xkkXJ4rpjYU40zkY7UcA/NZWopM3gv1iHyg4M5NTuRPrPf5'
        '6cJ4ETgsHg1ZHludDIxQQBphLpOiasfTrtVvPXB4a+nnPzO4rWFnOjroJO25CfkF5UAgBrTm+rP8nyiHAAzgALNNsCHzjdXZdI'
        'dop+h/BmzePeYPd+lXW9pIj4eqAwa3jtSeuV9PQhvKqKC7S4Hy1/myHIHNfSq84nyqXR7Tf+mK7cdMEU6G89O2HlLldAQCxPSD'
        '4U55TaRoJqodPDgCCEkOmaMR38HH9uy3B4tLAceViUt8zzckuInTJwE3QmerikbPApuDaXLbDk3yBCMnDOHPbYQYISEiJC7x6t'
        'F0AQNrzn1dpejnwD7ndJoHPcBKc0WX/uACAkOUr7Ntm5xUp2mdYQR8RAPBa5vqjMnvbceTmGoxajqj2aTah2bVNRAIB1pBmrm3'
        'AzfaMXNBNEqQU3wp2Jo2lWVKbok0yjWUGjWGjeuevyM6Fd2HxgbW4Kh1qiqgT07gEAEQwwO08M6bDu9lhhnnbcWiIBNCod9y4B'
        'HdABAvM55kxFa5khtmIcaVsDhS/aEME6xCBgcIUgCm9lBlmBxNKUQ4UfSWvE/0aPCCqrzDtdhfeCUO8pzX94qp/jz1R0jTBOqq'
        '7MO12L0xUfXq/WsWsktEWoqYL1kn2FaaSvYXxUlVOWkNhVJINXYMPggGqLg+MSrJvMlhGVXhaQlCvDJzRlicSyr5YKzjRjd00Q'
        'WbI8E7/MEkxIaU9BQkEQfSVtOGCvJDps2l6w6ziNSFtRiiObYsAGihYWhnoVYbHNPF5pfhJ6zMMA2HMx7S4BLeyvvdXtsexdgz'
        'WjqkU2sIKIyjH9Kt7EL0gA5aRKC4f61LQ47DmnJdCm26wWB0CAP9O//UoR+TaPqbdJJLN7q/GMoNCsgPACar7RseOAGq9iyhhR'
        'ss0jgUAaI3FVuihRI3rUU1QWL6kYniTbyauR/Cr+FIAgEp5v4dVKsRxXGkGShECjT88Nl8JAKDOWxvG4HNmVB6FvyolBIyhr6l'
        'vqbx1XEo8t3BZB/hCPRFxxWkwtSs0zid7wu+BXedB91nznSlx3k0fzml00wTjU75QFBeJlsrAHje8PJdN6Db7mZI8AsTXK4kSI'
        'QBH0f43vHWYc8pfXRl1gLcE8UukAF1uPVGVItgKw0oqGiM/8bqe/nHfO/rtzMzk1Kmjd8+SNKd1hV4nQKIVPAlgwKgk/6DL8qp'
        'nwp+of/Hv+4QejLW5bEeHsLQRXZoPTTuAdSv4qcH59f1i/wGycsTRKGME7gAAAABJRU5ErkJggg=='
    )

    def it_uses_gce_creds_for_storage_client_without_google_creds_envs(self, app, mocker):
        mocker.patch.dict('os.environ', {
            'GOOGLE_APPLICATION_CREDENTIALS': '',
            'PROJECT': 'test-project'
        })

        mock_google_creds = mocker.patch("google.auth.compute_engine.Credentials", return_value='google-credentials')
        mocker.patch("google.cloud.storage.Client", MockEmptyStorageClient)

        store = Storage('test-store')

        assert mock_google_creds.called
        assert store.storage_client.credentials == 'google-credentials'
        assert store.storage_client.project == 'test-project'
        assert store.storage_client.list_buckets() == ['test-store']

    def it_logs_args_if_development_and_no_google_config(self, app, mocker):
        mocker.patch.dict('app.storage.utils.current_app.config', {
            'ENVIRONMENT': 'development',
            'GOOGLE_APPLICATION_CREDENTIALS': '',
        })

        mock_logger = mocker.patch("app.storage.utils.current_app.logger.info")

        Storage('test-store')

        assert mock_logger.called

    def it_uses_api_key_for_storage_client_with_google_creds_envs(self, app, mocker):
        mocker.patch.dict('os.environ', {
            'GOOGLE_APPLICATION_CREDENTIALS': 'path/to/creds'
        })

        mock_google_creds = mocker.patch("google.auth.compute_engine.Credentials")
        mocker.patch("google.cloud.storage.Client", MockEmptyStorageClient)

        store = Storage('test-store')

        assert not mock_google_creds.called
        assert store.storage_client.list_buckets() == ['test-store']

    def it_doesnt_create_the_bucket_if_it_exists(self, app, mocker):
        mocker.patch.dict('os.environ', {
            'GOOGLE_APPLICATION_CREDENTIALS': 'path/to/creds'
        })

        mocker.patch("google.cloud.storage.Client", MockStorageClient)
        mock_google_creds = mocker.patch("google.auth.compute_engine.Credentials")

        store = Storage('test-store')

        assert not mock_google_creds.called
        assert not store.bucket.bucket_created
        assert store.bucket.name == 'test-store'

    def it_uploads_a_file(self, app, mocker):
        mocker.patch.dict('os.environ', {
            'GOOGLE_APPLICATION_CREDENTIALS': 'path/to/creds'
        })

        mocker.patch("google.cloud.storage.Client", MockStorageClient)
        mocker.patch("google.auth.compute_engine.Credentials")

        store = Storage('test-store')
        store.upload_blob('source', 'destination')

        assert store.bucket.destination_filename == 'destination'
        assert store.bucket.blob.source_filename == 'source'
        assert store.bucket.blob.public

    def it_generates_web_images(self, app, mocker):
        mocker.patch.dict('os.environ', {
            'GOOGLE_APPLICATION_CREDENTIALS': 'path/to/creds'
        })

        mocker.patch("google.cloud.storage.Client", MockStorageClient)
        mocker.patch("google.auth.compute_engine.Credentials")
        mock_generate_web_image = mocker.patch("app.storage.utils.Storage.generate_web_image")

        store = Storage('test-store')
        store.generate_web_images()

        assert mock_generate_web_image.called

    def it_logs_args_if_development_and_no_google_config_when_upload_file(self, app, mocker):
        mocker.patch.dict('app.storage.utils.current_app.config', {
            'ENVIRONMENT': 'development',
            'GOOGLE_APPLICATION_CREDENTIALS': '',
        })

        mock_logger = mocker.patch("app.storage.utils.current_app.logger.info")

        store = Storage('test-store')
        store.upload_blob('source', 'destination')

        assert mock_logger.called

    def it_checks_blob_exists(self, app, mocker):
        mocker.patch.dict('os.environ', {
            'GOOGLE_APPLICATION_CREDENTIALS': 'path/to/creds'
        })

        mocker.patch("google.cloud.storage.Client", MockStorageClient)
        mocker.patch("google.auth.compute_engine.Credentials")

        store = Storage('test-store')
        res = store.blob_exists('prefix', 'delimiter')

        assert store.bucket.prefix == 'prefix'
        assert store.bucket.delimiter == 'delimiter'
        assert res

    def it_logs_args_if_development_and_no_google_config_when_blob_exists(self, app, mocker):
        mocker.patch.dict('app.storage.utils.current_app.config', {
            'ENVIRONMENT': 'development',
            'GOOGLE_APPLICATION_CREDENTIALS': '',
        })

        mock_logger = mocker.patch("app.storage.utils.current_app.logger.info")

        store = Storage('test-store')
        store.blob_exists('prfix', 'delimiter')

        assert mock_logger.called

    def it_uploads_blob_from_base64string(self, app, mocker):
        mocker.patch.dict('os.environ', {
            'GOOGLE_APPLICATION_CREDENTIALS': 'path/to/creds'
        })

        mocker.patch("google.cloud.storage.Client", MockStorageClient)
        mocker.patch("google.auth.compute_engine.Credentials")

        store = Storage('test-store')
        store.upload_blob_from_base64string('test.png', '2019/new_test.png', self.base64img)

        assert store.bucket.blob.source_string == base64.b64decode(self.base64img)

    def it_logs_args_if_development_and_no_google_config_when_upload_from_base64string(self, app, mocker):
        mocker.patch.dict('app.storage.utils.current_app.config', {
            'ENVIRONMENT': 'development',
            'GOOGLE_APPLICATION_CREDENTIALS': '',
        })

        mock_logger = mocker.patch("app.storage.utils.current_app.logger.info")

        store = Storage('test-store')
        store.upload_blob_from_base64string('test.png', '2019/new_test.png', self.base64img)

        assert mock_logger.called

    @pytest.mark.parametrize('num,exp_res', [
        (1024 * 1000 * 2000, '1.9GiB'),
        (1500, '1.5KiB'),
        (800, '800.0B'),
    ])
    def it_gets_formatted_size(self, app, mocker, num, exp_res):
        res = sizeof_fmt(num)
        assert res == exp_res
