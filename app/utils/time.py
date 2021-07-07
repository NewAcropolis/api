from datetime import datetime
import pytz

TIMEZONE_STR = 'Europe/London'
TIMEZONE = pytz.timezone(TIMEZONE_STR)


def get_local_time(dt):
    tz_local = pytz.timezone(TIMEZONE_STR)
    return dt.replace(tzinfo=pytz.utc).astimezone(tz_local)
