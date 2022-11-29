import logging
from typing import Type

import pytest
import sqlalchemy as db
import sqlalchemy.orm as orm

from collector import models
from collector.configurations import CollectorConfig
from collector.functools import init_logger
from collector.session import DBSessionMixin

logger = init_logger(__name__, logging.DEBUG)


@pytest.fixture
def mock_database_config(
    monkeypatch: pytest.MonkeyPatch,
    config: CollectorConfig,
):
    logger.debug('mock_database_config fixture')
    monkeypatch.setattr(DBSessionMixin, 'config', config.db)


@pytest.fixture  # (scope="session")
def engine(config: CollectorConfig):
    logger.debug(f'engine fixture. bind to: {config.db.url}')
    return db.create_engine(config.db.url, future=True, echo=False)


@pytest.fixture  # (scope="session")
def setup_database(engine: db.engine.Engine, mock_database_config):
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
