from sqlalchemy import and_, not_, func

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
        articles = Article.query.filter(not_(Article.tags.ilike(f"%{without_tags},%")))
    else:
        articles = Article.query.order_by(Article.title)
    if limit:
        return articles.limit(limit).all()
    else:
        return articles.all()


def dao_get_articles_with_images(limit=5, without_tags=None):
    article_query = Article.query.filter(
        and_(
            Article.image_filename + '' != '',  # noqa E711 SqlAlchemy syntax
            Article.article_state == APPROVED
        )
    )

    articles = article_query.order_by(func.random()).limit(limit).all()

    if without_tags:
        articles_without_tag = []
        for article in articles:
            for tag in without_tags.split(','):
                if article not in articles_without_tag and (not article.tags or tag + ',' not in article.tags):
                    articles_without_tag.append(article)
        return articles_without_tag
    else:
        return articles


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
