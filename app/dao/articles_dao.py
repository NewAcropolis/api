from sqlalchemy import and_, not_, or_, func

from app import db
from app.dao.decorators import transactional
from app.models import Article, APPROVED


@transactional
def dao_create_article(article):
    db.session.add(article)


@transactional
def dao_update_article(article_id, **kwargs):
    if 'tags' in kwargs and kwargs['tags'] and not kwargs['tags'].endswith(','):
        kwargs['tags'] += ','

    return Article.query.filter_by(id=article_id).update(
        kwargs
    )


def dao_get_articles(limit=None, without_tags=None):
    articles = None
    if without_tags:
        without_tag_filter = ()
        for tag in without_tags.split(','):
            without_tag_filter = (*without_tag_filter, not_(Article.tags.ilike(f"%{tag},%")))

        articles = Article.query.filter(or_(*without_tag_filter, Article.tags.is_(None))).order_by(Article.title)
    else:
        articles = Article.query.order_by(Article.title)
    if limit:
        return articles.limit(limit).all()
    else:
        return articles.all()


def dao_get_articles_with_images(limit=5, without_tags=None):
    if without_tags:
        without_tag_filter = ()
        for tag in without_tags.split(','):
            without_tag_filter = (*without_tag_filter, not_(Article.tags.ilike(f"%{tag},%")))

        article_query = Article.query.filter(
            and_(
                or_(*without_tag_filter, Article.tags.is_(None)),
                Article.image_filename + '' != '',  # noqa E711 SqlAlchemy syntax
                Article.article_state == APPROVED
            )
        )
    else:
        article_query = Article.query.filter(
            and_(
                Article.image_filename + '' != '',  # noqa E711 SqlAlchemy syntax
                Article.article_state == APPROVED
            )
        )
    return article_query.order_by(func.random()).limit(limit).all()


def dao_get_article_by_id(article_id):
    return Article.query.filter_by(id=article_id).one()


def dao_get_article_by_title_author(title, author):
    return Article.query.filter_by(title=title, author=author).first()


def dao_get_articles_by_tags(tags):
    articles = []
    if tags:
        for tag in tags.split(","):
            for article in Article.query.filter(
                    and_(
                        Article.tags.ilike(f"%{tag},%"),
                        Article.image_filename + '' != '',  # noqa E711 SqlAlchemy syntax
                        Article.article_state == APPROVED
                    )
            ).all():
                articles.append(article)
    return articles
