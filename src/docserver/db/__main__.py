from docserver.config import config
from docserver.db.models import create_all

create_all(config)
