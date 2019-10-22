import logging
import os

from pydantic import BaseModel, Schema
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URI = os.getenv('DOCSERVER_DATABASE_URI', 'sqlite:////tmp/docserver.db').replace(os.path.sep, '/')

if SQLALCHEMY_DATABASE_URI.startswith('sqlite'):
    SQLALCHEMY_DB_KWARGS = dict(connect_args={"check_same_thread": False, "timeout": 20})
else:
    SQLALCHEMY_DB_KWARGS = dict()


class DBConfig(BaseModel):
    uri: str = Schema(SQLALCHEMY_DATABASE_URI)

    @property
    def engine(self):
        if not hasattr(self, '_engine'):
            super(BaseModel, self).__setattr__('_engine', create_engine(self.uri, **SQLALCHEMY_DB_KWARGS))
        return self._engine

    @property
    def local_session(self):
        if not hasattr(self, '_sessionmaker'):
            super(BaseModel, self).__setattr__('_sessionmaker', sessionmaker(autocommit=False, autoflush=False, bind=self.engine))
        return self._sessionmaker

    def __repr__(self):
        return f'DB ({self.uri})'
