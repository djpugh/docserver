import os

import click
from sphinx.application import Sphinx


@click.command()
@click.parameter('--dist-dir', None)
def build_help(dist_dir=None):
    app = Sphinx(os.path.dirname(__file__),
                 os.path.dirname(__file__),
                 os.path.join(os.path.dirname(__file__), 'html'),
                 os.path.join(os.path.dirname(__file__), 'html', '.doctrees'),
                 'html')
    app.build([])
