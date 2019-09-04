import uvicorn

from docserver.db.models import create_all
from docserver.config import config
from docserver.core import app


if __name__ == "__main__":
    create_all(config)
    uvicorn.run(app, host='0.0.0.0', debug=True, port=8001)
