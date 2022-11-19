from typing import Type
import pytest

import sqlalchemy as db
import sqlalchemy.orm as orm
from collector.functools import init_logger
from collector import models
from collector.session import Session as CollectorSession
from collector import configurations


logger = init_logger(__name__)



@pytest.fixture
def mock_config(monkeypatch):
    monkeypatch.setattr(configurations, 'CONFIG', configurations.CollectorConfig())

