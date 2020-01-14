import os
from random import randint
from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)

from flask_jwt_extended import jwt_required

from app.dao.articles_dao import (
    dao_create_article,
    dao_get_articles,
    dao_update_article,
    dao_get_article_by_id
)
from app.errors import register_errors

from app.routes.articles.schemas import post_import_articles_schema

from app.models import Article
from app.schema_validation import validate

articles_blueprint = Blueprint('articles', __name__)
article_blueprint = Blueprint('article', __name__)
register_errors(articles_blueprint)
register_errors(article_blueprint)


@articles_blueprint.route('/articles')
@jwt_required
def get_articles():
    current_app.logger.info('get_articles')
    articles = [a.serialize() if a else None for a in dao_get_articles()]
    return jsonify(articles)


@articles_blueprint.route('/articles/summary')
@articles_blueprint.route('/articles/summary/<string:ids>')
@jwt_required
def get_articles_summary(ids=None):
    if not ids:
        current_app.logger.info('Limit articles summary to 4')
        articles = dao_get_articles()
        len_articles = len(articles)

        ids = []

        end = 4 if len_articles > 3 else len_articles

        while len(ids) < end:
            index = randint(0, len(articles) - 1)
            if str(articles[index].id) not in ids:
                ids.append(str(articles[index].id))
    else:
        ids = ids.split(',')

    articles = [a.serialize_summary() if a else None for a in dao_get_articles(ids)]
    return jsonify(articles)


@article_blueprint.route('/article/<uuid:article_id>', methods=['GET'])
@jwt_required
def get_article_by_id(article_id):
    current_app.logger.info('get_article: {}'.format(article_id))
    article = dao_get_article_by_id(article_id)
    return jsonify(article.serialize())


@articles_blueprint.route('/articles/import', methods=['POST'])
@jwt_required
def import_articles():
    data = request.get_json(force=True)

    validate(data, post_import_articles_schema)

    articles = []
    errors = []
    for item in data:
        err = ''
        article = Article.query.filter(Article.old_id == item['id']).first()
        if not article:
            article = Article(
                old_id=item['id'],
                title=item['title'],
                author=item['author'],
                content=item['content'],
                created_at=item['entrydate'] if item['entrydate'] != '0000-00-00' else None
            )

            articles.append(article)
            dao_create_article(article)
        else:
            err = u'article already exists: {} - {}'.format(article.old_id, article.title)
            current_app.logger.info(err)
            errors.append(err)

    res = {
        "articles": [a.serialize() for a in articles]
    }

    if errors:
        res['errors'] = errors

    return jsonify(res), 201 if articles else 400 if errors else 200
