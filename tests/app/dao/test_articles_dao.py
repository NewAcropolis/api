import json

from app.dao.articles_dao import dao_create_article, \
    dao_update_article, dao_get_articles, dao_get_article_by_id, dao_get_articles_by_tags
from app.models import Article

from tests.db import create_article


class WhenUsingArticlesDAO:

    def it_creates_a_article(self, db_session):
        article = create_article()
        assert Article.query.count() == 1

        article_from_db = Article.query.filter(Article.id == Article.id).first()

        assert article == article_from_db

    def it_updates_a_article_dao(self, db, db_session, sample_article):
        dao_update_article(sample_article.id, title='Ancient Egypt')

        article_from_db = Article.query.filter(Article.id == sample_article.id).first()

        assert sample_article.title == article_from_db.title

    def it_gets_all_articles(self, db, db_session, sample_article):
        articles = [create_article(), sample_article]

        articles_from_db = dao_get_articles()
        assert Article.query.count() == 2
        assert set(articles) == set(articles_from_db)

    def it_gets_an_article_by_id(self, db, db_session, sample_article):
        article = create_article()

        fetched_article = dao_get_article_by_id(article.id)
        assert fetched_article == article

    def it_gets_articles_by_tags(self, db, db_session, sample_article):
        article = create_article(tags='music')
        art_article = create_article(tags='art')
        create_article(tags='')

        fetched_articles = dao_get_articles_by_tags('music,art')
        assert fetched_articles == [article, art_article]
