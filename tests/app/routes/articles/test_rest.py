import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

import base64
import os
import pytest
import uuid
from zipfile import BadZipFile

from flask import json, url_for
from freezegun import freeze_time
from mock import call

from sqlalchemy.orm.exc import NoResultFound

from app.dao.articles_dao import dao_create_article, dao_get_articles
from app.models import Article, DRAFT, READY, APPROVED, REJECTED
from tests.conftest import create_authorization_header, base64img_encoded, TEST_ADMIN_USER

from tests.db import create_article


sample_articles = [
    {
        "id": "1",
        "title": "Forty Years Fighting Racism and Intolerance",
        "author": "John Gilbert",
        "content": """<h2>A century with no solidarity</h2>\r\n One of the worst plagues that the twentieth century
        has had to \r\n bear is racial discrimination.""",
        "entrydate": "2015-11-01"
    },
    {
        "id": "2",
        "title": "Modern Mythology",
        "author": "Sabine Leitner",
        "content": """Despite their universal existence in all civilizations and all \r\ntimes of history,
        myths have often been scoffed at and regarded as old wives\u2019 \r\ntales.""",
        "entrydate": "2016-01-30"
    },
]


class WhenGettingArticles:

    def it_returns_all_articles(self, client, sample_article, db_session):
        response = client.get(
            url_for('articles.get_articles'),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert len(data) == 1
        assert data[0]['id'] == str(sample_article.id)

    def it_returns_all_articles_summary(self, client, sample_article, db_session):
        response = client.get(
            url_for('articles.get_articles_summary'),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert len(data) == 1
        assert data[0]['id'] == str(sample_article.id)

    def it_returns_up_to_5_articles_summary(self, client, sample_article, db_session):
        create_article(title='test 1', article_state=APPROVED)
        create_article(title='test 2', article_state=APPROVED)
        create_article(title='test 3', article_state=APPROVED)
        create_article(title='test 4', article_state=APPROVED)
        create_article(title='test 5', article_state=APPROVED)
        response = client.get(
            url_for('articles.get_articles_summary'),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert len(data) == 5

    @pytest.mark.parametrize("method_call", [
        'get_articles_by_tags',
        'get_articles_summary_by_tags'
    ])
    def it_returns_articles_by_tags_and_other_articles(self, client, method_call, sample_article, db_session):
        article_1 = create_article(title='test 1', tags='music', image_filename='a.jpg', article_state=APPROVED)
        article_2 = create_article(title='test 2', tags='art', image_filename='b.jpg', article_state=APPROVED)
        article_3 = create_article(title='test 3', tags='music,art', image_filename='c.jpg', article_state=APPROVED)
        article_4 = create_article(title='test 4', tags='physics', image_filename='d.jpg', article_state=APPROVED)
        create_article(title='test 5', tags='')

        response = client.get(
            url_for(f'articles.{method_call}', tags='art,physics'),
            headers=[create_authorization_header()]
        )

        assert response.status_code == 200
        data = json.loads(response.get_data(as_text=True))

        assert len(data) == 5
        if method_call == 'get_articles_by_tags':
            assert article_2.serialize() == data[0]
            assert article_4.serialize() == data[1]
        else:
            assert article_2.serialize_summary() == data[0]
            assert article_4.serialize_summary() == data[1]

    def it_returns_articles_by_tags_prioritised_and_all_articles(self, client, sample_article, db_session):
        article_1 = create_article(title='test 1', tags='music', image_filename='a.jpg', article_state=APPROVED)
        article_2 = create_article(title='test 2', tags='art', image_filename='b.jpg', article_state=APPROVED)
        article_3 = create_article(title='test 3', tags='music,art', image_filename='c.jpg', article_state=APPROVED)
        article_4 = create_article(title='test 4', tags='physics', image_filename='d.jpg', article_state=APPROVED)
        create_article(title='test 5', tags='')

        response = client.get(
            url_for('articles.get_all_articles_with_tags_prioritised', tags='art,physics'),
            headers=[create_authorization_header()]
        )

        assert response.status_code == 200
        data = json.loads(response.get_data(as_text=True))

        assert len(data) == 6
        assert article_2.serialize() == data[0]
        assert article_4.serialize() == data[1]


class WhenGettingArticleByID:

    def it_returns_correct_article(self, client, sample_article, db_session):
        response = client.get(
            url_for('article.get_article_by_id', article_id=str(sample_article.id)),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['id'] == str(sample_article.id)


class WhenPostingImportArticles(object):

    def it_creates_articles_for_imported_articles(self, client, db_session):
        response = client.post(
            url_for('articles.import_articles'),
            data=json.dumps(sample_articles),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_articles = json.loads(response.get_data(as_text=True))['articles']
        assert len(json_articles) == len(sample_articles)
        for i in range(0, len(sample_articles) - 1):
            assert json_articles[i]["old_id"] == int(sample_articles[i]["id"])
            assert json_articles[i]["title"] == sample_articles[i]["title"]
            assert json_articles[i]["author"] == sample_articles[i]["author"]
            assert json_articles[i]["content"] == sample_articles[i]["content"]
            assert json_articles[i]["created_at"] == sample_articles[i]["entrydate"]

    def it_does_not_create_article_for_imported_articles_with_duplicates(self, client, db_session):
        duplicate_article = {
            "id": "1",
            "title": "Forty Years Fighting Racism and Intolerance",
            "author": "John Gilbert",
            "content": """<h2>A century with no solidarity</h2>\r\n One of the worst plagues that the twentieth century
            has had to \r\n bear is racial discrimination.""",
            "entrydate": "2015-11-01"
        },

        sample_articles.extend(duplicate_article)

        response = client.post(
            url_for('articles.import_articles'),
            data=json.dumps(sample_articles),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201

        json_articles = json.loads(response.get_data(as_text=True))['articles']
        assert len(json_articles) == len(sample_articles) - 1  # don't add in duplicate article
        for i in range(0, len(sample_articles) - 1):
            assert json_articles[i]["old_id"] == int(sample_articles[i]["id"])
            assert json_articles[i]["title"] == sample_articles[i]["title"]
            assert json_articles[i]["author"] == sample_articles[i]["author"]
            assert json_articles[i]["content"] == sample_articles[i]["content"]
            assert json_articles[i]["created_at"] == sample_articles[i]["entrydate"]


class WhenPostingUpdateArticle:

    def it_updates_an_article(self, client, db_session, sample_article):
        data = {
            'title': 'Updated',
            'image_filename': 'new_filename.jpg'
        }
        response = client.post(
            url_for('article.update_article_by_old_id', old_id=sample_article.old_id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json['image_filename'] == data['image_filename']


class WhenPostingAddArticle:

    def it_adds_an_article(self, client, db_session, sample_magazine, mock_storage):
        data = {
            'title': 'New',
            'author': 'Somone',
            'content': 'Something interesting',
            'image_filename': 'new_filename.jpg',
            'image_data': base64img_encoded(),
            'magazine_id': str(sample_magazine.id),
            'tags': 'Some tag',
            'article_state': 'draft'
        }
        response = client.post(
            url_for('article.add_article'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201
        assert response.json['image_filename'] == f"{response.json['id']}"
        assert response.json['magazine_id'] == data['magazine_id']

        articles = Article.query.all()

        assert len(articles) == 1
        assert articles[0].title == data['title']
        assert articles[0].article_state == DRAFT
        assert articles[0].tags == data['tags'] + ","
        assert articles[0].magazine_id == sample_magazine.id

    def it_handles_duplicate_article_when_adding(self, client, db_session, sample_article):
        data = {
            'title': 'Ancient Greece',
            'author': 'Mrs Black',
            'content': 'Something interesting',
            'image_filename': 'new_filename.jpg',
            'image_data': base64img_encoded(),
            'tags': 'Some tag',
            'article_state': 'draft'
        }
        response = client.post(
            url_for('article.add_article'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400
        assert response.json['message'] == f"Article: Ancient Greece by Mrs Black exists ({sample_article.id})"
        assert response.json['result'] == 'error'

        articles = Article.query.all()

        assert len(articles) == 1

    def it_raises_400_if_image_filename_not_found(
        self, client, db_session, sample_magazine, mock_storage_no_blob
    ):
        data = {
            'title': 'New',
            'author': 'Somone',
            'content': 'Something interesting',
            'image_filename': 'new_filename.jpg',
            'magazine_id': str(sample_magazine.id),
            'tags': 'Some tag',
            'article_state': 'draft'
        }
        response = client.post(
            url_for('article.add_article'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400
        data = json.loads(response.get_data(as_text=True))

        article = Article.query.one()

        assert data == {"message": f"articles/{article.id} does not exist", "result": "error"}


class WhenPostingUpdateArticle:

    @freeze_time("2023-03-11T14:00:00")
    def it_updates_an_article(
        self, mocker, client, db_session, mock_storage,
        sample_email_provider, sample_admin_user, sample_article
    ):
        mock_smtp = mocker.patch('app.routes.articles.rest.send_smtp_email')
        UNIX_TIME = "1678543200.0"
        data = {
            'title': 'Updated',
            'author': 'Updated Somone',
            'content': 'Something updated',
            'image_filename': 'updated_filename.jpg',
            'image_data': base64img_encoded(),
            'tags': 'Updated tag',
            'article_state': READY
        }
        response = client.post(
            url_for('article.update_article_by_id', article_id=sample_article.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json['image_filename'] == f"{str(sample_article.id)}-temp?{UNIX_TIME}"

        articles = Article.query.all()

        assert len(articles) == 1
        assert articles[0].title == data['title']
        assert articles[0].article_state == READY
        assert articles[0].tags == data['tags']
        assert mock_smtp.called

    def it_does_not_update_an_article(
        self, mocker, client, db_session, mock_storage,
        sample_email_provider, sample_admin_user, sample_uuid
    ):
        mock_smtp = mocker.patch('app.routes.articles.rest.send_smtp_email')
        UNIX_TIME = "1678543200.0"
        data = {
            'title': 'Updated',
            'author': 'Updated Somone',
            'content': 'Something updated',
            'image_filename': 'updated_filename.jpg',
            'image_data': base64img_encoded(),
            'tags': 'Updated tag',
            'article_state': READY
        }

        mocker.patch('app.routes.articles.rest.dao_get_article_by_id', side_effect=NoResultFound())

        response = client.post(
            url_for('article.update_article_by_id', article_id=sample_uuid),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))

        assert json_resp['message'] == 'article not found: {}'.format(sample_uuid)

    def it_raises_error_if_file_not_found(
        self, mocker, client, db_session, sample_article, mock_storage_no_blob
    ):
        data = {
            'title': 'Updated',
            'article_state': READY,
            'image_filename': 'test.jpg'
        }
        response = client.post(
            url_for('article.update_article_by_id', article_id=sample_article.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        assert response.status_code == 400

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['message'] == 'test.jpg does not exist'

    def it_renames_temp_image_file_when_approved(
        self, mocker, client, db_session, sample_article,
        mock_storage
    ):
        data = {
            'title': 'Updated',
            'magazine_id': '',
            'author': 'Updated Somone',
            'content': 'Something updated',
            'image_filename': f'{str(sample_article.id)}-temp?222',
            'tags': 'Updated tag',
            'article_state': APPROVED
        }

        response = client.post(
            url_for('article.update_article_by_id', article_id=sample_article.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        assert mock_storage['mock_storage_rename'].called
        assert mock_storage['mock_storage_rename'].call_args == call(
            f'articles/{str(sample_article.id)}-temp', f'articles/{str(sample_article.id)}')
        assert response.json['image_filename'] == f'{str(sample_article.id)}'

    def it_logs_warning_if_no_temp_image_file_when_approved(
        self, mocker, client, db_session, sample_article,
        mock_storage
    ):
        mock_logger = mocker.patch('app.routes.articles.rest.current_app.logger.warn')

        data = {
            'title': 'Updated',
            'author': 'Updated Somone',
            'content': 'Something updated',
            'image_filename': f'articles/{str(sample_article.id)}?222',
            'tags': 'Updated tag',
            'article_state': APPROVED
        }

        response = client.post(
            url_for('article.update_article_by_id', article_id=sample_article.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200

        assert not mock_storage['mock_storage_rename'].called
        assert mock_logger.called

    def it_updates_an_article_to_rejected(
        self, mocker, client, db, db_session, sample_admin_user, sample_article, mock_storage
    ):
        mock_send_email = mocker.patch('app.routes.articles.rest.send_smtp_email', return_value=200)

        data = {
            'title': 'Confucius',
            'author': 'Updated Somone',
            'content': 'Something updated',
            'article_state': REJECTED,
            "reject_reason": 'test reason'
        }

        response = client.post(
            url_for('article.update_article_by_id', article_id=sample_article.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['content'] == data['content']
        articles = Article.query.all()
        assert len(articles) == 1
        assert articles[0].content == data['content']
        assert articles[0].article_state == REJECTED

        assert mock_send_email.call_args[0][0] == [TEST_ADMIN_USER]
        assert mock_send_email.call_args[0][1] == "Confucius article needs to be corrected"
        assert mock_send_email.call_args[0][2] == (
            '<div>Please correct this article <a href="http://frontend-test/admin/'
            'articles/{}">Confucius</a>'
            '</div><div>Reason: test reason</div>'.format(str(sample_article.id))
        )

    def it_updates_an_article_to_rejected_and_logs_email_errors(
        self, mocker, client, db, db_session, sample_admin_user, sample_article, mock_storage
    ):
        mock_send_email = mocker.patch('app.routes.articles.rest.send_smtp_email', return_value=400)

        data = {
            'title': 'Confucius',
            'author': 'Updated Somone',
            'content': 'Something updated',
            'article_state': REJECTED,
            "reject_reason": 'test reason'
        }

        response = client.post(
            url_for('article.update_article_by_id', article_id=sample_article.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp['content'] == data['content']
        articles = Article.query.all()
        assert len(articles) == 1
        assert articles[0].content == data['content']
        assert articles[0].article_state == REJECTED

        assert mock_send_email.called
        assert json_resp['errors'] == ['Problem sending smtp emails: 400']


class WhenPostingImportZip:

    @pytest.fixture
    def mock_articles_data(self):
        filename = os.path.join('tests', 'test_files', 'art.zip')

        articles_data = ''
        with open(filename, "rb") as f:
            data_bytes = f.read()

            articles_data = base64.b64encode(data_bytes)

        return str(articles_data, 'utf-8')

    def it_uploads_articles(self, client, db_session, sample_magazine, mock_articles_data):
        data = {
            'magazine_id': sample_magazine.id,
            'articles_data': mock_articles_data
        }

        response = client.post(
            url_for('articles.upload_articles'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        articles = Article.query.all()

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp == {
            'articles': [
                {
                    'name': articles[0].source_filename,
                    'id': str(articles[0].id)
                },
                {
                    'name': articles[1].source_filename,
                    'id': str(articles[1].id)
                }
            ]
        }

        articles = dao_get_articles()
        assert len(articles) == 2
        assert articles[0].title == 'Test 1'
        assert articles[1].title == 'Test 2'

    def it_handles_errors(self, mocker, client, db_session, sample_magazine, mock_articles_data):
        mocker.patch('app.routes.articles.rest.ZipFile.namelist', side_effect=BadZipFile("Bad Zip"))

        data = {
            'magazine_id': sample_magazine.id,
            'articles_data': mock_articles_data
        }

        response = client.post(
            url_for('articles.upload_articles'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        json_resp = json.loads(response.get_data(as_text=True))

        assert json_resp == {
            'articles': [],
            'errors': ["Bad Zip"]
        }

    def it_handles_duplicate_articles(self, client, db_session, sample_magazine, mock_articles_data):
        data = {
            'magazine_id': sample_magazine.id,
            'articles_data': mock_articles_data
        }

        article_2 = Article(title="Test 2", author="Test author")
        dao_create_article(article_2)

        response = client.post(
            url_for('articles.upload_articles'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )

        article_1 = Article.query.filter_by(source_filename='test_1_final.docx').one()

        json_resp = json.loads(response.get_data(as_text=True))
        assert json_resp == {
            'articles': [
                {'name': article_1.source_filename, 'id': str(article_1.id)}
            ],
            'errors': [
                {
                    'article': 'Test 2 by Test author exists',
                    'id': str(article_2.id)
                }
            ]
        }

        articles = dao_get_articles()
        assert len(articles) == 2
        assert articles[0].title == 'Test 1'
        assert articles[1].title == 'Test 2'
