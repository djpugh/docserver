from datetime import datetime


def get_copyright():
    start_year = 2019
    end_year = datetime.now().year
    if end_year > start_year:
        __copyright__ = f"David Pugh, {start_year} - {end_year}"
    else:
        __copyright__ = f'David Pugh, {start_year}'
    return __copyright__
