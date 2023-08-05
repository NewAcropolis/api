import base64
import json
import os
import re
import requests
import werkzeug
from zipfile import ZipFile, ZIP_DEFLATED

werkzeug.cached_property = werkzeug.utils.cached_property
from flask_script import Manager, Server
from app import create_app, db
from app.comms.encryption import decrypt, encrypt, get_tokens
from app.dao.magazines_dao import dao_get_magazine_by_old_id
from app.routes.magazines import get_magazine_filename, MAGAZINE_PATTERN
from app.utils.pdf import extract_topics as _extract_topics
from app.utils.pdf import extract_first_page
from app.utils.storage import Storage
from flask_migrate import Migrate, MigrateCommand


application = create_app()
migrate = Migrate(application, db)
manager = Manager(application)

manager.add_command('db', MigrateCommand)
manager.add_command("runserver", Server(host='0.0.0.0'))


@manager.command
def list_routes():
    """List URLs of all application routes."""
    for rule in sorted(application.url_map.iter_rules(), key=lambda r: r.rule):
        print("{:10} {}".format(", ".join(rule.methods - set(['OPTIONS', 'HEAD'])), rule.rule))


@manager.command
def generate_web_images(year=None):
    """Generate web images, thumbnail, standard."""
    application.logger.info('Generate web images')
    storage = Storage(application.config['STORAGE'])
    storage.generate_web_images(year)


@manager.command
def get_unsubcode(member_id):
    unsubcode = encrypt(
        "{}={}".format(application.config['EMAIL_TOKENS']['member_id'], member_id),
        application.config['EMAIL_UNSUB_SALT']
    )
    print(unsubcode)


@manager.command
def extract_topics():
    filename = 'Bi_monthly_Issue 49.pdf'
    with open(os.path.join('data', 'pdfs', filename), "rb") as f:
        pdf_binary = f.read()
        print(_extract_topics(pdf_binary))


@manager.command
def extract_first_page():
    filename = 'Bi_monthly_Issue 49.pdf'
    with open(os.path.join('data', 'pdfs', filename), "rb") as f:
        pdf = f.read()

        pdf_base64 = base64.b64encode(pdf).decode('utf-8')
        pdf_bin = base64.b64decode(pdf_base64)

        extract_first_page(pdf_bin)


@manager.command
def send_stats():
    from app.na_celery.stats_tasks import send_num_subscribers_and_social_stats
    send_num_subscribers_and_social_stats(inc_subscribers=False)


@manager.command
def create_test_zip():
    """Create zipfile for testing"""
    DATA_ROOT = os.path.join('tests', 'test_files')
    with ZipFile(f"{DATA_ROOT}art.zip", 'w', ZIP_DEFLATED) as myzip:
        os.chdir(DATA_ROOT + "/docs")
        myzip.write("Test 1.docx", arcname="test_1_final.docx")
        myzip.write("Test 2.docx", arcname="test_2_final.docx")


@manager.command
def upload_file(filename):
    """Upload file."""
    application.logger.info('Upload file')
    storage = Storage(application.config['STORAGE'])
    storage.upload_blob(filename, f'test/{filename}', set_public=True)


@manager.command
def upload_magazines(folder='data/pdfs'):
    """Upload magazines."""
    application.logger.info('Upload magazines')
    storage = Storage(application.config['STORAGE'])

    share_items = []
    with open(os.path.join('data', 'shareitems.json')) as f:
        json_shareitems = json.loads(f.read())
        for item in json_shareitems:
            share_items.append(item)

    access_token = get_access_token()

    for item in share_items:
        if not dao_get_magazine_by_old_id(item['id']):
            filename = item['ImageFilename']
            new_filename = get_magazine_filename(filename)
            if new_filename:
                if folder:
                    with open(os.path.join(folder, filename), "rb") as f:
                        pdf = f.read()

                        storage.upload_blob_from_base64string(
                            filename,
                            new_filename,
                            base64.b64encode(pdf),
                            content_type='application/pdf'
                        )

                payload = {
                    'old_id': item['id'],
                    'title': item['Title'],
                    'old_filename': item['ImageFilename'],
                    'filename': new_filename
                }

                auth_request('magazine/import', access_token, payload)
        else:
            application.logger.info("Magazine already uploaded: %s", item['Title'])


def get_access_token():
    auth_payload = {
        "username": application.config['ADMIN_CLIENT_ID'],
        "password": application.config['ADMIN_CLIENT_SECRET'],
    }

    auth_response = requests.post(
        os.path.join(application.config['API_BASE_URL'], 'auth/login'),
        data=json.dumps(auth_payload),
        headers={'Content-Type': 'application/json'},
    )

    return auth_response.json()["access_token"]


def auth_request(endpoint, access_token, payload):
    return requests.post(
        os.path.join(application.config['API_BASE_URL'], endpoint),
        data=json.dumps(payload),
        headers={'Authorization': 'Bearer {}'.format(access_token)},
    )


if __name__ == '__main__':
    manager.run()
