import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import current_app
from freezegun import freeze_time
from mock import call
import requests_mock

from app.na_celery.stats_tasks import send_num_subscribers_and_social_stats
from tests.db import create_member


class WhenProcessingSendNumSubscribersTask:

    @freeze_time("2021-01-01T10:00:00")
    def it_sends_num_subscribers_and_social_stats(self, mocker, db, db_session):
        create_member(created_at='2020-10-10T10:00:00')
        create_member(email='test2@example.com', created_at='2020-12-10T10:00:00')
        mock_send_ga_event = mocker.patch('app.na_celery.stats_tasks.send_ga_event')

        with requests_mock.mock() as r:
            r.get(
                current_app.config.get('FACEBOOK_URL'),
                text='<html><body><div><div>1,000</div><div>Total follows</div></div></body></html>')
            r.get(
                current_app.config.get('INSTAGRAM_URL'),
                text='{"data":{"user":{"edge_followed_by":{"count":1100,"page_info":'
                     '{"has_next_page":false,"end_cursor":null},"edges":[]}}},"status":"ok"}')

            send_num_subscribers_and_social_stats()
            assert mock_send_ga_event.call_args_list == [
                call('Number of subscribers', 'members', 'num_subscribers_december', 2),
                call('Number of new subscribers', 'members', 'num_new_subscribers_december', 1),
                call('Facebook followers count', 'social', 'num_facebook_december', 1000),
                call('Instagram followers count', 'social', 'num_instagram_december', 1100),
            ]

    @freeze_time("2021-01-01T10:00:00")
    def it_doesnt_send_instagram_stats(self, mocker, db, db_session):
        mocker.patch.dict('app.application.config', {
            'INSTAGRAM_URL': ''
        })

        create_member(created_at='2020-10-10T10:00:00')
        create_member(email='test2@example.com', created_at='2020-12-10T10:00:00')
        mock_send_ga_event = mocker.patch('app.na_celery.stats_tasks.send_ga_event')

        with requests_mock.mock() as r:
            r.get(
                current_app.config.get('FACEBOOK_URL'),
                text='<html><body><div><div>1,000</div><div>Total follows</div></div></body></html>')
            r.get(
                current_app.config.get('INSTAGRAM_URL'),
                text='{"data":{"user":{"edge_followed_by":{"count":1100,"page_info":'
                     '{"has_next_page":false,"end_cursor":null},"edges":[]}}},"status":"ok"}')

            send_num_subscribers_and_social_stats()
            assert mock_send_ga_event.call_args_list == [
                call('Number of subscribers', 'members', 'num_subscribers_december', 2),
                call('Number of new subscribers', 'members', 'num_new_subscribers_december', 1),
                call('Facebook followers count', 'social', 'num_facebook_december', 1000),
                call('Instagram followers count', 'social', 'num_instagram_december', 'url not set'),
            ]

    @freeze_time("2020-12-01T10:00:00")
    def it_sends_num_subscribers_and_failed_social_stats(self, mocker, db, db_session):
        create_member(created_at='2020-10-10T10:00:00')
        mock_send_ga_event = mocker.patch('app.na_celery.stats_tasks.send_ga_event')

        with requests_mock.mock() as r:
            r.get(
                current_app.config.get('FACEBOOK_URL'),
                text='<html><body><div><div>1,000</div><div>Total followers</div></div></body></html>')
            r.get(
                current_app.config.get('INSTAGRAM_URL'),
                text='<html><head><meta property="og:description" content="'
                     '1,100 Following, 200 Posts"/></head></html>')

            send_num_subscribers_and_social_stats()
            assert mock_send_ga_event.call_args_list == [
                call('Number of subscribers', 'members', 'num_subscribers_november', 1),
                call('Number of new subscribers', 'members', 'num_new_subscribers_november', 0),
                call('Facebook followers count', 'social', 'num_facebook_november', 'failed'),
                call('Instagram followers count', 'social', 'num_instagram_november', 'failed'),
            ]
