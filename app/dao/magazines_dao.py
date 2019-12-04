from app import db
from app.dao.decorators import transactional
from app.models import Magazine


def dao_get_magazines():
    return Magazine.query.order_by(Magazine.created_at.desc()).all()


def dao_get_magazine_by_old_id(old_id):
    return Magazine.query.filter_by(old_id=old_id).first()
