import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DOCSERVER_DATABASE_URI', 'sqlite:////tmp/docserver.db').replace(os.path.sep, '/')
print(app.config)
db = SQLAlchemy(app)
