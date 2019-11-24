import re


MAGAZINE_PATTERN = r'( |_)issue( |_)(?P<issue_no>\d+)( .*)?\.pdf'


def get_magazine_filename(filename):
    match = re.search(MAGAZINE_PATTERN, filename, re.IGNORECASE)
    if match:
        issue_no = match.group('issue_no')
        return 'bi_monthly_issue_{}.pdf'.format(issue_no)
