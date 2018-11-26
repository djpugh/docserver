from flask import render_template
from flask import Blueprint

from docserver.models import Package

app = Blueprint('docserver', 'docserver', url_prefix='')


@app.route("/")
@app.route("/packages/")
def list_docs():
    packages = Package.query.order_by(Package.name).all()
    print(packages)
    return render_template('index.html', packages=packages)
