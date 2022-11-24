import os
import pytest

from collector.functools import init_logger
from collector.configurations import CollectorConfig, CONFIG


logger = init_logger(__name__)

TEST_CITIES_FILE = os.path.join(os.path.dirname(__file__), 'testcities.json')


@pytest.fixture
def config():
    return CollectorConfig(
        debug=True,
        cities_amount=20,
        cities_file=TEST_CITIES_FILE,
        collect_weather_delay=0.5,
        _env_file='tests.env'
    )


@pytest.fixture
def mock_config(monkeypatch: pytest.MonkeyPatch, config: CollectorConfig):
    cities = config.cities_file
    if os.path.isfile(cities):
        logger.warning(f'Test begins with already existing {cities}. ')

    for field in CollectorConfig.__fields__:
        monkeypatch.setattr(CONFIG, field, getattr(config, field))
    yield

    if os.path.isfile(cities):
        os.remove(cities)
