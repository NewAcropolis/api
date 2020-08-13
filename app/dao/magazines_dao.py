from app import db
from app.dao.decorators import transactional
from app.models import Magazine


def dao_get_magazines():
    return Magazine.query.order_by(Magazine.created_at.desc()).all()


def dao_get_latest_magazine():
    return Magazine.query.order_by(Magazine.created_at.desc()).first()


def dao_get_magazine_by_id(id):
    return Magazine.query.filter_by(id=id).one()


def dao_get_magazine_by_old_id(old_id):
    return Magazine.query.filter_by(old_id=old_id).first()


def dao_get_magazine_by_title(title):
    return Magazine.query.filter_by(title=title).first()
