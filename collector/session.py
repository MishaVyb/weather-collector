from __future__ import annotations

from typing import ClassVar, Type

import pydantic
import sqlalchemy as db
import sqlalchemy.orm as orm
from collector.configurations import CONFIG, SQLiteDatabaseConfig

from collector.functools import init_logger
from collector.models import BaseModel

logger = init_logger(__name__)


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

    def query(self, model_class: Type[BaseModel]):
        return self.session.query(model_class)

    def create(self, *instances: BaseModel):
        self.session.add_all(instances)

    def create_from_schema(
        self, model_class: Type[BaseModel], *instances: pydantic.BaseModel
    ):
        self.create(*[model_class(**instance.dict()) for instance in instances])

    def delete(self, obj: BaseModel | Type[BaseModel]):
        """
        Delete one model instance or all records at table if `obj` is a Model Class.
        """
        if isinstance(obj, BaseModel):
            return self.session.delete(obj)
        if isinstance(obj, type):
            return self.session.query(obj).delete()
        raise ValueError

    def save(self):
        self.session.commit()
        self.session.close()
