from flask import current_app
from sqlalchemy.orm.exc import NoResultFound

from app import celery
from app.dao.events_dao import dao_get_event_by_id, dao_update_event
from app.errors import PaypalException
from app.payments.paypal import PayPal


@celery.task(bind=True)
def create_update_paypal_button_task(self, event_id):
    current_app.logger.info(
        'Task create_paypal_button received for event %s',
        str(event_id)
    )

    try:
        event = dao_get_event_by_id(event_id)
        if not event.booking_code:
            dao_update_event(event_id, booking_code=f'pending: {self.request.id}')

        booking_code = event.booking_code
        if event.booking_code.startswith('pending:') or event.booking_code.startswith('error:'):
            booking_code = None

        p = PayPal()
        booking_code = p.create_update_paypal_button(
            event_id, event.title,
            event.fee, event.conc_fee,
            event.multi_day_fee, event.multi_day_conc_fee,
            True if event.event_type == 'Talk' else False,
            booking_code=booking_code
        )

        dao_update_event(event_id, booking_code=booking_code)
    except NoResultFound as e:
        current_app.logger.error(f'No result error trying to create_update_paypal_button {e} {event_id}')
    except PaypalException as e:
        dao_update_event(event_id, booking_code=f'error: {self.request.id}')
        current_app.logger.error(f'Paypal error trying to create_update_paypal_button {e} {event_id}')
