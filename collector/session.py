from __future__ import annotations

import functools
import inspect
from typing import Callable, Type

import pydantic
import sqlalchemy as db
import sqlalchemy.orm as orm

from collector.configurations import CONFIG, logger
from collector.models import BaseModel

try:
    logger.info(f'Establishing connection to database: {CONFIG.db.url}')
    engine = db.create_engine(CONFIG.db.url, future=True, echo=CONFIG.db.echo)
except Exception as e:
    logger.critical(f'Connection failed. Check your database is running: {CONFIG.db}')
    raise e


class DBSessionMeta(type):
    """
    Create class which operates as session context manager.

    Meta is for wrapping all class methods into `safe_transaction` decorator.
    And for wrapping enter method for `Session()` opening and exit method for
    `session.commit()`, `session.close()`.
    """

    session_enter_method = '__init__'
    session_exit_method = 'execute'

    def __new__(cls, clsname: str, bases: tuple, attrs: dict):
        for key, value in attrs.items():
            if inspect.isfunction(value):
                attrs[key] = cls.safe_transaction(value)

                if key == cls.session_enter_method:
                    attrs[key] = cls.session_enter(attrs[key])
                if key == cls.session_exit_method:
                    attrs[key] = cls.session_exit(attrs[key])

        return type.__new__(cls, clsname, bases, attrs)

    @classmethod
    def session_enter(cls, wrapped: Callable):
        @functools.wraps(wrapped)
        def wrapper(self: DBSessionMixin, *args, **kwargs):
            self.session = orm.Session(engine)
            logger.debug(f'Session is open with {engine=}. ')
            return wrapped(self, *args, **kwargs)

        return wrapper

    @classmethod
    def session_exit(cls, wrapped: Callable):
        @functools.wraps(wrapped)
        def wrapper(self: DBSessionMixin, *args, **kwargs):
            result = wrapped(self, *args, **kwargs)
            self.session.commit()
            self.session.close()
            logger.debug('Session is closed. ')
            return result

        return wrapper

    @classmethod
    def safe_transaction(cls, wrapped: Callable):
        @functools.wraps(wrapped)
        def wrapper(self: DBSessionMixin, *args, **kwargs):
            try:
                return wrapped(self, *args, **kwargs)
            except Exception as e:
                logger.debug(f'Transaction is rolling back. Exception: {e}')
                self.session.rollback()
                raise e

        return wrapper


class DBSessionMixin(metaclass=DBSessionMeta):
    """
    Mixin for handling usual CRUD operations with database.
    Session is opening at class init and closing when `save()` is called. For commit any
    changes `save()` method must by called.
    """

    session: orm.Session

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
