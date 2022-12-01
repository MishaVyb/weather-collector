"""
Main config file for pytest.
"""

import logging
import pytest

from collector.functools import init_logger

pytest_plugins = [
    'tests.fixtures.fixture_db',
    'tests.fixtures.fixture_config',
    'tests.fixtures.fixture_cities',
]

logger = init_logger('pytest', 'DEBUG')


@pytest.fixture(autouse=True)
def new_line():
    """
    Fixture simple makes new line to seperate each test logging ouput.
    """
    print('\n')
