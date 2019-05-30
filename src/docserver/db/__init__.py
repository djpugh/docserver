import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker


SQLALCHEMY_DATABASE_URI = os.getenv('DOCSERVER_DATABASE_URI', 'sqlite:////tmp/docserver.db').replace(os.path.sep, '/')


engine = create_engine(
    SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class CustomBase:
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


Model = declarative_base(cls=CustomBase)


def create_all():
    Model.metadata.create_all(bind=engine)
