from typing import Type
import pytest

import sqlalchemy as db
import sqlalchemy.orm as orm
from collector.functools import init_logger
from collector import models
from collector.session import Session as CollectorSession
from collector import session as session_module


logger = init_logger(__name__)


@pytest.fixture(scope="session")
def connection():
    logger.debug('connection fixture')
    engine = db.create_engine('sqlite:///testdb.sqlite3', future=True)
    return engine.connect()


@pytest.fixture(scope="session")
def setup_database(connection):
    logger.debug('setup_database fixture')
    models.Base.metadata.bind = connection
    models.Base.metadata.create_all()
    yield
    models.Base.metadata.drop_all()


@pytest.fixture
def clear_records(setup_database, connection):
    yield
    logger.debug('session clear_records')

    cleaned_models: list[Type[models.BaseModel]] = [
        models.CityModel,
        models.MeasurementModel,
        models.ExtraMeasurementDataModel,
    ]

    Session: Type[orm.Session] = orm.sessionmaker(bind=connection)
    session = Session()
    for model in cleaned_models:
        session.query(model).delete()
    session.close()


@pytest.fixture
def session_class(setup_database, connection, clear_records):
    logger.debug('session fixture')
    Session: Type[orm.Session] = orm.sessionmaker(bind=connection)
    yield Session


@pytest.fixture
def session(setup_database, connection, clear_records):
    logger.debug('opened session fixture')
    Session: Type[orm.Session] = orm.sessionmaker(
        autocommit=False, autoflush=False, bind=connection
    )
    yield Session()

@pytest.fixture
def mock_session(monkeypatch, session_class):
    logger.debug('mock_session fixture')
    monkeypatch.setattr(session_module, 'Session', session_class)

