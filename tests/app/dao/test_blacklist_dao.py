import pytest
from datetime import datetime
import uuid
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
)

from app.routes.authentication.errors import TokenNotFound
from app.dao.blacklist_dao import store_token, is_token_revoked, get_user_tokens, unrevoke_token, prune_database
from app.models import TokenBlacklist
from app.utils.time import get_local_time
from tests.conftest import get_unixtime_start_and_expiry
from tests.db import create_token_blacklist


class WhenUsingBlacklistDAO(object):

    # need this test in order to reset db when running full test
    # def it_passes(self, db_session):
    #     pass

    def it_stores_a_token(self, db_session, sample_decoded_token):
        assert TokenBlacklist.query.count() == 0

        token_blacklist = create_token_blacklist(sample_decoded_token)

        assert TokenBlacklist.query.count() == 1
        token_blacklist_from_db = TokenBlacklist.query.first()

        expected_blacklist = {
            'token_id': token_blacklist_from_db.id,
            'jti': token_blacklist['jti'],
            'token_type': token_blacklist['type'],
            'user_identity': token_blacklist['identity'],
            'revoked': True,
            'expires': datetime.fromtimestamp(token_blacklist['exp'])
        }

        assert expected_blacklist == token_blacklist_from_db.serialize()

    def it_checks_if_token_is_revoked(self, db_session, sample_decoded_token):
        create_token_blacklist(sample_decoded_token)
        assert is_token_revoked(sample_decoded_token)

    def it_checks_if_token_is_not_revoked(self, db_session, sample_decoded_token):
        assert not is_token_revoked(sample_decoded_token)

    def it_gets_user_tokens(self, db_session, sample_decoded_token):
        another_token = {
            'jti': 'test',
            'exp': 1512865100,
            'iat': 1512864800,
            'fresh': False,
            'type': 'access',
            'nbf': 1512864800,
            'identity': 'someone_else'
        }

        create_token_blacklist(sample_decoded_token)
        create_token_blacklist(another_token)
        user_tokens = get_user_tokens(sample_decoded_token['identity'])

        assert len(user_tokens) == 1

    def it_unrevokes_a_token(self, db_session, sample_decoded_token):
        create_token_blacklist(sample_decoded_token)

        token_from_db = TokenBlacklist.query.one()

        unrevoke_token(token_from_db.id, sample_decoded_token['identity'])
        assert TokenBlacklist.query.all() == []

    def it_raises_token_not_found_unrevoking_non_existent_token(self, db_session):
        with pytest.raises(expected_exception=TokenNotFound):
            unrevoke_token(uuid.uuid4(), 'noone')

    def it_prunes_database(self, db_session, sample_decoded_token):
        now = get_local_time()

        start, expiry = get_unixtime_start_and_expiry(
            year=now.year, month=now.month, day=now.day, hour=now.hour, minute=now.minute)

        current_token = {
            'jti': 'test',
            'exp': expiry,
            'iat': start,
            'fresh': False,
            'type': 'access',
            'nbf': start,
            'identity': 'someone_else'
        }

        create_token_blacklist(current_token)
        create_token_blacklist(sample_decoded_token)
        create_token_blacklist(sample_decoded_token)

        prune_database()

        assert len(TokenBlacklist.query.all()) == 1
