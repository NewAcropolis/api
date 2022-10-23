import pytest
import uuid

from flask import json, url_for

from app.models import Article, DRAFT, READY
from tests.conftest import create_authorization_header

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

    def it_returns_up_to_4_articles_summary(self, client, sample_article, db_session):
        create_article(title='test 1')
        create_article(title='test 2')
        create_article(title='test 3')
        create_article(title='test 4')
        create_article(title='test 5')
        response = client.get(
            url_for('articles.get_articles_summary'),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert len(data) == 5

    def it_returns_selected_article_summary(self, client, sample_article, db_session):
        article_1 = create_article(title='test 1')
        create_article(title='test 2')

        article_ids = "{},{}".format(sample_article.id, article_1.id)
        response = client.get(
            url_for('articles.get_articles_summary', ids=article_ids),
            headers=[create_authorization_header()]
        )
        assert response.status_code == 200

        data = json.loads(response.get_data(as_text=True))

        assert len(data) == 2
        assert set([str(sample_article.id), str(article_1.id)]) == set(article_ids.split(','))


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

    def it_adds_an_article(self, client, db_session, sample_magazine):
        data = {
            'title': 'New',
            'author': 'Somone',
            'content': 'Something interesting',
            'image_filename': 'new_filename.jpg',
            'magazine_id': str(sample_magazine.id),
            'tags': 'Some tag'
        }
        response = client.post(
            url_for('article.add_article'),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 201
        assert response.json['image_filename'] == data['image_filename']
        assert response.json['magazine_id'] == data['magazine_id']

        articles = Article.query.all()

        assert len(articles) == 1
        assert articles[0].title == data['title']
        assert articles[0].article_state == DRAFT
        assert articles[0].tags == data['tags']
        assert articles[0].magazine_id == sample_magazine.id


class WhenPostingUpdateArticle:

    def it_updates_an_article(self, client, db_session, sample_article):
        data = {
            'title': 'Updated',
            'author': 'Updated Somone',
            'content': 'Something updated',
            'image_filename': 'updated_filename.jpg',
            'tags': 'Updated tag',
            'article_state': READY
        }
        response = client.post(
            url_for('article.update_article_by_id', article_id=sample_article.id),
            data=json.dumps(data),
            headers=[('Content-Type', 'application/json'), create_authorization_header()]
        )
        assert response.status_code == 200
        assert response.json['image_filename'] == data['image_filename']

        articles = Article.query.all()

        assert len(articles) == 1
        assert articles[0].title == data['title']
        assert articles[0].article_state == READY
        assert articles[0].tags == data['tags']
