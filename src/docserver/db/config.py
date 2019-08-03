import logging
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URI = os.getenv('DOCSERVER_DATABASE_URI', 'sqlite:////tmp/docserver.db').replace(os.path.sep, '/')


class DBConfigClass:
    uri: str = SQLALCHEMY_DATABASE_URI
    engine = create_engine(SQLALCHEMY_DATABASE_URI,
                           connect_args={"check_same_thread": False})
    local_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def __repr__(self):
        return f'DB ({self.uri})'


db_config = DBConfigClass()
logger.debug(f'DB Config {db_config}')
print(f'DB Config {db_config}')
