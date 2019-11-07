import os
from flask_script import Manager, Server
from app import create_app, db
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


if __name__ == '__main__':
    manager.run()
