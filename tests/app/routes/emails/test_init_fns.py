from datetime import datetime

from app.comms.email import get_nice_event_dates


class WhenGettingNiceEventDates:

    class MockEventDate:
        def __init__(self, event_date):
            self.event_datetime = datetime.strptime(event_date, "%Y-%m-%d %H:%M")

    def it_returns_nice_dates(self):
        event_dates = [
            self.MockEventDate('2019-01-01 19:00'),
            self.MockEventDate('2019-01-07 19:00'),
        ]
        dates = get_nice_event_dates(event_dates)
        assert dates == 'Tues 1, Mon 7 of January - 7 PM'

    def it_returns_nice_dates_for_different_months(self):
        event_dates = [
            self.MockEventDate('2019-01-01 19:00'),
            self.MockEventDate('2019-02-07 19:00'),
        ]
        dates = get_nice_event_dates(event_dates)
        assert dates == 'Tues 1 of January, Thurs 7 of February - 7 PM'
