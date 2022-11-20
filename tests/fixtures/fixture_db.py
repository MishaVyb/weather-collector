import os
from typing import Type
import pytest

import sqlalchemy as db
import sqlalchemy.orm as orm
from collector.functools import init_logger
from collector import models
from collector.session import Session as CollectorSession
from collector import session as session_module



logger = init_logger(__name__)

TEST_DB_FILE = os.path.join(os.path.dirname(__file__), 'testdb.sqlite3')
TEST_JOURNAL_FILE = os.path.join(os.path.dirname(__file__), 'testdb.sqlite3-journal')


@pytest.fixture(scope="session")
def connection():
    logger.debug('connection fixture')
    if os.path.isfile(TEST_DB_FILE) or os.path.isfile(TEST_JOURNAL_FILE):
        logger.warning(f'Test begins with already existing test db: {TEST_DB_FILE}.')

    engine = db.create_engine(f'sqlite:///{TEST_DB_FILE}', future=True)
    return engine.connect()


@pytest.fixture(scope="session")
def setup_database(connection):
    logger.debug('setup_database fixture')

    models.Base.metadata.bind = connection
    models.Base.metadata.create_all()
    yield
    models.Base.metadata.drop_all()

    if os.path.isfile(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    if os.path.isfile(TEST_JOURNAL_FILE):
        os.remove(TEST_JOURNAL_FILE)


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
def session_class(setup_database, clear_records, connection):
    logger.debug('session fixture')
    Session: Type[orm.Session] = orm.sessionmaker(bind=connection)
    yield Session


@pytest.fixture
def session(setup_database, clear_records, connection):
    logger.debug('opened session fixture')
    Session: Type[orm.Session] = orm.sessionmaker(
        autocommit=False, autoflush=False, bind=connection
    )
    yield Session()

@pytest.fixture
def mock_session(monkeypatch: pytest.MonkeyPatch, session_class: Type[orm.Session]):
    logger.debug('mock_session fixture')
    monkeypatch.setattr(session_module, 'Session', session_class)


