import base64
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask import (
    current_app,
    jsonify
)

from app import celery
from app.comms.email import get_email_html, send_smtp_email
from app.dao import dao_update_record
from app.dao.emails_dao import dao_create_email, dao_get_email_by_magazine_id
from app.dao.magazines_dao import dao_get_magazine_by_id
from app.dao.users_dao import dao_get_users
from app.models import Email, Magazine, MAGAZINE, READY
from app.utils.pdf import extract_topics
from app.utils.storage import Storage


@celery.task()
def upload_magazine(magazine_id, pdf_data):
    current_app.logger.info('Upload magazine pdf: {}'.format(magazine_id))

    try:
        magazine = dao_get_magazine_by_id(magazine_id)

        storage = Storage(current_app.config['STORAGE'])
        decoded_data = base64.b64decode(pdf_data)
        storage.upload_blob_from_base64string(
            magazine.filename,
            magazine.filename,
            decoded_data,
            content_type='application/pdf'
        )

        if not magazine.topics:
            try:
                topics = extract_topics(base64.b64decode(decoded_data))
            except Exception as e:
                topics = []
                current_app.logger.error("Error extracting topics: %r", e)

            dao_update_record(Magazine, magazine_id, topics=topics)

        email = dao_get_email_by_magazine_id(magazine_id)

        if not email:
            email = Email(
                magazine_id=magazine.id,
                email_state=READY,
                email_type=MAGAZINE
            )
            dao_create_email(email)

        emails_to = [user.email for user in dao_get_users()]

        subject = 'Please review {}'.format(magazine.title)

        # send email to admin users and ask them to log in in order to approve the email
        review_part = '<div>Please review this email: {}/emails/{}</div>'.format(
            current_app.config['FRONTEND_ADMIN_URL'], str(email.id))
        magazine_html = get_email_html(MAGAZINE, magazine_id=magazine.id)
        response = send_smtp_email(emails_to, subject, review_part + magazine_html)

        if response != 200:
            current_app.logger.error('Error sending review email {}, for {}'.format(email.id, magazine.id))
    except Exception as e:
        current_app.logger.error('Task error uploading magazine: {}'.format(str(e)))
