from celery import Celery
from celery.schedules import crontab
from celery.task.control import revoke
from flask import current_app


class NewAcropolisCelery(Celery):  # pragma: no cover
    def init_app(self, app):
        if app.config['ENVIRONMENT'] == 'test':
            return

        if not app.config['CELERY_BROKER_URL']:
            app.logger.info('Celery broker URL not set')
            return

        super().__init__(
            app.import_name,
            broker=app.config['CELERY_BROKER_URL'],
        )

        app.logger.info('Setting up celery: %s', app.config['CELERY_BROKER_URL'])

        self.conf.update(app.config)

        app.logger.info('Celery beat schedule: %r', app.config['CELERYBEAT_SCHEDULE'])

        class ContextTask(self.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        self.Task = ContextTask


def revoke_task(task_id):  # pragma: no cover
    res = revoke(task_id, terminate=True)
    current_app.logger.info('Task revoked: %d, %r', task_id, res)
    return res
