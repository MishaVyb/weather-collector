import logging
import os

import pydantic
import pytest

from collector.configurations import (CONFIG, CollectorConfig, DatabaseConfig,
                                      SQLiteDatabaseConfig)


from tests import logger

TEST_CITIES_FILE = os.path.join(os.path.dirname(__file__), 'testcities.json')
TEST_DB_FILE = os.path.join(os.path.dirname(__file__), 'testdb.sqlite3')


@pytest.fixture(
    scope="session",
    params=[
        pytest.param(SQLiteDatabaseConfig(path=TEST_DB_FILE), id='sqlite'),
        pytest.param(
            DatabaseConfig(
                user='test',
                password='test',
                host='localhost',
                database='test',
            ),
            id='postgres',
        ),
    ],
)
def config(request: pytest.FixtureRequest):
    db_config: pydantic.BaseSettings = request.param
    config = CollectorConfig(
        debug=False,
        cities_amount=20,
        cities_file=TEST_CITIES_FILE,
        collect_weather_delay=0.5,
        retry_collect_delay=1,
        db=db_config.dict(),
    )
    logger.debug(f'Running tests under those configurations: {config}')
    return config


@pytest.fixture
def mock_config(monkeypatch: pytest.MonkeyPatch, config: CollectorConfig):
    """
    Patching collector config file and restore test files ('cities.json')
    """
    cities = config.cities_file
    if os.path.isfile(cities):
        logger.warning(f'Test begins with already existing {cities}. ')

    for field in CollectorConfig.__fields__:
        monkeypatch.setattr(CONFIG, field, getattr(config, field))
    yield

    if os.path.isfile(cities):
        os.remove(cities)
