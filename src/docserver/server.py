import uvicorn

from docserver.config import config
from docserver.core import app
from docserver.db.models import create_all


if __name__ == "__main__":
    create_all(config)
    uvicorn.run(app, host='0.0.0.0', debug=True, port=8001)  # nosec
