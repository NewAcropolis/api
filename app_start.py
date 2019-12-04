import base64
import json
import os
import re
import requests
from flask_script import Manager, Server
from app import create_app, db
from app.dao.magazines_dao import dao_get_magazine_by_old_id
from app.routes.magazines import get_magazine_filename, MAGAZINE_PATTERN
from app.storage.utils import Storage
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
def upload_magazines(folder=None):
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
                    with open(os.path.join(folder, filename)) as f:
                        binary = f.read()

                        storage.upload_blob_from_base64string(
                            filename,
                            new_filename,
                            base64.b64encode(binary),
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
