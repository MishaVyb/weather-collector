import logging
from typing import Type

import pytest
import sqlalchemy as db
import sqlalchemy.orm as orm

from collector import models
from collector.configurations import CollectorConfig

from collector.session import DBSessionMixin
import collector

from tests import logger


@pytest.fixture  # (scope="session")
def engine(config: CollectorConfig):
    logger.debug(f'engine fixture. bind to: {config.db.url}')
    return db.create_engine(config.db.url, future=True, echo=False)


@pytest.fixture
def patch_engine(monkeypatch: pytest.MonkeyPatch, engine: db.engine.Engine):
    logger.debug('patch_engine fixture')
    monkeypatch.setattr(collector.session, 'engine', engine)


@pytest.fixture  # (scope="session")
def setup_database(engine: db.engine.Engine, patch_engine):
    logger.debug('setup_database fixture')

    models.Base.metadata.drop_all(engine)  # clear leftovers from previous broken tests
    models.Base.metadata.create_all(engine)
    yield
    logger.debug(engine.pool.status())
    models.Base.metadata.drop_all(engine)


@pytest.fixture
def session_class():
    logger.debug('session_class fixture')
    return orm.Session  # return default Session, not from orn.session_maker (for now)


@pytest.fixture
def session(engine: db.engine.Engine, session_class: Type[orm.Session]):
    logger.debug('opened session fixture')
    with session_class(engine) as session:
        yield session
        session.commit()
