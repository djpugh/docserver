import logging
import os

from pydantic import BaseSettings, Field, validator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


logger = logging.getLogger(__name__)


class DBConfig(BaseSettings):
    uri: str = Field('sqlite:////tmp/docserver.db', env='DOCSERVER_DATABASE_URI')
    _engine = None
    _sessionmaker = None

    class Config:  # noqa D106
        env_file = '.env'
        underscore_attrs_are_private = True

    @validator('uri')
    def _validate_uri(cls, value):
        return value.replace(os.path.sep, '/')

    @property
    def engine(self):
        if self._engine is None:
            if self.uri.startswith('sqlite'):
                db_kwargs = dict(connect_args={"check_same_thread": False, "timeout": 20})
            else:
                db_kwargs = dict()
            self._engine = create_engine(self.uri, **db_kwargs)
        return self._engine

    @property
    def local_session(self):
        if self._sessionmaker is None:
            self._sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        return self._sessionmaker

    def __repr__(self):
        return f'DB ({self.uri})'
