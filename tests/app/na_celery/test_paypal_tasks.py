from mock import call
import pytest

from app.errors import PaypalException
from app.na_celery.paypal_tasks import create_update_paypal_button_task


@pytest.fixture
def mock_paypal(mocker):
    return mocker.patch(
        "app.na_celery.paypal_tasks.PayPal.create_update_paypal_button", return_value='test booking code'
    )


@pytest.fixture
def mock_paypal_error(mocker):
    return mocker.patch(
        "app.na_celery.paypal_tasks.PayPal.create_update_paypal_button",
        side_effect=PaypalException('Paypal exception,' * 10)
    )


class WhenProcessingCreateUpdatePaypalButtonTask:

    def it_creates_a_paypal_button(self, db_session, sample_event_with_dates, mock_paypal):
        create_update_paypal_button_task(sample_event_with_dates.id)

        assert mock_paypal.called
        assert sample_event_with_dates.booking_code == 'test booking code'

    def it_doesnt_create_a_paypal_button_if_no_event(self, app, mock_paypal, sample_uuid):
        create_update_paypal_button_task(sample_uuid)

        assert not mock_paypal.called

    def it_doesnt_update_event_if_paypal_error(self, mocker, mock_paypal_error, sample_event_with_dates):
        create_update_paypal_button_task(sample_event_with_dates.id)

        assert mock_paypal_error.called
        assert sample_event_with_dates.booking_code.startswith('error:')
        assert sample_event_with_dates.booking_code == 'error: ' + ('Paypal exception,' * 10)[:40]

    def it_calls_create_button_with_no_booking_code_for_pending_or_error(
        self, mocker, mock_paypal, sample_event_with_dates
    ):
        sample_event_with_dates.booking_code = "pending: task_id"
        create_update_paypal_button_task(sample_event_with_dates.id)

        assert mock_paypal.called
        assert mock_paypal.call_args == call(
            sample_event_with_dates.id, sample_event_with_dates.title,
            sample_event_with_dates.fee, sample_event_with_dates.conc_fee,
            sample_event_with_dates.multi_day_fee, sample_event_with_dates.multi_day_conc_fee,
            True if sample_event_with_dates.event_type == 'Talk' else False,
            booking_code=None
        )
        assert sample_event_with_dates.booking_code == 'test booking code'
