from sqlalchemy import and_

from app import db
from app.dao.decorators import transactional
from app.models import Article, APPROVED


@transactional
def dao_create_article(article):
    db.session.add(article)


@transactional
def dao_update_article(article_id, **kwargs):
    return Article.query.filter_by(id=article_id).update(
        kwargs
    )


def dao_get_articles(article_ids=None):
    if not article_ids:
        return Article.query.order_by(Article.title).all()
    else:
        return Article.query.filter(Article.id.in_(article_ids)).order_by(Article.title).all()


def dao_get_articles_with_images(limit=None):
    article_query = Article.query.filter(
        and_(
            Article.image_filename != None,  # noqa E711 SqlAlchemy syntax
            Article.article_state == APPROVED
        )
    )

    if not limit:
        return article_query.all()  # noqa E711 SqlAlchemy syntax
    else:
        return article_query.limit(limit).all()


def dao_get_article_by_id(article_id):
    return Article.query.filter_by(id=article_id).one()


def dao_get_article_by_title_author(title, author):
    return Article.query.filter_by(title=title, author=author).first()


def dao_get_articles_by_tags(tags):
    articles = []
    for tag in tags.split(","):
        for article in Article.query.filter(
                and_(
                    Article.tags.like(f"{tag},"),
                    Article.image_filename != None,  # noqa E711 SqlAlchemy syntax
                    Article.article_state == APPROVED
                )
        ).all():
            articles.append(article)
    return articles
