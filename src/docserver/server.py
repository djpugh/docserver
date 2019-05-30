import uvicorn

from docserver import db
from docserver.app import app


if __name__ == "__main__":
    db.create_all()
    uvicorn.run(app, host='0.0.0.0', debug=True, port=80)
