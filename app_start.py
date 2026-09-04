import base64
import click
import json
import os
import requests
import werkzeug
from zipfile import ZipFile, ZIP_DEFLATED
werkzeug.cached_property = werkzeug.utils.cached_property

from app import create_app, db
from app.comms.encryption import encrypt
from app.dao.magazines_dao import dao_get_magazine_by_old_id
from app.routes.magazines import get_magazine_filename
from app.utils.pdf import extract_topics as _extract_topics
from app.utils.pdf import extract_first_page as _extract_first_page
from app.utils.storage import Storage
from flask_migrate import Migrate

app = create_app()
migrate = Migrate(app, db)


@app.cli.command("list-routes")
def list_routes():
    """List URLs of all application routes."""
    for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
        print("{:10} {}".format(", ".join(rule.methods - set(['OPTIONS', 'HEAD'])), rule.rule))


@app.cli.command("upload-magazine")
@click.argument("file_path")
def generate_web_images(year=None):
    """Generate web images, thumbnail, standard."""
    app.logger.info('Generate web images')
    storage = Storage(app.config['STORAGE'])
    storage.generate_web_images(year)


@app.cli.command("get-unsubcode")
@click.argument("member_id")
def get_unsubcode(member_id):
    unsubcode = encrypt(
        "{}={}".format(app.config['EMAIL_TOKENS']['member_id'], member_id),
        app.config['EMAIL_UNSUB_SALT']
    )
    print(unsubcode)


@app.cli.command("extract-topics")
def extract_topics():
    filename = 'Bi_monthly_Issue 49.pdf'
    with open(os.path.join('data', 'pdfs', filename), "rb") as f:
        pdf_binary = f.read()
        print(_extract_topics(pdf_binary))


@app.cli.command("extract-first-page")
def extract_first_page():
    filename = 'Bi_monthly_Issue 49.pdf'
    with open(os.path.join('data', 'pdfs', filename), "rb") as f:
        pdf = f.read()

        pdf_base64 = base64.b64encode(pdf).decode('utf-8')
        pdf_bin = base64.b64decode(pdf_base64)
        _extract_first_page(pdf_bin)


@app.cli.command("send-stats")
def send_stats():
    from app.na_celery.stats_tasks import send_num_subscribers_and_social_stats
    send_num_subscribers_and_social_stats(inc_subscribers=False)


@app.cli.command("create-test-zip")
def create_test_zip():
    """Create zipfile for testing"""
    DATA_ROOT = os.path.join('tests', 'test_files')
    with ZipFile(f"{DATA_ROOT}/art.zip", 'w', ZIP_DEFLATED) as myzip:
        os.chdir(DATA_ROOT + "/docs")
        myzip.write("Test 1.docx", arcname="test_1_final.docx")
        myzip.write("Test 2.docx", arcname="test_2_final.docx")


@app.cli.command("upload-file")
@click.argument("filename")
@click.argument("target-filename")
def upload_file(filename, target_filename=None):
    """Upload file."""
    if not target_filename:
        target_filename = f'test/{filename}'
    app.logger.info('Upload file')
    storage = Storage(app.config['STORAGE'])
    storage.upload_blob(filename, target_filename, set_public=True)


@app.cli.command("upload-magazines")
@click.argument("folder")
def upload_magazines(folder='data/pdfs'):
    """Upload magazines."""
    app.logger.info('Upload magazines')
    storage = Storage(app.config['STORAGE'])

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
                            content_type='app/pdf'
                        )

                payload = {
                    'old_id': item['id'],
                    'title': item['Title'],
                    'old_filename': item['ImageFilename'],
                    'filename': new_filename
                }

                auth_request('magazine/import', access_token, payload)
        else:
            app.logger.info("Magazine already uploaded: %s", item['Title'])


@app.cli.command("upload-magazine")
@click.argument("file_path")
@click.argument("title")
@click.argument("create_magazine")
def upload_magazine(file_path='', title='', create_magazine='False'):
    """Upload magazine."""
    app.logger.info(f'Upload magazine {file_path}')
    storage = Storage(app.config['STORAGE'])

    filename = file_path.split('/')[-1]
    with open(file_path, "rb") as f:
        pdf = f.read()

        if create_magazine == 'True':
            access_token = get_access_token()

            payload = {
                'title': title,
                'filename': filename,
                'pdf_data': base64.b64encode(pdf).decode('utf-8'),
            }

            auth_request('magazine', access_token, payload)

        storage.upload_blob_from_base64string(
            filename,
            filename,
            base64.b64encode(pdf),
            content_type='application/pdf'
        )


@app.cli.command("get-emails-for-sending")
def get_emails_for_sending():
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

    SQLAlchemy(app)

    from app.dao.emails_dao import dao_get_approved_emails_for_sending
    emails = dao_get_approved_emails_for_sending()

    if emails:
        for email in emails:
            print(email.subject)
    else:
        print("No emails to send")


def get_access_token():
    auth_payload = {
        "username": app.config['ADMIN_CLIENT_ID'],
        "password": app.config['ADMIN_CLIENT_SECRET'],
    }

    auth_response = requests.post(
        os.path.join(app.config['API_BASE_URL'], 'auth/login'),
        data=json.dumps(auth_payload),
        headers={'Content-Type': 'application/json'},
    )

    return auth_response.json()["access_token"]


def auth_request(endpoint, access_token, payload):
    return requests.post(
        os.path.join(app.config['API_BASE_URL'], endpoint),
        data=json.dumps(payload),
        headers={'Authorization': 'Bearer {}'.format(access_token)},
    )
