from fastapi import applications
from fastapi.openapi.docs import get_redoc_html as _get_redoc_html
from fastapi.openapi.docs import get_swagger_ui_html as _get_swagger_ui_html
from starlette.responses import HTMLResponse

from docserver.ui.templates.nav import nav


def get_swagger_ui_html(*args, **kwargs) -> HTMLResponse:
    response = _get_swagger_ui_html(*args, **kwargs)
    return wrap_response(response)


def get_redoc_html(*args, **kwargs) -> HTMLResponse:
    response = _get_redoc_html(*args, **kwargs)
    return wrap_response(response)


def wrap_response(response: HTMLResponse) -> HTMLResponse:
    html = response.body.decode(response.charset)

    css = """
    <link href="/static/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/docserver.css">
    <link href="/static/css/open-iconic-bootstrap.css" rel="stylesheet">
    """
    head, body = html.split('</head>')
    head += '\n' + css
    print(css)
    body = body.split('<body>')[-1]
    body = nav() + '\n' + body
    print(body)
    html = f'{head}\n</head>\n<body>{body}'
    return HTMLResponse(html)


applications.get_swagger_ui_html = get_swagger_ui_html
applications.get_redoc_html = get_redoc_html
