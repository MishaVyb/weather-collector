"""
Main config file for pytest.
"""
import os
import sys

import pytest

pytest_plugins = [
    'tests.fixtures.fixture_db',
    'tests.fixtures.fixture_config',
    'tests.fixtures.fixture_cities',
]


@pytest.fixture(autouse=True)
def new_line():
    """
    Fixture simple makes new line to seperate each test logging ouput.
    """
    print('\n')
