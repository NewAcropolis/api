from app import db
from app.dao.decorators import transactional


@transactional
def dao_create_record(record):
    db.session.add(record)


@transactional
def dao_update_record(data_type, id, **kwargs):
    return data_type.query.filter_by(id=id).update(
        kwargs
    )


# def dao_get_record_by_id(data_type, id):
#     return data_type.query.filter_by(id=id).one()


# def dao_get_record_by_old_id(data_type, old_id):
#     return data_type.query.filter_by(old_id=old_id).first()
