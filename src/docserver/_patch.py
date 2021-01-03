from fastapi import applications
from fastapi.openapi.docs import get_redoc_html as _get_redoc_html
from fastapi.openapi.docs import get_swagger_ui_html as _get_swagger_ui_html
from fastapi_aad_auth.ui.jinja import Jinja2Templates
from starlette.responses import HTMLResponse

from docserver import config


# TODO: check if this has been updated

_JINJA_ENV = Jinja2Templates('').env


def nav(config):
    template = _JINJA_ENV.from_string('{% from "docserver.ui.templates.components:nav.jinja" import nav %}\n{{ nav(None, project_logo, app_name, links, auth) }}')
    return template.render(project_logo=config.logo, app_name=config.app_name, links=[], auth=config.auth.enabled)


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
    body = body.split('<body>')[-1]
    body = nav(config.config) + '\n' + body
    html = f'{head}\n</head>\n<body>{body}'
    return HTMLResponse(html)


applications.get_swagger_ui_html = get_swagger_ui_html
applications.get_redoc_html = get_redoc_html
