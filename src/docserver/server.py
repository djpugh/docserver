from docserver import app, db
from docserver.api import blueprint as api_blueprint
from docserver.app import app as app_blueprint

app.register_blueprint(api_blueprint)
app.register_blueprint(app_blueprint)
if __name__ == "__main__":
    db.create_all()
    app.run(host='0.0.0.0', debug=True, port=80)