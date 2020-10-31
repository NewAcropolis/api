from app import db
from app.dao.decorators import transactional
from app.models import User


@transactional
def dao_create_user(user):
    db.session.add(user)


@transactional
def dao_update_user(user_id, **kwargs):
    return User.query.filter_by(id=user_id).update(
        kwargs
    )


def dao_get_users():
    users = User.query.all()

    users.sort(key=lambda u: u.name.split(' ')[-1])
    return users


def dao_get_user_by_id(user_id):
    return User.query.filter_by(id=user_id).one()


def dao_get_user_by_email(email):
    return User.query.filter_by(email=email).first()


def dao_get_admin_users():
    return User.query.filter_by(access_area='admin', active=True).all()
