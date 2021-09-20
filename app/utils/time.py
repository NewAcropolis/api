from datetime import datetime
import pytz

TIMEZONE_STR = 'Europe/London'
TIMEZONE = pytz.timezone(TIMEZONE_STR)


def get_local_time(dt):
    tz_local = pytz.timezone(TIMEZONE_STR)
    return dt.replace(tzinfo=pytz.utc).astimezone(tz_local)


def make_ordinal(n):
    n = int(n)
    suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    return str(n) + suffix
