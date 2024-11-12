import base64
import docx
import io
import os
from random import randint
from zipfile import ZipFile

import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property

from flask import (
    Blueprint,
    current_app,
    jsonify,
    request
)
from sqlalchemy.orm.exc import NoResultFound
import time

from flask_jwt_extended import jwt_required

from app.comms.email import get_email_html, send_email, send_smtp_email
from app.dao.articles_dao import (
    dao_create_article,
    dao_get_articles,
    dao_update_article,
    dao_get_article_by_id,
    dao_get_articles_by_tags,
    dao_get_articles_with_images,
    dao_get_article_by_title_author
)
from app.dao.users_dao import dao_get_admin_users, dao_get_users
from app.errors import register_errors, InvalidRequest

from app.routes.articles.schemas import (
    post_import_articles_schema,
    post_update_article_schema,
    post_create_article_schema,
    post_upload_articles_schema
)

from app.models import Article, APPROVED, READY, REJECTED
from app.schema_validation import validate
from app.utils.storage import Storage

articles_blueprint = Blueprint('articles', __name__)
article_blueprint = Blueprint('article', __name__)
register_errors(articles_blueprint)
register_errors(article_blueprint)


@articles_blueprint.route('/articles')
@jwt_required()
def get_articles():
    articles = [a.serialize() if a else None for a in dao_get_articles()]
    return jsonify(articles)


@articles_blueprint.route('/articles/<string:tags>')
@jwt_required()
def get_articles_by_tags(tags, all=False):
    articles = [a.serialize() if a else None for a in dao_get_articles_by_tags(tags)]

    if all:
        extra_articles = [a.serialize() if a else None for a in dao_get_articles_with_images()]
        articles += extra_articles
    elif len(articles) < 5:
        num_extra_articles = 5 - len(articles)
        extra_articles = [a.serialize() if a else None for a in dao_get_articles_with_images(num_extra_articles)]
        articles += extra_articles

    return jsonify(articles)


@articles_blueprint.route('/articles/all/<string:tags>')
@jwt_required()
def get_all_articles_with_tags_prioritised(tags):
    return get_articles_by_tags(tags, all=True)


@articles_blueprint.route('/articles/summary')
@articles_blueprint.route('/articles/summary/<string:ids>')
@jwt_required()
def get_articles_summary(ids=None):
    if not ids:
        current_app.logger.info('Limit articles summary to 5')
        articles = dao_get_articles_with_images()
        len_articles = len(articles)

        ids = []

        end = 5 if len_articles > 4 else len_articles

        while len(ids) < end:
            index = randint(0, len(articles) - 1)
            if str(articles[index].id) not in ids:
                ids.append(str(articles[index].id))
    else:
        ids = ids.split(',')

    articles = [a.serialize_summary() if a else None for a in dao_get_articles(ids)]
    return jsonify(articles)


@article_blueprint.route('/article/<uuid:article_id>', methods=['GET'])
@jwt_required()
def get_article_by_id(article_id):
    article = dao_get_article_by_id(article_id)
    return jsonify(article.serialize())


@articles_blueprint.route('/articles/import', methods=['POST'])
@jwt_required()
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
                created_at=item['entrydate'] if item['entrydate'] != '0000-00-00' else None,
                image_filename=item['image_filename'] if 'image_filename' in item else None
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


@articles_blueprint.route('/articles/upload', methods=['POST'])
@jwt_required()
def upload_articles():
    data = request.get_json(force=True)
    validate(data, post_upload_articles_schema)

    file_like_object = io.BytesIO(base64.b64decode(data['articles_data']))
    zipfile_ob = ZipFile(file_like_object)

    articles = []
    errors = []

    try:
        for name in zipfile_ob.namelist():
            article = zipfile_ob.read(name)

            doc = docx.Document(io.BytesIO(article))
            fullText = []
            article_html = author = title = ""
            is_title = True
            sources_found = False
            for para in doc.paragraphs:
                if not para.text.strip():
                    continue
                fullText.append(para.text)
                if is_title:
                    # if the title is more than 255 chars long then take title from the filename
                    # assumes that title has '_final.docx' suffix
                    if len(para.text) < 256:
                        article_html += f"<h1>{para.text}</h1>"
                        title = para.text
                    else:
                        article_html += f"<p>{para.text}</p>"
                        title = name.replace("_final.docx", "").replace("_", " ").capitalize()
                    is_title = False
                else:
                    article_html += f"<p>{para.text}</p>"

                    # usually author is at the end of the article unless sources are provided
                    if para.text.lower() == "sources:":
                        sources_found = True
                    elif not sources_found:
                        author = para.text

            article_from_db = dao_get_article_by_title_author(title, author)
            if article_from_db:
                errors.append(
                    {
                        "article": f"{title} by {author} exists",
                        "id": str(article_from_db.id)
                    }
                )
            else:
                article = Article(
                    source_filename=name,
                    title=title,
                    author=author,
                    content=article_html,
                    magazine_id=data['magazine_id'] if data['magazine_id'] else None
                )
                dao_create_article(
                    article
                )
                articles.append(
                    {
                        "name": name,
                        "id": str(article.id)
                    }
                )
                current_app.logger.info(f"Uploading article {title} by {author}, {article.id}")
    except Exception as e:
        errors.append(str(e))
    resp = {
        'articles': articles
    }

    if errors:
        resp.update({'errors': errors})
    return jsonify(resp)


@article_blueprint.route('/article', methods=['POST'])
@jwt_required()
def add_article():
    data = request.get_json(force=True)

    validate(data, post_create_article_schema)

    article = Article(
        title=data['title'],
        author=data['author'],
        content=data['content'],
        image_filename=data['image_filename'],
        magazine_id=data.get('magazine_id'),
        tags=data['tags'] + ',',
        article_state=data['article_state']
    )

    article_from_db = dao_get_article_by_title_author(data['title'], data['author'])

    if article_from_db:
        raise InvalidRequest(f"Article: {data['title']} by {data['author']} exists ({str(article_from_db.id)})", 400)
    else:
        dao_create_article(article)

    image_filename = data.get('image_filename')

    image_data = data.get('image_data')

    storage = Storage(current_app.config['STORAGE'])

    image_filename = str(article.id)
    target_image_filename = f"articles/{image_filename}"

    if image_data:
        storage.upload_blob_from_base64string(
            image_filename, target_image_filename, base64.b64decode(image_data))

    elif data.get('image_filename'):
        if not storage.blob_exists(target_image_filename):
            raise InvalidRequest('{} does not exist'.format(target_image_filename), 400)

    article.image_filename = image_filename
    dao_update_article(article.id, image_filename=image_filename)

    return jsonify(article.serialize()), 201


@article_blueprint.route('/article/<uuid:article_id>', methods=['POST'])
@jwt_required()
def update_article_by_id(article_id):
    data = request.get_json(force=True)

    validate(data, post_update_article_schema)

    try:
        article = dao_get_article_by_id(str(article_id))
    except NoResultFound:
        raise InvalidRequest('article not found: {}'.format(article_id), 400)

    errs = []
    article_data = {}
    for k in data.keys():
        if hasattr(Article, k):
            if k == 'magazine_id' and data[k] == '':
                continue
            else:
                article_data[k] = data[k]

    res = dao_update_article(article.id, **article_data)

    image_data = data.get('image_data')

    image_filename = data.get('image_filename')

    storage = Storage(current_app.config['STORAGE'])
    if image_data:
        target_image_filename = str(article_id)

        if data.get('article_state') != APPROVED:
            target_image_filename += '-temp'

        storage.upload_blob_from_base64string(
            image_filename, 'articles/' + target_image_filename, base64.b64decode(image_data))

        unix_time = time.time()

        image_filename = '{}?{}'.format(target_image_filename, unix_time)
    elif image_filename:
        image_filename_without_cache_buster = image_filename.split('?')[0]
        if not storage.blob_exists('articles/' + image_filename_without_cache_buster):
            raise InvalidRequest('{} does not exist'.format(image_filename_without_cache_buster), 400)

    if image_filename:
        dao_update_article(article.id, image_filename=image_filename)

    if image_filename:
        if data.get('article_state') == APPROVED:
            if '-temp' in image_filename:
                q_pos = image_filename.index('-temp?')
                image_filename = image_filename[0:q_pos]
                storage.rename_image('articles/' + image_filename + '-temp', 'articles/' + image_filename)
            else:
                current_app.logger.warn(f"No temp file to rename: {image_filename}")

        article.image_filename = image_filename
        dao_update_article(article.id, image_filename=image_filename)

    json_article = article.serialize()

    if data.get('article_state') == READY:
        emails_to = [admin.email for admin in dao_get_admin_users()]

        message = 'Please review this article for publishing <a href="{}">{}</a>'.format(
            '{}/articles/{}'.format(current_app.config['FRONTEND_ADMIN_URL'], article_id),
            article.title
        )

        status_code = send_smtp_email(emails_to, 'Article: {} is ready for review'.format(article.title), message)
        if status_code != 200:
            errs.append(f"Problem sending admin email {status_code}")
    elif data.get('article_state') == REJECTED:
        emails_to = [user.email for user in dao_get_users()]

        message = '<div>Please correct this article <a href="{}">{}</a></div>'.format(
            '{}/articles/{}'.format(current_app.config['FRONTEND_ADMIN_URL'], article_id),
            article.title)
        message += '<div>Reason: {}</div>'.format(data.get('reject_reason'))

        status_code = send_smtp_email(emails_to, '{} article needs to be corrected'.format(article.title), message)
        if status_code != 200:
            errs.append(f"Problem sending smtp emails: {status_code}")

    json_article['errors'] = errs
    return jsonify(json_article), 200
