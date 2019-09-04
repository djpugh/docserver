import pkg_resources


from docserver.config import config


def nav():
    with open(pkg_resources.resource_filename('docserver.ui.help._templates', 'nav.html')) as f:
        nav_html = f.read()
        return nav_html.replace('{{ project }}', config.app_name)
