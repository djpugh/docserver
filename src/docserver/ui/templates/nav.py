import pkg_resources


def nav():
    with open(pkg_resources.resource_filename('docserver.ui.help._templates', 'nav.html')) as f:
        return f.read()
