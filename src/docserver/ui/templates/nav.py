import pkg_resources


from docserver.config import config


def nav(logo=None):
    with open(pkg_resources.resource_filename('docserver.ui.help._templates', 'nav.html')) as f:
        nav_html = f.read()
        if logo is None:
            logo = ''
        return nav_html.replace('{{ project }}', config.app_name).replace('{{ project_logo }}', logo)
