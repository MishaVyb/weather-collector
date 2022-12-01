import json
import logging

import pytest
import sqlalchemy.orm as orm

from collector import models
from collector.configurations import CollectorConfig
from tests import logger


@pytest.fixture
def cities_list():
    return [
        {'name': 'Shanghai'},
        {'name': 'Istanbul'},
        {'name': 'Tokyo'},
        {'name': 'Moscow'},
        {'name': 'Entebbe'},  # small African city
    ]


@pytest.fixture
def broken_cities_file(config: CollectorConfig):
    invalid_schema = [
        {'name': 'Moscow'},
        {'no_name': 'no_city'},
    ]
    with open(config.cities_file, 'w+', encoding='utf-8') as file:
        json.dump(invalid_schema, file)


@pytest.fixture
def cities_file(config: CollectorConfig, cities_list: list[dict]):
    with open(config.cities_file, 'w+', encoding='utf-8') as file:
        json.dump(cities_list, file)
    return cities_list


@pytest.fixture
def seed_cities_to_database(cities_list, session: orm.Session):
    session.add_all([models.CityModel(**city) for city in cities_list])
    session.commit()
