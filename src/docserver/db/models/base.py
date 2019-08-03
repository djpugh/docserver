import logging
from typing import Union

from sqlalchemy.orm import Session
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql.schema import PrimaryKeyConstraint, UniqueConstraint

from docserver.app import schemas


class CustomBase:

    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    # Generate logger automatically
    @declared_attr
    def logger(cls):
        return logging.getLogger(cls.__module__)

    @classmethod
    def create(cls, db: Session, params: dict, **kwargs):
        cls.logger.info(f'Creating object {cls.__name__}')
        cls.logger.debug(f'Creating object {cls.__name__} from {params}')
        db_object = cls(**params)
        db.add(db_object)
        db.commit()
        db.refresh(db_object)
        return db_object

    @classmethod
    def read(cls, db: Session, skip: int = 0, limit: int = 100, params: dict = None, **kwargs):
        cls.logger.info(f'Reading objects {cls.__name__}')
        cls.logger.debug(f'Reading objects {cls.__name__} from {params}')
        return cls._read_query(db, params, **kwargs).offset(skip).limit(limit).all()

    @classmethod
    def read_unique(cls, db: Session, params: dict = None, **kwargs):
        cls.logger.info(f'Reading unique object {cls.__name__}')
        cls.logger.debug(f'Reading unique object {cls.__name__} from {params}')
        return cls._read_query(db, params, **kwargs).first()

    @classmethod
    def _read_query(cls, db: Session, params: dict = None, **kwargs):
        if params is None:
            compare_params = dict()
        else:
            compare_params = {u.name: params[u.name] for u in cls.__table__.columns if u.name in params.keys()}
        query = db.query(cls).filter_by(**compare_params)
        cls.logger.debug(f'Read query {query.statement}')
        return query

    @classmethod
    def _get_unique_params(cls, params):
        unique_columns = []
        for constraint in cls.__table__.constraints:
            if isinstance(constraint, (UniqueConstraint, PrimaryKeyConstraint)):
                unique_columns += [column.name for column in constraint.columns]
        compare_params = {column: params[column] for column in unique_columns if column in params.keys()}
        return compare_params

    def update(self, db: Session, params: dict, **kwargs):
        self.logger.info(f'Updating object {self.__class__.__name__}')
        self.logger.debug(f'Updating object {self.__class__.__name__} with {params}')
        params.update(kwargs)
        for key, value in params.items():
            try:
                setattr(self, key, value)
            except InvalidRequestError:
                self.logger.exception(f'Error updating {key} with {value} on {self}')
        db.add(self)
        db.commit()
        db.refresh(self)
        return self

    @classmethod
    def get_or_create(cls, db: Session, params: Union[dict, schemas.BaseModel], **kwargs):
        cls.logger.info(f'Get or create object {cls.__name__}')
        result = cls.read_unique(db, params=params, **kwargs)
        if result:
            cls.logger.debug(f'{cls.__name__} found with {params}')
            return result
        else:
            cls.logger.debug(f'{cls.__name__} not found with {params}')
            return cls.create(db, params, **kwargs)


Model = declarative_base(cls=CustomBase)
