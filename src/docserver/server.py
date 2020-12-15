import uvicorn

from docserver.config import config
from docserver.db.models import create_all


if __name__ == "__main__":
    create_all(config)
    uvicorn.run('docserver.core:app', host='0.0.0.0', debug=True, port=8001, log_level='debug', reload=True)  # nosec
