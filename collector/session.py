from __future__ import annotations

from typing import Type

import pydantic
import sqlalchemy as db
import sqlalchemy.orm as orm

from collector.functools import init_logger
from collector.models import BaseModel

logger = init_logger(__name__)
engine = db.create_engine('sqlite:///db.sqlite3', future=True)
Session: Type[orm.Session] = orm.sessionmaker(engine)


class DBSessionMixin:
    """
    Mixin for handling usal CRUD operations with database.
    Session is opening at class init and closing when `save()` is called. For commit any
    changes `save()` method must by called.
    """

    def __init__(self) -> None:
        self.session = Session()

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
