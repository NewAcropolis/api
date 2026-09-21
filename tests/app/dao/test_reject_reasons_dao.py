from app.dao.reject_reasons_dao import dao_update_reject_reason
from app.models import RejectReason

from tests.db import create_reject_reason


class WhenUsingRejectReasonsDAO(object):

    def it_creates_a_reject_reason(self, db_session, sample_event):
        reject_reason = create_reject_reason(sample_event.id)
        assert RejectReason.query.count() == 1

        reject_reason_from_db = RejectReason.query.filter(RejectReason.id == reject_reason.id).first()

        assert reject_reason == reject_reason_from_db

    def it_updates_a_reject_reason_dao(self, db_session, sample_reject_reason):
        dao_update_reject_reason(sample_reject_reason.id, reason='new reason', resolved=True)

        reject_reason_from_db = RejectReason.query.filter(RejectReason.id == sample_reject_reason.id).first()

        assert reject_reason_from_db.reason == 'new reason'
        assert reject_reason_from_db.resolved
