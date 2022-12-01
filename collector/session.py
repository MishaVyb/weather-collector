from __future__ import annotations

import functools
import inspect
from typing import Callable, Type

import pydantic
import sqlalchemy as db
import sqlalchemy.orm as orm

from collector.configurations import CONFIG, DatabaseConfig

from collector.models import BaseModel

from collector.configurations import logger

try:
    logger.info(f'Establishing connection to database: {CONFIG.db.url}')
    engine = db.create_engine(CONFIG.db.url, future=True, echo=CONFIG.db.echo)
except Exception as e:
    logger.critical(f'Connection failed. Check your databbase is running: {CONFIG.db}')
    raise e


def safe_transaction(wrapped: Callable):
    @functools.wraps(wrapped)
    def wrapper(*args, **kwargs):
        # do not specify self as wrapper's argument,
        # otherwise functools.wraps won't work how it should
        if not args and isinstance(args[0], DBSessionMixin):
            raise TypeError(f'{wrapped} missing required positional argument: \'self\'')
        self = args[0]

        try:
            return wrapped(*args, **kwargs)
        except Exception as e:
            logger.warning(f'Transaction is rolling back. Exeption: {e}')
            self.session.rollback()
            raise e

    return wrapper


class SafeTransactionMeta(type):
    def __new__(cls, clsname: str, bases: tuple, attrs: dict):
        for key, value in attrs.items():
            if inspect.isfunction(value):
                attrs[key] = safe_transaction(value)
        return type.__new__(cls, clsname, bases, attrs)


class DBSessionMixin(metaclass=SafeTransactionMeta):
    """
    Mixin for handling usal CRUD operations with database.
    Session is opening at class init and closing when `save()` is called. For commit any
    changes `save()` method must by called.
    """

    def __init__(self) -> None:
        logger.debug(f'Session are opening with {engine=}')
        self.session = orm.Session(engine)

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
        Delete one model instance. Or all records at table if `obj` is a Model Class.
        """
        if isinstance(obj, BaseModel):
            return self.session.delete(obj)
        if isinstance(obj, type):
            return self.session.query(obj).delete()
        raise ValueError

    def save(self):
        """
        Commit transaction and close session.
        """
        self.session.commit()
        self.session.close()
