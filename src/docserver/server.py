import uvicorn

from docserver import db


if __name__ == "__main__":
    db.create_all()
    uvicorn.run('docserver.app:app', reload=True, host='0.0.0.0', debug=True, port=80)
