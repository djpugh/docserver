import os
from sphinx.application import Sphinx

def build_help():
    app = Sphinx(os.path.dirname(__file__),
                 os.path.dirname(__file__),
                 os.path.join(os.path.dirname(__file__), 'html'),
                 os.path.join(os.path.dirname(__file__), 'html', '.doctrees'),
                 'html')
    app.build([])
