from datetime import datetime
import pytz

TIMEZONE_STR = 'Europe/London'
TIMEZONE = pytz.timezone(TIMEZONE_STR)


def get_local_time():
    tz_local = pytz.timezone(TIMEZONE_STR)
    return datetime.now(tz_local)


# def get_local_time_as_string():
#     return datetime.strftime(get_local_time(), "%H:%M:%S")
