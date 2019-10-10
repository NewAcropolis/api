from freezegun import freeze_time

from app.models import Event, Fee, Speaker
from tests.db import create_article, create_event, create_email, create_fee, create_speaker


class WhenUsingEventModel(object):

    def it_shows_event_info_id_on_str(self, db, db_session):
        event = create_event()

        assert str(event) == '<Event: id {}>'.format(event.id)


class WhenUsingFeeModel(object):

    def it_shows_fee_json_on_serialize(self, db, db_session):
        fee = create_fee(fee=5, conc_fee=3)

        assert fee.serialize() == {
            'id': str(fee.id),
            'event_type_id': str(fee.event_type_id),
            'fee': fee.fee,
            'conc_fee': fee.conc_fee,
            'multi_day_fee': fee.multi_day_fee,
            'multi_day_conc_fee': fee.multi_day_conc_fee,
            'valid_from': fee.valid_from.isoformat()
        }


class WhenUsingSpeakerModel(object):

    def it_shows_speaker_json_on_serialize(self, db, db_session):
        speaker = create_speaker()

        assert speaker.serialize() == {
            'id': str(speaker.id),
            'title': speaker.title,
            'name': speaker.name,
            'parent_id': None
        }

    def it_gets_last_name_correctly(self, db, db_session):
        speaker = create_speaker(name='John Smith')

        assert speaker.last_name == 'Smith'


class WhenUsingArticleModel(object):

    def it_shows_article_summary_json_on_serialize(self, db, db_session):
        article = create_article()

        assert article.serialize_summary() == {
            'id': str(article.id),
            'author': article.author,
            'title': article.title,
            'short_content': article.content,
            'very_short_content': article.content,
        }

    def it_shows_shortened_content_article_summary_json_on_serialize_long_content(self, db_session):
        long_content = ''
        short_content_length = 0
        very_short_content_length = 0
        for i in range(120):
            long_content += '{}some-text '.format(i)
            if i == 30:
                very_short_content_length = len(long_content) - 1
            if i == 110:
                short_content_length = len(long_content) - 1

        article = create_article(content=long_content)

        assert article.serialize_summary() == {
            'id': str(article.id),
            'author': article.author,
            'title': article.title,
            'short_content': long_content[:short_content_length] + '...',
            'very_short_content': long_content[:very_short_content_length] + '...'
        }

    def it_removes_html_tags_on_article_summary(self, db_session):
        long_content_with_tags = '<h1>'
        clean_long_content = ''
        clean_very_short_content_length = 0
        clean_short_content_length = 0
        for i in range(120):
            long_content_with_tags += '{}<div>text</div> '.format(i)
            clean_long_content += '{}text '.format(i)
            if i == 30:
                clean_very_short_content_length = len(clean_long_content) - 1
            if i == 110:
                clean_short_content_length = len(clean_long_content) - 1

        article = create_article(content=long_content_with_tags)

        assert article.serialize_summary() == {
            'id': str(article.id),
            'author': article.author,
            'title': article.title,
            'short_content': clean_long_content[:clean_short_content_length] + '...',
            'very_short_content': clean_long_content[:clean_very_short_content_length] + '...',
        }


class WhenUsingEmailModel:
    def it_shows_email_json_on_serialize(self, db, db_session):
        email = create_email(
            created_at='2019-06-01T10:00:00', send_starts_at='2019-06-02T11:00:00', send_after='2019-06-02T12:00:00')

        assert email.serialize() == {
            'id': str(email.id),
            'subject': 'workshop: test title',
            'event_id': str(email.event_id),
            'old_id': email.old_id,
            'old_event_id': email.old_event_id,
            'created_at': '2019-06-01 10:00',
            'extra_txt': u'test extra text',
            'details': u'test event details',
            'replace_all': False,
            'email_type': u'event',
            'email_state': u'draft',
            'send_starts_at': '2019-06-02',
            'expires': '2019-06-21',
            'send_after': '2019-06-02 12:00'
        }
