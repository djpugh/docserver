import os

import click
from sphinx.application import Sphinx


@click.command()
@click.option('--dist-dir', default=None)
def build_help(dist_dir):
    if not dist_dir:
        dist_dir = os.path.join(os.path.dirname(__file__), 'html')
    app = Sphinx(os.path.dirname(__file__),
                 os.path.dirname(__file__),
                 os.path.join(dist_dir),
                 os.path.join(dist_dir, '.doctrees'),
                 'html')
    app.build([])
