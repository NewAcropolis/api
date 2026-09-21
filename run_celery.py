#!/usr/bin/env python


from app import celery, create_app  # noqa


application = create_app(is_celery=True)
application.app_context().push()
