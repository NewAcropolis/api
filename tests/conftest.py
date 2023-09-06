import base64
import os
import subprocess
import datetime

from bs4 import BeautifulSoup

import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

import pytest
from alembic.command import upgrade
from alembic.config import Config
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager
import sqlalchemy
from flask_jwt_extended import create_access_token, create_refresh_token

from app import create_app, db as _db, get_env
from app.models import APPROVED, EVENT, MAGAZINE, TICKET_STATUS_UNUSED
from tests.db import (
    create_article,
    create_book,
    create_email,
    create_email_provider,
    create_event,
    create_event_date,
    create_event_type,
    create_fee,
    create_magazine,
    create_marketing,
    create_member,
    create_order,
    create_reject_reason,
    create_speaker,
    create_ticket,
    create_user,
    create_venue
)

TEST_DATABASE_URI = os.environ.get("TEST_DATABASE_URI", "postgresql://localhost/na_api_" + get_env() + '_test')
TEST_ADMIN_USER = 'admin@example.com'
TEST_ADMIN_USER_CONFIG = 'admin-config@example.com'


@pytest.yield_fixture(scope='session')
def app():
    _app = create_app(**{
        'TESTING': True,
        'DB_HOST': 'localhost',
        'ENVIRONMENT': 'test',
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'PREFERRED_URL_SCHEME': 'http',
        'DELIVERY_ID': 'delivery-53441e2a-c991-4d38-a785-394277bbc30c',
        'ADMIN_CLIENT_ID': 'testadmin',
        'ADMIN_CLIENT_SECRET': 'testsecret',
        'TOKEN_EXPIRY': 1,
        'GOOGLE_APPLICATION_CREDENTIALS': './path/to/creds',
        'JWT_SECRET_KEY': 'secret',
        'ADMIN_USERS': [TEST_ADMIN_USER_CONFIG],
        'EMAIL_DOMAIN': 'example.com',
        'EMAIL_TOKENS': {"member_id": "memberid", "type": "typeid"},
        'EMAIL_SALT': 'test',
        'EMAIL_UNSUB_SALT': 'unsub_test',
        'EMAIL_RESTRICT': None,
        'EMAIL_ANYTIME': False,
        'TEST_EMAIL': 'test@example.com',
        'EVENTS_MAX': 2,
        'GOOGLE_APPLICATION_CREDENTIALS': 'test',
        'PROJECT': 'test-project',
        'STORAGE': 'test-store',
        'PAYPAL_URL': 'https://test.paypal',
        'PAYPAL_USER': 'seller@test.com',
        'PAYPAL_PASSWORD': 'test pass',
        'PAYPAL_SIG': 'paypal signature',
        'PAYPAL_RECEIVER': 'receiver@example.com',
        'PAYPAL_RECEIVER_ID': 'AABBCC1',
        'PAYPAL_VERIFY_URL': 'https://test.paypal/verify',
        'API_BASE_URL': 'http://test',
        'IMAGES_URL': 'http://test/images',
        'FRONTEND_URL': 'http://frontend-test',
        'FRONTEND_ADMIN_URL': 'http://frontend-test/admin',
        'CELERY_BROKER_URL': 'http://mock-celery',
        'EMAIL_DELAY': 1,
        'GA_ID': 1,
        'INSTAGRAM_URL': 'http://example.instagram',
        'DISABLE_STATS': False,
        'EMAIL_DISABLED': None,
        'SMTP_SERVER': 'test.smtp.server',
        'TEST_VERIFY': None
    })

    ctx = _app.app_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture(scope='session')
def db(app):
    assert _db.engine.url.database.endswith('_test'), 'dont run tests against main db'

    create_test_db_if_does_not_exist(_db)

    Migrate(app, _db)
    Manager(_db, MigrateCommand)
    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    ALEMBIC_CONFIG = os.path.join(BASE_DIR, 'migrations')
    config = Config(ALEMBIC_CONFIG + '/alembic.ini')
    config.set_main_option("script_location", ALEMBIC_CONFIG)

    with app.app_context():
        upgrade(config, 'head')

    yield _db

    _db.session.remove()
    _db.get_engine(app).dispose()


@pytest.fixture(scope='function')
def db_session(db):
    yield db

    db.session.remove()
    for tbl in reversed(db.metadata.sorted_tables):
        if tbl.name not in [
            "article_states", "event_states", "email_types", "email_states", "ticket_types", "ticket_statuses"
        ]:
            db.engine.execute(tbl.delete())
    db.session.commit()


@pytest.fixture(scope='function')
def sample_article(db):
    return create_article(title='Ancient Greece')


@pytest.fixture(scope='function')
def sample_book(db):
    return create_book(title='The Spirits of Nature')


@pytest.fixture(scope='function')
def sample_email(db):
    return create_email(
        details='<strong>Fees:</strong> 10, <strong>Concessions:</strong> 5',
        created_at='2019-06-01',
        expires='2019-07-01',
        email_state=APPROVED
    )


@pytest.fixture(scope='function')
def sample_magazine_email(db):
    magazine = create_magazine(title="New mag", filename="new_mag.pdf")
    return create_email(
        magazine_id=magazine.id,
        details='<strong>Fees:</strong> 10, <strong>Concessions:</strong> 5',
        created_at='2019-06-01',
        expires='2019-07-01',
        email_type=MAGAZINE,
        email_state=APPROVED
    )


@pytest.fixture(scope='function')
def sample_email_provider(db):
    return create_email_provider(
        name='Sample Email Provider', minute_limit=10, daily_limit=25, monthly_limit=100,
        api_key='sample-api-key', api_url='http://sample-api-url.com', pos=0,
    )


@pytest.fixture(scope='function')
def sample_magazine(db):
    return create_magazine(
        title='Test magazine',
        filename='magazine.pdf'
    )


@pytest.fixture(scope='function')
def sample_marketing(db):
    return create_marketing(
        old_id=1,
        description='Leaflet'
    )


@pytest.fixture(scope='function')
def sample_member(db):
    return create_member(
        name='Sue Green',
        email='sue@example.com'
    )


@pytest.fixture(scope='function')
def sample_event(db):
    return create_event(title='test_title', description='test description')


@pytest.fixture(scope='function')
def sample_event_with_dates(db, sample_event_date_without_event):
    another_event_date = create_event_date(event_datetime='2018-01-02 19:00')
    return create_event(
        title='test_title',
        description='test description',
        event_dates=[sample_event_date_without_event, another_event_date]
    )


@pytest.fixture(scope='function')
def sample_event_type(db):
    return create_event_type(event_type='short course')


@pytest.fixture(scope='function')
def sample_event_date(db, sample_event):
    return create_event_date(event_id=sample_event.id)


@pytest.fixture(scope='function')
def sample_event_date_without_event(db):
    return create_event_date()


@pytest.fixture(scope='function')
def sample_fee(db, sample_event_type):
    return create_fee(fee=5, conc_fee=3, event_type_id=sample_event_type.id)


@pytest.fixture(scope='function')
def sample_reject_reason(db, sample_event):
    return create_reject_reason(sample_event.id)


@pytest.fixture(scope='function')
def sample_speaker(db):
    return create_speaker(name='Paul White')


@pytest.fixture(scope='function')
def sample_user(db):
    return create_user(email='test_user@example.com', name='Test User')


@pytest.fixture(scope='function')
def sample_admin_user(db):
    return create_user(email=TEST_ADMIN_USER, name='Admin User', access_area='admin')


@pytest.fixture(scope='function')
def sample_order(db, sample_book, sample_event_with_dates):
    event_dates = sample_event_with_dates.get_sorted_event_dates()
    ticket = create_ticket(
        status=TICKET_STATUS_UNUSED,
        event_id=sample_event_with_dates.id,
        eventdate_id=event_dates[0]['id']
    )

    return create_order(books=[sample_book], tickets=[ticket], txn_id='111222333')


@pytest.fixture(scope='function')
def sample_venue(db):
    return create_venue()


# token set around 2017-12-10T23:10:00
@pytest.fixture(scope='function')
def sample_decoded_token():
    start, expiry = get_unixtime_start_and_expiry()

    return {
        'jti': 'test',
        'exp': expiry,
        'iat': start,
        'fresh': False,
        'type': 'access',
        'nbf': start,
        'identity': 'admin'
    }


@pytest.fixture
def sample_uuid():
    return '42111e2a-c990-4d38-a785-394277bbc30c'


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


def base64img_encoded():
    base64img_encoded = base64.b64encode(base64img.encode())
    base64img_encoded = base64.b64encode(base64img_encoded).decode('utf-8')
    return base64img_encoded


@pytest.fixture(scope='function')
def mock_storage(mocker):
    mocker.patch('app.utils.storage.Storage.__init__', return_value=None)
    mocker.patch('app.utils.storage.Storage.upload_blob_from_base64string')
    mocker.patch('app.utils.storage.Storage.blob_exists', return_value=True)
    mock_storage_rename = mocker.patch("app.utils.storage.Storage.rename_image")

    return {
        'mock_storage_rename': mock_storage_rename
    }


@pytest.fixture(scope='function')
def mock_storage_no_blob(mocker):
    mocker.patch('app.utils.storage.Storage.__init__', return_value=None)
    mocker.patch('app.utils.storage.Storage.upload_blob_from_base64string')
    mocker.patch('app.utils.storage.Storage.blob_exists', return_value=False)


def create_test_db_if_does_not_exist(db):
    try:
        conn = db.engine.connect()
        conn.close()

    except sqlalchemy.exc.OperationalError as e:
        if 'database "{}" does not exist'.format(TEST_DATABASE_URI.split('/')[-1:][0]) in str(e):
            db_url = sqlalchemy.engine.url.make_url(TEST_DATABASE_URI)
            dbname = db_url.database

            if db_url.drivername == 'postgresql':
                subprocess.call(['/usr/bin/env', 'createdb', '-h', 'db', '-U', 'postgres', dbname])
        else:
            raise


def request(url, method, data=None, headers=None):
    r = method(url, data=data, headers=headers)
    r.soup = BeautifulSoup(r.get_data(as_text=True), 'html.parser')
    return r


def create_authorization_header(client_id='testadmin'):
    expires = datetime.timedelta(minutes=1)

    token = create_access_token(identity=client_id, expires_delta=expires)
    return 'Authorization', 'Bearer {}'.format(token)


def create_refresh_header(client_id='testadmin'):
    token = create_refresh_token(identity=client_id)
    return 'Authorization', 'Bearer {}'.format(token)


def get_unixtime_start_and_expiry(year=2017, month=12, day=10, hour=23, minute=10):
    from time import mktime
    d = datetime.datetime(year, month, day, hour, minute, 0)
    unixtime = mktime(d.timetuple())

    added_time = 900
    unixtime_expiry = unixtime + added_time
    return unixtime, unixtime_expiry
