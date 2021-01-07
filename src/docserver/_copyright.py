from datetime import datetime


def get_copyright():
    return
    start_year = 2019
    end_year = datetime.now().year
    if end_year > start_year:
        __copyright__ = f'<a href="www.github.com/djpugh">@djpugh</a>, {start_year} - {end_year}'
    else:
        __copyright__ = f'<a href="www.github.com/djpugh">@djpugh</a>, {start_year}'
    return __copyright__
