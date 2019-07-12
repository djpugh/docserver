import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URI = os.getenv('DOCSERVER_DATABASE_URI', 'sqlite:////tmp/docserver.db').replace(os.path.sep, '/')


class DBConfigClass:
    uri : str = SQLALCHEMY_DATABASE_URI
    engine = create_engine(
        SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False})
    local_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


db_config = DBConfigClass()