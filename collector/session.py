from __future__ import annotations
import functools

from typing import Callable, ClassVar, Type

import pydantic
import sqlalchemy as db
import sqlalchemy.orm as orm
from collector.configurations import CONFIG, SQLiteDatabaseConfig

from collector.functools import init_logger
from collector.models import BaseModel

logger = init_logger(__name__)

def safe_transaction(func: Callable):
    @functools.wraps(func)
    def wrapper(self: DBSessionMixin, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except:
            self.session.rollback()
            raise
    return wrapper


class DBSessionMixin:
    """
    Mixin for handling usal CRUD operations with database.
    Session is opening at class init and closing when `save()` is called. For commit any
    changes `save()` method must by called.
    """

    sessison_class: Type[orm.Session] | None = None
    config = CONFIG.db

    def __init__(self) -> None:
        logger.info(f'Establishing connection to database:: {self.config.url}')
        if isinstance(self.config, SQLiteDatabaseConfig):
            # [FIXME]
            # for SQLite we have to establish connection every time for every thread

            engine = db.create_engine(self.config.url, future=True)
            connection = engine.connect()
            DBSessionMixin.sessison_class = orm.sessionmaker(bind=connection)

        elif not DBSessionMixin.sessison_class:
            engine = db.create_engine(self.config.url)
            connection = engine.connect()
            DBSessionMixin.sessison_class = orm.sessionmaker(bind=connection)

        assert callable(DBSessionMixin.sessison_class), 'Check database configuration'
        self.session = DBSessionMixin.sessison_class()

    @safe_transaction
    def query(self, model_class: Type[BaseModel]):
        return self.session.query(model_class)

    @safe_transaction
    def create(self, *instances: BaseModel):
        self.session.add_all(instances)

    @safe_transaction
    def create_from_schema(
        self, model_class: Type[BaseModel], *instances: pydantic.BaseModel
    ):
        self.create(*[model_class(**instance.dict()) for instance in instances])

    @safe_transaction
    def delete(self, obj: BaseModel | Type[BaseModel]):
        """
        Delete one model instance. Or all records at table if `obj` is a Model Class.
        """
        if isinstance(obj, BaseModel):
            return self.session.delete(obj)
        if isinstance(obj, type):
            return self.session.query(obj).delete()
        raise ValueError

    @safe_transaction
    def save(self):
        self.session.commit()
        self.session.close()
        self.session.rollback()
